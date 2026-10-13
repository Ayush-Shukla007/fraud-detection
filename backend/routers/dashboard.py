"""
routers/dashboard.py — Dashboard statistics and chart-data endpoints.

Endpoints
---------
GET /api/v1/dashboard/stats      — KPI summary cards.
GET /api/v1/dashboard/chart-data — Daily fraud/legit counts for the last 30 days.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Transaction
from routers.auth import get_current_user
from schemas import (
    ChartDataPoint,
    DashboardStats,
    RecentTransaction,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get(
    "/stats",
    response_model=DashboardStats,
    summary="Return top-level KPI statistics",
)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
) -> DashboardStats:
    """
    Compute and return:
    - Total transaction count.
    - Fraud / legitimate split.
    - Fraud rate as a percentage.
    - The 10 most recent transactions for the activity feed.
    """
    count_q = select(
        func.count(Transaction.id).label("total"),
        func.sum(
            case((Transaction.prediction == 1, 1), else_=0)
        ).label("fraud_count"),
    )
    if current_user.role != "admin":
        count_q = count_q.where(Transaction.user_id == current_user.id)
        
    agg_result = await db.execute(count_q)
    agg = agg_result.one()

    total: int = agg.total or 0
    fraud_count: int = int(agg.fraud_count or 0)
    legit_count: int = total - fraud_count
    fraud_rate: float = round((fraud_count / total * 100), 2) if total else 0.0

    # ── Recent 10 transactions ────────────────────────────────────────────────
    recent_q = (
        select(Transaction)
    )
    if current_user.role != "admin":
        recent_q = recent_q.where(Transaction.user_id == current_user.id)
    recent_q = recent_q.order_by(Transaction.created_at.desc()).limit(10)
    
    recent_result = await db.execute(recent_q)
    recent_rows = recent_result.scalars().all()

    recent = [RecentTransaction.model_validate(r) for r in recent_rows]

    logger.debug(
        "Dashboard stats: total=%d fraud=%d rate=%.2f%%", total, fraud_count, fraud_rate
    )

    return DashboardStats(
        total_transactions=total,
        fraud_detected=fraud_count,
        legitimate_transactions=legit_count,
        fraud_rate=fraud_rate,
        recent_transactions=recent,
    )


# ── Chart data ────────────────────────────────────────────────────────────────

@router.get(
    "/chart-data",
    response_model=list[ChartDataPoint],
    summary="Daily fraud vs. legitimate counts for the last 30 days",
)
async def get_chart_data(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
) -> list[ChartDataPoint]:
    """
    Return a list of daily data points covering the last 30 days.

    Days with zero transactions are included (with zero counts) so the
    frontend chart always renders a continuous 30-day window.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    q = (
        select(Transaction.created_at, Transaction.prediction)
        .where(Transaction.created_at >= cutoff)
    )
    if current_user.role != "admin":
        q = q.where(Transaction.user_id == current_user.id)

    result = await db.execute(q)
    rows = result.all()

    # Build a lookup from the results
    db_map: dict[str, tuple[int, int]] = {}
    for (created_at, prediction) in rows:
        if not created_at:
            continue
        day_str = created_at.date().isoformat()
        fraud, total = db_map.get(day_str, (0, 0))
        db_map[day_str] = (fraud + (1 if prediction == 1 else 0), total + 1)

    # Fill in all 30 days (including days with no transactions)
    points: list[ChartDataPoint] = []
    for delta in range(30):
        day = (datetime.now(timezone.utc) - timedelta(days=29 - delta)).date()
        day_str = day.isoformat()
        fraud, total = db_map.get(day_str, (0, 0))
        points.append(
            ChartDataPoint(
                date=day_str,
                fraud_count=fraud,
                legitimate_count=total - fraud,
                total=total,
            )
        )

    return points
