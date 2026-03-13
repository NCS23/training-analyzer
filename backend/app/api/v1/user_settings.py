"""User Settings API (API Keys).

Verwaltet verschlüsselte API-Keys für KI-Provider.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt_api_key
from app.infrastructure.database.models import AthleteModel
from app.infrastructure.database.session import get_db
from app.models.user_settings import UserSettingsRequest, UserSettingsResponse

router = APIRouter(prefix="/user", tags=["user-settings"])


async def _get_or_create_athlete(db: AsyncSession) -> AthleteModel:
    """Singleton-Athlete laden oder erstellen (wie in athlete.py)."""
    result = await db.execute(select(AthleteModel).limit(1))
    athlete = result.scalar_one_or_none()
    if not athlete:
        athlete = AthleteModel()
        db.add(athlete)
        await db.commit()
        await db.refresh(athlete)
    return athlete


@router.get("/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    db: AsyncSession = Depends(get_db),
) -> UserSettingsResponse:
    """Gibt User-Settings mit maskierten API Keys zurück."""
    athlete = await _get_or_create_athlete(db)
    return UserSettingsResponse.from_db(athlete)


@router.patch("/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    body: UserSettingsRequest,
    db: AsyncSession = Depends(get_db),
) -> UserSettingsResponse:
    """Aktualisiert API Keys (verschlüsselt in DB).

    - Feld nicht im Body oder None → keine Änderung
    - Leerer String '' → Key löschen
    - Wert → Key verschlüsseln und speichern
    """
    athlete = await _get_or_create_athlete(db)

    if body.claude_api_key is not None:
        if body.claude_api_key == "":
            athlete.encrypted_claude_api_key = None
        else:
            athlete.encrypted_claude_api_key = encrypt_api_key(body.claude_api_key)

    if body.openai_api_key is not None:
        if body.openai_api_key == "":
            athlete.encrypted_openai_api_key = None
        else:
            athlete.encrypted_openai_api_key = encrypt_api_key(body.openai_api_key)

    await db.commit()
    await db.refresh(athlete)
    return UserSettingsResponse.from_db(athlete)
