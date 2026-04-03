"""Athlete Settings API Endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.infrastructure.database.models import AthleteModel, ThresholdTestModel, UserModel
from app.infrastructure.database.session import get_db
from app.models.athlete import AthleteSettingsRequest, AthleteSettingsResponse
from app.services.hr_zone_calculator import calculate_friel_zones, calculate_karvonen_zones

router = APIRouter(prefix="/athlete", tags=["athlete"])


async def _get_or_create_athlete(db: AsyncSession, user_id: int) -> AthleteModel:
    """Holt den Athleten oder erstellt einen neuen (Singleton pro User)."""
    result = await db.execute(select(AthleteModel).where(AthleteModel.user_id == user_id).limit(1))
    athlete = result.scalar_one_or_none()
    if not athlete:
        athlete = AthleteModel(user_id=user_id)
        db.add(athlete)
        await db.commit()
        await db.refresh(athlete)
    return athlete


async def _get_latest_lthr(db: AsyncSession, user_id: int) -> int | None:
    """Holt die LTHR aus dem neuesten Schwellentest des Users."""
    result = await db.execute(
        select(ThresholdTestModel.lthr)
        .where(ThresholdTestModel.user_id == user_id)
        .order_by(ThresholdTestModel.test_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def _build_settings_response(
    athlete: AthleteModel, db: AsyncSession, user_id: int
) -> AthleteSettingsResponse:
    """Erstellt AthleteSettingsResponse mit Zonen (Friel bevorzugt)."""
    karvonen_zones = None
    if athlete.resting_hr and athlete.max_hr:
        karvonen_zones = calculate_karvonen_zones(athlete.resting_hr, athlete.max_hr)

    lthr = await _get_latest_lthr(db, user_id)
    friel_zones = calculate_friel_zones(lthr) if lthr else None

    return AthleteSettingsResponse.from_db(
        athlete,
        zones=karvonen_zones,
        lthr=lthr,
        friel_zones=friel_zones,
    )


@router.get("/settings", response_model=AthleteSettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> AthleteSettingsResponse:
    """Gibt aktuelle Athleten-Einstellungen zurück."""
    athlete = await _get_or_create_athlete(db, current_user.id)
    return await _build_settings_response(athlete, db, current_user.id)


@router.put("/settings", response_model=AthleteSettingsResponse)
async def update_settings(
    body: AthleteSettingsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> AthleteSettingsResponse:
    """Aktualisiert Athleten-Einstellungen (Ruhe-HR, Max-HR)."""
    athlete = await _get_or_create_athlete(db, current_user.id)

    if body.resting_hr is not None:
        athlete.resting_hr = body.resting_hr
    if body.max_hr is not None:
        athlete.max_hr = body.max_hr
    if body.elevation_gain_factor is not None:
        athlete.elevation_gain_factor = body.elevation_gain_factor
    if body.elevation_loss_factor is not None:
        athlete.elevation_loss_factor = body.elevation_loss_factor

    await db.commit()
    await db.refresh(athlete)
    return await _build_settings_response(athlete, db, current_user.id)
