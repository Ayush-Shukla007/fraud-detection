"""
models.py — SQLAlchemy ORM model definitions.
Uses declarative_base() with async-compatible column types.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Boolean, Integer, Text, DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


class Transaction(Base):
    """
    Stores every fraud-detection inference result.

    Columns
    -------
    id                : Auto-increment primary key.
    transaction_id    : UUID string assigned at prediction time.
    timestamp         : The 'Time' feature value from the original transaction
                        (seconds elapsed since first transaction in the dataset).
    amount            : Transaction amount in USD.
    prediction        : 1 = Fraud, 0 = Legitimate.
    fraud_probability : Model confidence score in [0, 1].
    risk_level        : "LOW" | "MEDIUM" | "HIGH".
    features_json     : JSON-serialised feature dict for audit purposes.
    created_at        : Wall-clock time the record was inserted.
    """

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(String(36), unique=True, index=True, nullable=False)
    timestamp = Column(Float, nullable=False, default=0.0)
    amount = Column(Float, nullable=False)
    prediction = Column(Integer, nullable=False)          # 0 or 1
    fraud_probability = Column(Float, nullable=False)
    risk_level = Column(String(10), nullable=False)       # LOW / MEDIUM / HIGH
    user_id = Column(Integer, index=True, nullable=True)  # Links transaction to the user who created it
    features_json = Column(Text, nullable=True)           # raw JSON string
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} txn={self.transaction_id} "
            f"fraud={bool(self.prediction)} prob={self.fraud_probability:.4f}>"
        )


class User(Base):
    """
    Stores analyst accounts and roles.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="viewer")  # "admin" or "viewer"
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username} role={self.role}>"
