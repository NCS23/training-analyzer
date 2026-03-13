import logging

from fastapi import APIRouter
from sqlalchemy import text

from app.infrastructure.database.session import engine

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        logger.warning("Health check: DB-Verbindung fehlgeschlagen")

    status = "healthy" if db_ok else "degraded"
    return {"status": status, "database": db_ok}
