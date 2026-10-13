"""
routers/model.py — Model metrics and service health endpoints.

Endpoints
---------
GET /api/v1/model/metrics — Return ML model performance metrics.
GET /api/v1/health        — Service health check (also available at root).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter

from ml_service import ml_service
from schemas import HealthResponse, ModelMetrics
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Model"])


# ── Model metrics ─────────────────────────────────────────────────────────────

@router.get(
    "/model/metrics",
    response_model=ModelMetrics,
    summary="Return ML model performance metrics",
)
async def get_model_metrics() -> ModelMetrics:
    """
    Load and return model performance metrics.

    In DEMO MODE the returned object contains realistic demo values and
    `is_demo=true` so the frontend can show an appropriate disclaimer.

    In REAL MODE the metrics are read from metrics.json produced during
    model training.
    """
    raw = ml_service.get_metrics()
    return ModelMetrics(**raw)


# ── Health ────────────────────────────────────────────────────────────────────

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health check",
)
async def health_check() -> HealthResponse:
    """
    Lightweight liveness / readiness probe.

    Returns:
    - status  : "ok" when the server is running.
    - mode    : "demo" or "real".
    - model_loaded : True when real ML artefacts are loaded.
    """
    mode = "demo" if ml_service.is_demo else "real"
    logger.debug("Health check: mode=%s model_loaded=%s", mode, ml_service.model_loaded)

    return HealthResponse(
        status="ok",
        mode=mode,
        model_loaded=ml_service.model_loaded,
    )
