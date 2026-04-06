"""User Settings API (API Keys + AI Provider Präferenz).

Verwaltet verschlüsselte API-Keys und Provider-Einstellungen.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.core.encryption import encrypt_api_key
from app.infrastructure.database.models import AthleteModel, UserModel
from app.infrastructure.database.session import get_db
from app.models.user_settings import VALID_PROVIDERS, UserSettingsRequest, UserSettingsResponse

router = APIRouter(prefix="/user", tags=["user-settings"])


async def _get_or_create_athlete(db: AsyncSession, user_id: int) -> AthleteModel:
    """Athlete für einen User laden oder erstellen."""
    result = await db.execute(
        select(AthleteModel)
        .where(AthleteModel.user_id == user_id)
        .order_by(AthleteModel.id.asc())
        .limit(1)
    )
    athlete = result.scalar_one_or_none()
    if not athlete:
        athlete = AthleteModel(user_id=user_id)
        db.add(athlete)
        await db.commit()
        await db.refresh(athlete)
    return athlete


@router.get("/settings", response_model=UserSettingsResponse)
async def get_user_settings(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
) -> UserSettingsResponse:
    """Gibt User-Settings mit maskierten API Keys zurück."""
    athlete = await _get_or_create_athlete(db, current_user.id)
    return UserSettingsResponse.from_db(athlete)


@router.patch("/settings", response_model=UserSettingsResponse)
async def update_user_settings(
    body: UserSettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
) -> UserSettingsResponse:
    """Aktualisiert API Keys (verschlüsselt in DB).

    - Feld nicht im Body oder None → keine Änderung
    - Leerer String '' → Key löschen
    - Wert → Key verschlüsseln und speichern
    """
    athlete = await _get_or_create_athlete(db, current_user.id)

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

    if body.preferred_ai_provider is not None:
        if body.preferred_ai_provider == "":
            athlete.preferred_ai_provider = None
        elif body.preferred_ai_provider in VALID_PROVIDERS:
            athlete.preferred_ai_provider = body.preferred_ai_provider
        else:
            raise HTTPException(
                status_code=422,
                detail=f"Ungültiger Provider: {body.preferred_ai_provider}. "
                f"Gültig: {', '.join(sorted(VALID_PROVIDERS))}",
            )

    await db.commit()
    await db.refresh(athlete)
    return UserSettingsResponse.from_db(athlete)
