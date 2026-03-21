"""Athlete Settings API Endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import AthleteModel, ThresholdTestModel
from app.infrastructure.database.session import get_db
from app.models.athlete import AthleteSettingsRequest, AthleteSettingsResponse
from app.services.hr_zone_calculator import calculate_friel_zones, calculate_karvonen_zones

router = APIRouter(prefix="/athlete", tags=["athlete"])


async def _get_or_create_athlete(db: AsyncSession) -> AthleteModel:
    """Holt den Athleten oder erstellt einen neuen (Singleton)."""
    result = await db.execute(select(AthleteModel).limit(1))
    athlete = result.scalar_one_or_none()
    if not athlete:
        athlete = AthleteModel()
        db.add(athlete)
        await db.commit()
        await db.refresh(athlete)
    return athlete


async def _get_latest_lthr(db: AsyncSession) -> int | None:
    """Holt die LTHR aus dem neuesten Schwellentest."""
    result = await db.execute(
        select(ThresholdTestModel.lthr).order_by(ThresholdTestModel.test_date.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def _build_settings_response(
    athlete: AthleteModel, db: AsyncSession
) -> AthleteSettingsResponse:
    """Erstellt AthleteSettingsResponse mit Zonen (Friel bevorzugt)."""
    karvonen_zones = None
    if athlete.resting_hr and athlete.max_hr:
        karvonen_zones = calculate_karvonen_zones(athlete.resting_hr, athlete.max_hr)

    lthr = await _get_latest_lthr(db)
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
) -> AthleteSettingsResponse:
    """Gibt aktuelle Athleten-Einstellungen zurück."""
    athlete = await _get_or_create_athlete(db)
    return await _build_settings_response(athlete, db)


@router.put("/settings", response_model=AthleteSettingsResponse)
async def update_settings(
    body: AthleteSettingsRequest,
    db: AsyncSession = Depends(get_db),
) -> AthleteSettingsResponse:
    """Aktualisiert Athleten-Einstellungen (Ruhe-HR, Max-HR)."""
    athlete = await _get_or_create_athlete(db)

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
    return await _build_settings_response(athlete, db)
