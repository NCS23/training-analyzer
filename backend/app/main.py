import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.infrastructure.database.session import engine, init_db
from app.routers import training

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    await init_db()
    yield


app = FastAPI(
    title="Training Analyzer API",
    description="API for analyzing running and strength training data",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (exercise images)
_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# Register Routers
app.include_router(training.router, prefix="/api")
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Training Analyzer API", "version": "0.1.0"}


@app.get("/health")
async def health():
    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        logger.warning("Health check: DB-Verbindung fehlgeschlagen")

    status = "ok" if db_ok else "degraded"
    return {"status": status, "environment": settings.environment, "database": db_ok}
