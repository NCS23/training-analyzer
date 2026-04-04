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


@router.get("/debug/user-data")
async def debug_user_data():
    """Temporärer Debug-Endpoint: Zeigt user_id-Verteilung in allen Tabellen."""
    results: dict = {}
    try:
        async with engine.connect() as conn:
            for table in [
                "users",
                "training_plans",
                "weekly_plan_days",
                "planned_sessions",
                "race_goals",
                "workouts",
                "chat_conversations",
            ]:
                rows = (
                    await conn.execute(
                        text(
                            f"SELECT user_id, COUNT(*) FROM {table} GROUP BY user_id ORDER BY user_id"
                        )
                    )
                ).fetchall()
                results[table] = [{"user_id": r[0], "count": r[1]} for r in rows]
    except Exception as e:
        return {"error": str(e)}
    return results
