import logging
import traceback
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.core.config import settings
from app.infrastructure.database.session import engine, init_db
from app.routers import training

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    await init_db()
    await _backfill_trimp_scores()
    yield


async def _backfill_trimp_scores() -> None:
    """Berechne TRIMP für Sessions ohne Score (nach Migration / neuen Algorithmen)."""
    from sqlalchemy import select

    from app.infrastructure.database.models import WorkoutModel
    from app.infrastructure.database.session import async_session_maker
    from app.services.fitness_score import calculate_trimp

    async with async_session_maker() as db:
        result = await db.execute(select(WorkoutModel).where(WorkoutModel.trimp_score.is_(None)))
        sessions = list(result.scalars().all())
        if not sessions:
            return

        count = 0
        for session in sessions:
            trimp = calculate_trimp(session)
            if trimp > 0:
                session.trimp_score = trimp
                count += 1

        if count > 0:
            await db.commit()

        import logging

        logging.getLogger("uvicorn").info(
            "TRIMP Backfill: %d/%d Sessions berechnet", count, len(sessions)
        )


app = FastAPI(
    title="Training Analyzer API",
    description="API for analyzing running and strength training data",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
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


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(_request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Pass-through für HTTPException (4xx) — Detail unverändert."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Pydantic-Validierungs-Fehler (422) — liefert Feld-Details."""
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Globaler Fallback: loggt Stack-Trace und liefert Exception-Details in 500-Response.

    Erkannte ungehandelte Exception → sichtbar in Backend-Container-Logs UND
    als JSON-Detail in der Response, damit Frontend den Fehler anzeigen kann.
    """
    tb = traceback.format_exc()
    logger.exception(
        "Unhandled exception in %s %s: %s",
        request.method,
        request.url.path,
        exc,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"{type(exc).__name__}: {exc}",
            "path": request.url.path,
            "traceback": tb.splitlines()[-10:],  # letzte 10 Zeilen für Debug
        },
    )


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
