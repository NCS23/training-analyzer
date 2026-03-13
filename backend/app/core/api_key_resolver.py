"""API Key Resolution: DB (User-konfiguriert) → .env Fallback."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.encryption import decrypt_api_key
from app.infrastructure.database.models import AthleteModel


async def resolve_claude_api_key(db: AsyncSession) -> str:
    """Claude API Key auflösen: User-DB-Key zuerst, dann .env."""
    db_key = await _get_db_key(db, "encrypted_claude_api_key")
    return db_key or settings.claude_api_key


async def resolve_openai_api_key(db: AsyncSession) -> str:
    """OpenAI API Key auflösen: User-DB-Key zuerst, dann .env."""
    db_key = await _get_db_key(db, "encrypted_openai_api_key")
    return db_key or settings.openai_api_key


async def _get_db_key(db: AsyncSession, column_name: str) -> str | None:
    """Entschlüsselten API Key aus der DB laden, oder None."""
    result = await db.execute(select(AthleteModel).limit(1))
    athlete = result.scalar_one_or_none()
    if not athlete:
        return None
    encrypted = getattr(athlete, column_name, None)
    if not encrypted:
        return None
    try:
        return decrypt_api_key(encrypted)
    except Exception:
        return None
