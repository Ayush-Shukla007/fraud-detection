"""
routers/predict.py — Single and batch fraud-prediction endpoints.

Endpoints
---------
POST /api/v1/predict        — Single transaction prediction.
POST /api/v1/predict/batch  — CSV file upload for bulk predictions.
"""

from __future__ import annotations

import io
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from ml_service import ml_service
from models import Transaction, User
from routers.auth import require_admin, get_current_user
from utils import send_high_risk_alert_email
from schemas import (
    BatchResult,
    BatchRowResult,
    TransactionInput,
    TransactionResult,
)
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict", tags=["Predictions"])

# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_db_record(
    txn_id: str,
    features: dict,
    result: dict,
    user_id: int = None,
) -> Transaction:
    """Construct a Transaction ORM object ready to be added to the session."""
    return Transaction(
        transaction_id=txn_id,
        timestamp=features.get("time", 0.0),
        amount=features.get("amount", 0.0),
        prediction=result["prediction"],
        fraud_probability=result["fraud_probability"],
        risk_level=result["risk_level"],
        user_id=user_id,
        features_json=json.dumps(features),
        created_at=datetime.now(timezone.utc),
    )


def _verdict_message(prediction: int, prob: float) -> str:
    """Return a friendly verdict string for the UI."""
    if prediction == 1:
        return f"⚠️  Fraudulent transaction detected (confidence: {prob:.1%})"
    return f"✅  Legitimate transaction (fraud probability: {prob:.1%})"


# ── Single prediction ─────────────────────────────────────────────────────────

@router.post(
    "/",
    response_model=TransactionResult,
    summary="Predict fraud for a single transaction",
    status_code=status.HTTP_200_OK,
)
async def predict_single(
    payload: TransactionInput,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionResult:
    """
    Accept a JSON transaction payload, run the fraud-detection model,
    persist the result, and return a structured response.
    """
    features = payload.to_feature_dict()
    txn_id = str(uuid.uuid4())

    try:
        result = ml_service.predict(features)
    except Exception as exc:
        logger.exception("ML inference error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction service encountered an error. Please try again.",
        ) from exc

    # Persist to database
    record = _build_db_record(txn_id, features, result, user_id=current_user.id)
    db.add(record)
    # Commit handled by get_db dependency on exit

    # Trigger email alert for high risk transactions
    if result["fraud_probability"] >= settings.HIGH_RISK_THRESHOLD:
        background_tasks.add_task(
            send_high_risk_alert_email,
            txn_id,
            payload.amount,
            result["fraud_probability"]
        )

    logger.info(
        "Prediction [%s]: amount=%.2f fraud=%s prob=%.4f",
        txn_id,
        payload.amount,
        bool(result["prediction"]),
        result["fraud_probability"],
    )

    return TransactionResult(
        transaction_id=txn_id,
        prediction=result["prediction"],
        fraud_probability=result["fraud_probability"],
        risk_level=result["risk_level"],
        amount=payload.amount,
        timestamp=payload.time,
        is_fraud=bool(result["prediction"]),
        message=_verdict_message(result["prediction"], result["fraud_probability"]),
    )


# ── Batch prediction ──────────────────────────────────────────────────────────

# Columns that must be present in the uploaded CSV (case-insensitive)
_REQUIRED_COLUMNS = {"amount"}
_OPTIONAL_V_COLS = {f"v{i}" for i in range(1, 29)}
_ALL_KNOWN_COLS = _REQUIRED_COLUMNS | _OPTIONAL_V_COLS | {"time"}


@router.post(
    "/batch",
    response_model=BatchResult,
    summary="Batch prediction from CSV file upload",
    status_code=status.HTTP_200_OK,
)
async def predict_batch(
    file: UploadFile = File(..., description="CSV file containing transaction rows"),
    current_user = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> BatchResult:
    """
    Accept a multipart CSV upload, validate its size and columns, run
    predictions on every row, persist all results, and return aggregate stats.

    CSV must have an `amount` column.  V1–V28 and Time are optional (default 0).
    """
    # ── File size guard ───────────────────────────────────────────────────────
    raw_bytes = await file.read()
    if len(raw_bytes) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE // (1024*1024)} MB.",
        )

    # ── Content-type / extension check ────────────────────────────────────────
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only CSV files are supported for batch upload.",
        )

    # ── Parse CSV ─────────────────────────────────────────────────────────────
    try:
        df = pd.read_csv(io.BytesIO(raw_bytes))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not parse CSV: {exc}",
        ) from exc

    if df.empty:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="The uploaded CSV file is empty.",
        )

    # Normalise column names to lowercase
    df.columns = [c.strip().lower() for c in df.columns]

    # Check required columns
    missing = _REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"CSV is missing required column(s): {', '.join(sorted(missing))}",
        )

    # ── Process rows ──────────────────────────────────────────────────────────
    row_results: List[BatchRowResult] = []
    fraud_count = 0

    for idx, row in df.iterrows():
        # Build a feature dict; fill missing V-features with 0.0
        features: dict = {"time": float(row.get("time", 0.0))}
        try:
            features["amount"] = float(row["amount"])
            if features["amount"] <= 0:
                logger.warning("Row %d skipped: non-positive amount.", idx)
                continue
        except (ValueError, TypeError):
            logger.warning("Row %d skipped: invalid amount value.", idx)
            continue

        for col in _OPTIONAL_V_COLS:
            raw_val = row.get(col, 0.0)
            try:
                features[col] = float(raw_val) if pd.notna(raw_val) else 0.0
            except (ValueError, TypeError):
                features[col] = 0.0

        txn_id = str(uuid.uuid4())

        try:
            result = ml_service.predict(features)
        except Exception as exc:
            logger.warning("Row %d prediction failed: %s — skipping.", idx, exc)
            continue
            
        # Yield to the event loop every 100 rows to prevent server freeze
        if idx > 0 and idx % 100 == 0:
            import asyncio
            await asyncio.sleep(0)

        if result["prediction"] == 1:
            fraud_count += 1

        record = _build_db_record(txn_id, features, result, user_id=current_user.id)
        db.add(record)

        row_results.append(
            BatchRowResult(
                row_index=int(idx),
                transaction_id=txn_id,
                prediction=result["prediction"],
                fraud_probability=result["fraud_probability"],
                risk_level=result["risk_level"],
                amount=features["amount"],
                is_fraud=bool(result["prediction"]),
            )
        )

    if not row_results:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No valid rows could be processed from the uploaded CSV.",
        )

    total = len(row_results)
    legit_count = total - fraud_count
    fraud_pct = round((fraud_count / total) * 100, 2) if total else 0.0

    logger.info(
        "Batch prediction complete: %d rows, %d fraud (%.1f%%)",
        total,
        fraud_count,
        fraud_pct,
    )

    return BatchResult(
        total=total,
        fraud_count=fraud_count,
        legitimate_count=legit_count,
        fraud_percentage=fraud_pct,
        results=row_results,
    )
