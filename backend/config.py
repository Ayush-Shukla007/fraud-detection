"""
config.py — Application settings loaded from .env via pydantic-settings.
All configuration values have safe defaults so the app runs out-of-the-box.
"""

from pydantic_settings import BaseSettings
from typing import List
import json


class Settings(BaseSettings):
    # ── Database ────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./fraudguard.db"

    # ── ML artefact paths ────────────────────────────────────────────────────
    MODEL_PATH: str = "../ml/model.joblib"
    SCALER_PATH: str = "../ml/scaler.joblib"
    FEATURES_PATH: str = "../ml/features.json"

    # ── Upload limits ────────────────────────────────────────────────────────
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10 MB

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Stored as a JSON string in .env; parsed below.
    CORS_ORIGINS: str = '["http://localhost:5173","http://localhost:3000","http://127.0.0.1:5173"]'

    # ── Auth ─────────────────────────────────────────────────────────────────
    JWT_SECRET: str = "super_secret_jwt_key_for_fraudguard"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours

    # ── Email Alerts ─────────────────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    ALERT_EMAIL: str = ""
    HIGH_RISK_THRESHOLD: float = 0.80

    # ── Feature flags ────────────────────────────────────────────────────────
    DEMO_MODE: bool = True

    # ── Derived helpers ──────────────────────────────────────────────────────
    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS_ORIGINS as a Python list."""
        try:
            return json.loads(self.CORS_ORIGINS)
        except (ValueError, TypeError):
            return ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton — import this everywhere
settings = Settings()
