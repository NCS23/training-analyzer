"""Laktatschwellen-Test API Endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.athlete import _get_or_create_athlete
from app.infrastructure.database.models import ThresholdTestModel
from app.infrastructure.database.session import get_db
from app.models.threshold_test import (
    ThresholdTestCreate,
    ThresholdTestListResponse,
    ThresholdTestResponse,
)
from app.services.hr_zone_calculator import calculate_friel_zones

router = APIRouter(prefix="/threshold-tests", tags=["threshold-tests"])


def _build_response(test: ThresholdTestModel) -> ThresholdTestResponse:
    """Erstellt ThresholdTestResponse inkl. Friel-Zonen."""
    zones = calculate_friel_zones(test.lthr)
    return ThresholdTestResponse.from_db(test, friel_zones=zones)


@router.get("", response_model=ThresholdTestListResponse)
async def list_tests(
    db: AsyncSession = Depends(get_db),
) -> ThresholdTestListResponse:
    """Gibt alle Schwellentests zurück (neueste zuerst)."""
    result = await db.execute(
        select(ThresholdTestModel).order_by(ThresholdTestModel.test_date.desc())
    )
    tests = result.scalars().all()
    return ThresholdTestListResponse(
        tests=[_build_response(t) for t in tests],
        total=len(tests),
    )


@router.get("/latest", response_model=ThresholdTestResponse)
async def get_latest_test(
    db: AsyncSession = Depends(get_db),
) -> ThresholdTestResponse:
    """Gibt den neuesten Schwellentest zurück."""
    result = await db.execute(
        select(ThresholdTestModel).order_by(ThresholdTestModel.test_date.desc()).limit(1)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Kein Schwellentest vorhanden")
    return _build_response(test)


@router.post("", response_model=ThresholdTestResponse, status_code=201)
async def create_test(
    body: ThresholdTestCreate,
    db: AsyncSession = Depends(get_db),
) -> ThresholdTestResponse:
    """Erstellt einen neuen Schwellentest und aktualisiert das Athletenprofil."""
    test = ThresholdTestModel(
        test_date=body.test_date,
        lthr=body.lthr,
        max_hr_measured=body.max_hr_measured,
        avg_pace_sec=body.avg_pace_sec,
        session_id=body.session_id,
        notes=body.notes,
    )
    db.add(test)

    # Max-HR im Athletenprofil aktualisieren wenn höher als bisheriger Wert
    if body.max_hr_measured:
        athlete = await _get_or_create_athlete(db)
        if athlete.max_hr is None or body.max_hr_measured > athlete.max_hr:
            athlete.max_hr = body.max_hr_measured

    await db.commit()
    await db.refresh(test)
    return _build_response(test)


@router.delete("/{test_id}", status_code=204)
async def delete_test(
    test_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Löscht einen Schwellentest."""
    result = await db.execute(select(ThresholdTestModel).where(ThresholdTestModel.id == test_id))
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Schwellentest nicht gefunden")
    await db.delete(test)
    await db.commit()
