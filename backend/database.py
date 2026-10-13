"""
database.py — Async SQLAlchemy engine, session factory, and DB initialiser.

We use aiosqlite as the async driver for SQLite.  All operations in routers
and services must use `async with get_session() as session:` to get a
properly scoped AsyncSession.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import settings
from models import Base

logger = logging.getLogger(__name__)

# ── Engine ────────────────────────────────────────────────────────────────────
# check_same_thread=False is required for SQLite when used with async drivers.
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,          # Set True to log all SQL statements during debugging
    future=True,
)

# ── Session factory ────────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Avoids lazy-load errors after commit
    autoflush=False,
    autocommit=False,
)


# ── Dependency / context-manager ───────────────────────────────────────────────
@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager that yields a database session.

    Usage (in router):
        async with get_session() as session:
            result = await session.execute(select(Transaction))
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency injection version of get_session.

    Usage (in endpoint):
        async def my_endpoint(db: AsyncSession = Depends(get_db)):
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Initialiser ────────────────────────────────────────────────────────────────
async def init_db() -> None:
    """
    Create all tables that don't yet exist.
    Called once from the FastAPI lifespan startup hook.
    """
    logger.info("Initialising database at: %s", settings.DATABASE_URL)
    async with engine.begin() as conn:
        # create_all is idempotent — safe to call on every startup
        await conn.run_sync(Base.metadata.create_all)
        # Attempt to add user_id column if it doesn't exist (ignore error if it does)
        try:
            from sqlalchemy import text
            await conn.execute(text("ALTER TABLE transactions ADD COLUMN user_id INTEGER;"))
        except Exception:
            pass
    logger.info("Database initialised successfully.")
