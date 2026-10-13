"""
routers/transactions.py — Transaction history CRUD endpoints.

Endpoints
---------
GET    /api/v1/transactions                  — Paginated + filtered history.
GET    /api/v1/transactions/{transaction_id} — Single transaction detail.
DELETE /api/v1/transactions                  — Clear all history (with confirm).
"""

from __future__ import annotations

import logging
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Transaction
from schemas import PaginatedTransactions, TransactionHistory
from routers.auth import require_admin, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["Transactions"])


# ── List / search ─────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=PaginatedTransactions,
    summary="Get paginated transaction history with optional filters",
)
async def list_transactions(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=500, description="Records per page"),
    prediction_filter: Optional[int] = Query(
        default=None,
        description="Filter by prediction: 0=Legitimate, 1=Fraud",
    ),
    risk_filter: Optional[str] = Query(
        default=None,
        description="Filter by risk level: LOW, MEDIUM, HIGH",
    ),
    search: Optional[str] = Query(
        default=None,
        description="Search by transaction_id (partial match supported)",
    ),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
) -> PaginatedTransactions:
    """
    Return a paginated list of past transactions.

    All filter params are optional and can be combined.
    Results are ordered by creation time descending (newest first).
    """
    # ── Build base query ──────────────────────────────────────────────────────
    base_q = select(Transaction)

    # RBAC: Viewers can only see their own transactions
    if current_user.role != "admin":
        base_q = base_q.where(Transaction.user_id == current_user.id)

    # Apply filters
    if prediction_filter is not None:
        base_q = base_q.where(Transaction.prediction == prediction_filter)

    if risk_filter is not None:
        risk_upper = risk_filter.upper()
        if risk_upper not in ("LOW", "MEDIUM", "HIGH"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="risk_filter must be one of: LOW, MEDIUM, HIGH",
            )
        base_q = base_q.where(Transaction.risk_level == risk_upper)

    if search:
        base_q = base_q.where(
            Transaction.transaction_id.ilike(f"%{search}%")
        )

    # ── Count total matching records ──────────────────────────────────────────
    count_q = select(func.count()).select_from(base_q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar_one()

    # ── Paginate ──────────────────────────────────────────────────────────────
    offset = (page - 1) * page_size
    paginated_q = (
        base_q
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(paginated_q)
    rows = result.scalars().all()

    pages = math.ceil(total / page_size) if total else 1

    return PaginatedTransactions(
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
        items=[TransactionHistory.model_validate(r) for r in rows],
    )


# ── Single transaction ────────────────────────────────────────────────────────

@router.get(
    "/{transaction_id}",
    response_model=TransactionHistory,
    summary="Get a single transaction by its UUID",
)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
) -> TransactionHistory:
    """
    Return full details for a single transaction.
    Returns 404 if the transaction_id is not found.
    """
    q = select(Transaction).where(Transaction.transaction_id == transaction_id)
    result = await db.execute(q)
    row = result.scalar_one_or_none()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{transaction_id}' not found.",
        )

    return TransactionHistory.model_validate(row)


# ── Delete all ────────────────────────────────────────────────────────────────

@router.delete(
    "/",
    summary="Clear transaction history",
    status_code=status.HTTP_200_OK,
)
async def clear_transactions(
    current_user = Depends(get_current_user),
    confirm: bool = Query(
        default=False,
        description="Must be true to actually delete records.",
    ),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Permanently delete transaction records.
    Admins delete everything. Viewers delete only their own.
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pass ?confirm=true to confirm deletion of transaction history.",
        )

    stmt = delete(Transaction)
    if current_user.role != "admin":
        stmt = stmt.where(Transaction.user_id == current_user.id)

    result = await db.execute(stmt)
    deleted = result.rowcount
    logger.warning("Transaction history cleared by %s (%d records deleted).", current_user.username, deleted)

    return {
        "message": f"Successfully deleted {deleted} transaction record(s).",
        "deleted_count": deleted,
    }


@router.delete(
    "/{transaction_id}",
    summary="Delete a single transaction",
    status_code=status.HTTP_200_OK,
)
async def delete_single_transaction(
    transaction_id: str,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Permanently delete a single transaction.
    """
    stmt = delete(Transaction).where(Transaction.transaction_id == transaction_id)
    if current_user.role != "admin":
        stmt = stmt.where(Transaction.user_id == current_user.id)
        
    result = await db.execute(stmt)
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or you don't have permission to delete it."
        )

    return {
        "message": "Successfully deleted transaction.",
        "transaction_id": transaction_id
    }
