"""API Key Resolution: DB (User-konfiguriert) → .env Fallback."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.encryption import decrypt_api_key
from app.infrastructure.database.models import AthleteModel


async def resolve_claude_api_key(db: AsyncSession, user_id: int | None = None) -> str:
    """Claude API Key auflösen: User-DB-Key zuerst, dann .env."""
    db_key = await _get_db_key(db, "encrypted_claude_api_key", user_id)
    return db_key or settings.claude_api_key


async def resolve_openai_api_key(db: AsyncSession, user_id: int | None = None) -> str:
    """OpenAI API Key auflösen: User-DB-Key zuerst, dann .env."""
    db_key = await _get_db_key(db, "encrypted_openai_api_key", user_id)
    return db_key or settings.openai_api_key


async def resolve_preferred_provider(db: AsyncSession, user_id: int | None = None) -> str:
    """Bevorzugten AI Provider auflösen: User-Präferenz oder System-Default."""
    athlete = await _get_athlete(db, user_id)
    if athlete and getattr(athlete, "preferred_ai_provider", None):
        return athlete.preferred_ai_provider  # type: ignore[return-value]
    return settings.ai_primary_provider


async def _get_athlete(db: AsyncSession, user_id: int | None) -> AthleteModel | None:
    """Athlete für User laden."""
    query = select(AthleteModel)
    if user_id is not None:
        query = query.where(AthleteModel.user_id == user_id)
    query = query.order_by(AthleteModel.id.asc()).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def _get_db_key(db: AsyncSession, column_name: str, user_id: int | None) -> str | None:
    """Entschlüsselten API Key aus der DB laden, oder None."""
    athlete = await _get_athlete(db, user_id)
    if not athlete:
        return None
    encrypted = getattr(athlete, column_name, None)
    if not encrypted:
        return None
    try:
        return decrypt_api_key(encrypted)
    except Exception:
        return None
