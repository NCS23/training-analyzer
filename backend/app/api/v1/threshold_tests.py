"""Laktatschwellen-Test API Endpoints."""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.athlete import _get_or_create_athlete
from app.infrastructure.database.models import ThresholdTestModel, WorkoutModel
from app.infrastructure.database.session import get_db
from app.models.threshold_test import (
    ThresholdAnalysisResponse,
    ThresholdTestCreate,
    ThresholdTestListResponse,
    ThresholdTestResponse,
)
from app.services.hr_zone_calculator import calculate_friel_zones

logger = logging.getLogger(__name__)

# Friel-Test: Ø HR der letzten 20 Min eines 30-Min-Maximaltests
_ANALYSIS_WINDOW_SEC = 20 * 60  # 1200 Sekunden
_MIN_SESSION_DURATION_SEC = 25 * 60  # Mindestens 25 Min Session

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


@router.get("/analyze/{session_id}", response_model=ThresholdAnalysisResponse)
async def analyze_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> ThresholdAnalysisResponse:
    """Berechnet LTHR aus einer Session (Ø HR der letzten 20 Min).

    Basiert auf dem 30-Min-Friel-Test: Der Athlet läuft 30 Min maximal,
    die Durchschnitts-HR der letzten 20 Min entspricht der LTHR.
    """
    result = await db.execute(select(WorkoutModel).where(WorkoutModel.id == session_id))
    workout = result.scalar_one_or_none()
    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")

    # HR-Werte extrahieren (per-Sekunde)
    hr_values = _extract_hr_from_workout(workout)
    if not hr_values:
        raise HTTPException(status_code=400, detail="Keine HR-Daten in dieser Session vorhanden")

    total_seconds = len(hr_values)
    if total_seconds < _MIN_SESSION_DURATION_SEC:
        raise HTTPException(
            status_code=400,
            detail=f"Session zu kurz ({total_seconds // 60} Min). Mindestens 25 Min erforderlich.",
        )

    # Letzte 20 Min für LTHR-Berechnung
    analysis_window = hr_values[-_ANALYSIS_WINDOW_SEC:]
    lthr = round(sum(analysis_window) / len(analysis_window))
    max_hr = max(hr_values)

    # Pace aus Session extrahieren (wenn vorhanden)
    avg_pace_sec = _extract_avg_pace(workout)

    duration_minutes = round(total_seconds / 60.0, 1)
    friel_zones = calculate_friel_zones(lthr)

    return ThresholdAnalysisResponse(
        session_id=session_id,
        session_date=workout.date,
        duration_minutes=duration_minutes,
        lthr=lthr,
        max_hr_measured=max_hr,
        avg_pace_sec=avg_pace_sec,
        friel_zones=friel_zones,
        hr_sample_count=len(analysis_window),
    )


def _extract_hr_from_workout(workout: WorkoutModel) -> list[int]:
    """Extrahiert per-Sekunde HR-Werte aus einer Session."""
    # 1. GPS Track (beste Qualität — per-Sekunde)
    if workout.gps_track_json:
        track = json.loads(str(workout.gps_track_json))
        points = track.get("points", [])
        hr_values = [int(p["hr"]) for p in points if p.get("hr") is not None]
        if hr_values:
            return hr_values

    # 2. HR Timeseries (FIT ohne GPS)
    if workout.hr_timeseries_json:
        ts = json.loads(str(workout.hr_timeseries_json))
        hr_values = [int(p["hr_bpm"]) for p in ts if p.get("hr_bpm")]
        if hr_values:
            return hr_values

    return []


def _extract_avg_pace(workout: WorkoutModel) -> float | None:
    """Extrahiert Durchschnittspace aus Session-Daten."""
    if workout.gps_track_json:
        track = json.loads(str(workout.gps_track_json))
        total_dist = track.get("total_distance_km")
        total_time = track.get("total_duration_sec")
        if total_dist and total_time and total_dist > 0:
            return round(total_time / total_dist, 1)
    return None


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
