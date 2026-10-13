"""
schemas.py — Pydantic v2 request/response schemas for FraudGuard AI.

All schemas use strict typing and sensible defaults so the frontend can
omit optional fields without breaking validation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Input ─────────────────────────────────────────────────────────────────────

class TransactionInput(BaseModel):
    """
    Payload for a single fraud-detection prediction request.

    The 28 anonymised PCA components (V1–V28) and the Time feature are all
    optional and default to 0.0, so callers only need to provide what they
    actually know.  Amount is required and must be positive.
    """

    # Required
    amount: float = Field(..., gt=0, description="Transaction amount in USD (must be > 0)")

    # Optional — dataset features
    time: float = Field(default=0.0, description="Seconds elapsed since first transaction")
    v1:  float = Field(default=0.0)
    v2:  float = Field(default=0.0)
    v3:  float = Field(default=0.0)
    v4:  float = Field(default=0.0)
    v5:  float = Field(default=0.0)
    v6:  float = Field(default=0.0)
    v7:  float = Field(default=0.0)
    v8:  float = Field(default=0.0)
    v9:  float = Field(default=0.0)
    v10: float = Field(default=0.0)
    v11: float = Field(default=0.0)
    v12: float = Field(default=0.0)
    v13: float = Field(default=0.0)
    v14: float = Field(default=0.0)
    v15: float = Field(default=0.0)
    v16: float = Field(default=0.0)
    v17: float = Field(default=0.0)
    v18: float = Field(default=0.0)
    v19: float = Field(default=0.0)
    v20: float = Field(default=0.0)
    v21: float = Field(default=0.0)
    v22: float = Field(default=0.0)
    v23: float = Field(default=0.0)
    v24: float = Field(default=0.0)
    v25: float = Field(default=0.0)
    v26: float = Field(default=0.0)
    v27: float = Field(default=0.0)
    v28: float = Field(default=0.0)

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("amount must be greater than 0")
        return round(v, 4)

    def to_feature_dict(self) -> Dict[str, float]:
        """Return a flat dict keyed by feature name (lowercase, matching ML pipeline)."""
        return self.model_dump()


# ── Single prediction response ────────────────────────────────────────────────

class TransactionResult(BaseModel):
    """Response returned after a single /predict call."""

    transaction_id: str
    prediction: int                # 0 = Legitimate, 1 = Fraud
    fraud_probability: float       # [0.0, 1.0]
    risk_level: str                # LOW | MEDIUM | HIGH
    amount: float
    timestamp: float               # The 'Time' feature value
    is_fraud: bool
    message: str                   # Human-readable verdict


# ── Batch prediction response ──────────────────────────────────────────────────

class BatchRowResult(BaseModel):
    """One row inside a batch response."""

    row_index: int
    transaction_id: str
    prediction: int
    fraud_probability: float
    risk_level: str
    amount: float
    is_fraud: bool


class BatchResult(BaseModel):
    """Aggregate response for a CSV batch upload."""

    total: int
    fraud_count: int
    legitimate_count: int
    fraud_percentage: float
    results: List[BatchRowResult]


# ── Dashboard ─────────────────────────────────────────────────────────────────

class RecentTransaction(BaseModel):
    """Lightweight transaction summary used in the dashboard feed."""

    transaction_id: str
    amount: float
    prediction: int
    fraud_probability: float
    risk_level: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DashboardStats(BaseModel):
    """Top-level KPIs for the dashboard."""

    total_transactions: int
    fraud_detected: int
    legitimate_transactions: int
    fraud_rate: float              # percentage, 0–100
    recent_transactions: List[RecentTransaction]


class ChartDataPoint(BaseModel):
    """One day's worth of fraud vs. legitimate counts for the time-series chart."""

    date: str                      # ISO date string, e.g. "2024-01-15"
    fraud_count: int
    legitimate_count: int
    total: int


# ── Model metrics ──────────────────────────────────────────────────────────────

class ModelMetrics(BaseModel):
    """Performance metrics returned by GET /model/metrics."""

    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    confusion_matrix: Dict[str, Any]   # {"TP": int, "TN": int, "FP": int, "FN": int}
    model_name: str
    training_samples: int
    test_samples: int
    features_used: List[str]
    is_demo: bool
    all_model_results: Optional[List[Dict[str, Any]]] = None


# ── Transaction history ────────────────────────────────────────────────────────

class TransactionHistory(BaseModel):
    """Full transaction record returned from GET /transactions endpoints."""

    id: int
    transaction_id: str
    timestamp: float
    amount: float
    prediction: int
    fraud_probability: float
    risk_level: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedTransactions(BaseModel):
    """Wrapper for paginated transaction list responses."""

    total: int
    page: int
    page_size: int
    pages: int
    items: List[TransactionHistory]


# ── Health check ───────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Response for GET /health."""

    status: str
    mode: str          # "demo" or "real"
    model_loaded: bool
    version: str = "1.0.0"
    app_name: str = "FraudGuard AI"
