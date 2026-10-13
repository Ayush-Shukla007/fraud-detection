"""
main.py — FraudGuard Pro FastAPI application entry point.

Start the server:
    uvicorn main:app --reload --port 8000

API base URL : http://localhost:8000
Swagger UI   : http://localhost:8000/docs
ReDoc        : http://localhost:8000/redoc
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database import init_db
from ml_service import ml_service
from routers import dashboard, model, predict, transactions
from schemas import HealthResponse

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    Startup  : Initialise DB schema and load ML artefacts.
    Shutdown : Log goodbye (add cleanup tasks here as needed).
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("=" * 60)
    logger.info("  FraudGuard Pro - starting up")
    logger.info("=" * 60)

    # Initialise database tables
    await init_db()

    # Load ML model (falls back to demo if artefacts are missing)
    ml_service.load(
        model_path=settings.MODEL_PATH,
        scaler_path=settings.SCALER_PATH,
        features_path=settings.FEATURES_PATH,
        force_demo=settings.DEMO_MODE,
    )

    # Initialize default users
    from database import AsyncSessionLocal
    from models import User
    from sqlalchemy import select
    from routers.auth import get_password_hash
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).limit(1))
        if not result.scalars().first():
            logger.info("Initializing default users: admin/admin, viewer/viewer")
            admin_user = User(username="admin", hashed_password=get_password_hash("admin"), role="admin")
            viewer_user = User(username="viewer", hashed_password=get_password_hash("viewer"), role="viewer")
            session.add_all([admin_user, viewer_user])
            await session.commit()

    mode_label = "DEMO" if ml_service.is_demo else "REAL"
    logger.info("ML service started in %s MODE.", mode_label)
    logger.info("Server ready.  Docs -> http://localhost:8000/docs")
    logger.info("=" * 60)

    yield  # Application runs here

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("FraudGuard Pro shutting down. Goodbye!")


# ── Application factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="FraudGuard Pro Backend",
        description=(
            "Production-quality REST API for real-time credit card fraud detection "
            "powered by XGBoost / scikit-learn with a transparent DEMO fallback mode."
        ),
        version="1.0.0",
        contact={
            "name": "FraudGuard Pro Team",
            "url": "https://github.com/your-org/fraudguard-ai",
        },
        license_info={"name": "MIT"},
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from routers import dashboard, model, predict, transactions, auth
    from routers.auth import get_current_user
    from fastapi import Depends

    # ── Routers ───────────────────────────────────────────────────────────────
    API_PREFIX = "/api/v1"

    app.include_router(auth.router,          prefix=API_PREFIX)
    app.include_router(predict.router,       prefix=API_PREFIX, dependencies=[Depends(get_current_user)])
    app.include_router(transactions.router,  prefix=API_PREFIX, dependencies=[Depends(get_current_user)])
    app.include_router(dashboard.router,     prefix=API_PREFIX, dependencies=[Depends(get_current_user)])
    app.include_router(model.router,         prefix=API_PREFIX, dependencies=[Depends(get_current_user)])

    # ── Root health check (mirrors /api/v1/health for load-balancer probes) ──
    @app.get(
        "/health",
        response_model=HealthResponse,
        tags=["Health"],
        summary="Root-level health check",
        include_in_schema=True,
    )
    async def root_health() -> HealthResponse:
        mode = "demo" if ml_service.is_demo else "real"
        return HealthResponse(
            status="ok",
            mode=mode,
            model_loaded=ml_service.model_loaded,
        )

    # ── Root redirect ─────────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def root() -> JSONResponse:
        return JSONResponse(
            content={
                "message": "Welcome to FraudGuard Pro Backend",
                "docs": "/docs",
                "health": "/health",
                "api": "/api/v1",
            }
        )

    # ── Global exception handler ──────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled exception on %s %s: %s",
            request.method,
            request.url.path,
            exc,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An unexpected server error occurred. Please try again.",
                "type": type(exc).__name__,
            },
        )

    return app


# ── Application instance ──────────────────────────────────────────────────────
app = create_app()


# ── Dev entrypoint ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

