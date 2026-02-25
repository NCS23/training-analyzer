"""Athlete Settings API Endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import AthleteModel
from app.infrastructure.database.session import get_db
from app.models.athlete import AthleteSettingsRequest, AthleteSettingsResponse
from app.services.hr_zone_calculator import calculate_karvonen_zones

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


@router.get("/settings", response_model=AthleteSettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
) -> AthleteSettingsResponse:
    """Gibt aktuelle Athleten-Einstellungen zurueck."""
    athlete = await _get_or_create_athlete(db)
    zones = None
    if athlete.resting_hr and athlete.max_hr:
        zones = calculate_karvonen_zones(
            int(athlete.resting_hr),  # type: ignore[arg-type]
            int(athlete.max_hr),  # type: ignore[arg-type]
        )
    return AthleteSettingsResponse.from_db(athlete, zones)


@router.put("/settings", response_model=AthleteSettingsResponse)
async def update_settings(
    body: AthleteSettingsRequest,
    db: AsyncSession = Depends(get_db),
) -> AthleteSettingsResponse:
    """Aktualisiert Athleten-Einstellungen (Ruhe-HR, Max-HR)."""
    athlete = await _get_or_create_athlete(db)

    if body.resting_hr is not None:
        athlete.resting_hr = body.resting_hr  # type: ignore[assignment]
    if body.max_hr is not None:
        athlete.max_hr = body.max_hr  # type: ignore[assignment]

    await db.commit()
    await db.refresh(athlete)

    zones = None
    if athlete.resting_hr and athlete.max_hr:
        zones = calculate_karvonen_zones(
            int(athlete.resting_hr),  # type: ignore[arg-type]
            int(athlete.max_hr),  # type: ignore[arg-type]
        )
    return AthleteSettingsResponse.from_db(athlete, zones)
