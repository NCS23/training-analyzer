"""Session API Endpoints — CRUD + CSV Upload mit DB-Persistenz."""

import json
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import WorkoutModel
from app.infrastructure.database.session import get_db
from app.models.session import (
    HRZoneResponse,
    HRZonesResponse,
    LapOverrideRequest,
    LapOverrideResponse,
    LapResponse,
    SessionListResponse,
    SessionResponse,
    SessionSummaryResponse,
    SessionUploadResponse,
)
from app.models.training import TrainingSubType, TrainingType
from app.services.csv_parser import TrainingCSVParser

router = APIRouter(prefix="/sessions", tags=["sessions"])

csv_parser = TrainingCSVParser()


@router.post("/upload/csv", response_model=SessionUploadResponse, status_code=201)
async def upload_csv(
    csv_file: UploadFile = File(..., description="Apple Watch CSV Export"),
    training_date: date = Form(..., description="Datum des Trainings (YYYY-MM-DD)"),
    training_type: TrainingType = Form(..., description="Trainingstyp"),
    training_subtype: Optional[TrainingSubType] = Form(None, description="Unter-Typ"),
    notes: Optional[str] = Form(None, description="Notizen"),
    db: AsyncSession = Depends(get_db),
) -> SessionUploadResponse:
    """Upload Apple Watch CSV und speichere als Session."""
    # Validiere Dateiformat
    if not csv_file.filename or not csv_file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Nur CSV-Dateien werden akzeptiert.")

    content = await csv_file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="CSV-Datei ist leer.")

    # Parse CSV
    result = csv_parser.parse(content, training_type, training_subtype)

    if not result["success"]:
        return SessionUploadResponse(
            success=False,
            errors=result.get("errors", ["Unbekannter Parse-Fehler"]),
        )

    # Extrahiere Summary-Daten fuer DB-Felder
    summary = result.get("summary", {})
    laps = result.get("laps")
    hr_zones = result.get("hr_zones")

    # Erstelle DB-Eintrag
    workout = WorkoutModel(
        date=datetime.combine(training_date, datetime.min.time()),
        workout_type=training_type.value,
        subtype=training_subtype.value if training_subtype else None,
        duration_sec=summary.get("total_duration_seconds"),
        distance_km=summary.get("total_distance_km"),
        pace=summary.get("avg_pace_formatted"),
        hr_avg=summary.get("avg_hr_bpm"),
        hr_max=summary.get("max_hr_bpm"),
        hr_min=summary.get("min_hr_bpm"),
        cadence_avg=summary.get("avg_cadence_spm"),
        csv_data=content.decode("utf-8"),
        laps_json=json.dumps(laps) if laps else None,
        hr_zones_json=json.dumps(hr_zones) if hr_zones else None,
        notes=notes,
    )

    db.add(workout)
    await db.commit()
    await db.refresh(workout)

    return SessionUploadResponse(
        success=True,
        session_id=int(workout.id),  # type: ignore[arg-type]
        data={
            "laps": laps,
            "summary": summary,
            "hr_zones": hr_zones,
            "hr_timeseries": result.get("hr_timeseries"),
        },
        metadata={
            **result.get("metadata", {}),
            "training_date": training_date.isoformat(),
            "training_subtype": training_subtype.value if training_subtype else None,
            "notes": notes,
        },
    )


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1, description="Seitennummer"),
    page_size: int = Query(20, ge=1, le=100, description="Eintraege pro Seite"),
    workout_type: Optional[TrainingType] = Query(None, description="Filter nach Typ"),
    db: AsyncSession = Depends(get_db),
) -> SessionListResponse:
    """Liste aller Sessions mit Paginierung."""
    # Count query
    count_query = select(func.count(WorkoutModel.id))
    if workout_type:
        count_query = count_query.where(WorkoutModel.workout_type == workout_type.value)
    total = (await db.execute(count_query)).scalar() or 0

    # Data query
    query = select(WorkoutModel).order_by(WorkoutModel.date.desc())
    if workout_type:
        query = query.where(WorkoutModel.workout_type == workout_type.value)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    workouts = result.scalars().all()

    from app.models.session import SessionListItem

    return SessionListResponse(
        sessions=[SessionListItem.from_db(w) for w in workouts],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Einzelne Session mit allen Details."""
    query = select(WorkoutModel).where(WorkoutModel.id == session_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden.")

    return SessionResponse.from_db(workout)


@router.patch("/{session_id}/laps", response_model=LapOverrideResponse)
async def update_lap_overrides(
    session_id: int,
    body: LapOverrideRequest,
    db: AsyncSession = Depends(get_db),
) -> LapOverrideResponse:
    """Aktualisiert Lap-Type Overrides und berechnet Working-Laps Metriken."""
    query = select(WorkoutModel).where(WorkoutModel.id == session_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden.")

    if not workout.laps_json:
        raise HTTPException(status_code=400, detail="Session hat keine Laps.")

    # Parse existing laps
    laps_raw = json.loads(str(workout.laps_json))

    # Apply overrides
    override_map = {o.lap_number: o.user_override for o in body.overrides}
    for lap in laps_raw:
        lap_num = lap["lap_number"]
        if lap_num in override_map:
            lap["user_override"] = override_map[lap_num]

    # Save updated laps back to DB
    workout.laps_json = json.dumps(laps_raw)  # type: ignore[assignment]
    await db.commit()
    await db.refresh(workout)

    # Build response with working-laps aggregation
    laps = [LapResponse(**lap) for lap in laps_raw]
    summary_working, hr_zones_working = _calculate_working_laps_metrics(laps_raw)

    return LapOverrideResponse(
        success=True,
        laps=laps,
        summary_working=summary_working,
        hr_zones_working=hr_zones_working,
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Loescht eine Session."""
    query = select(WorkoutModel).where(WorkoutModel.id == session_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden.")

    await db.delete(workout)
    await db.commit()


# --- Helper ---

EXCLUDED_TYPES = {"warmup", "cooldown", "pause"}


def _get_effective_type(lap: dict) -> str:
    """Gibt den effektiven Lap-Typ zurueck (Override > Suggested)."""
    return lap.get("user_override") or lap.get("suggested_type") or "unclassified"


def _format_duration(seconds: int) -> str:
    """Formatiert Sekunden zu HH:MM:SS oder MM:SS."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _format_pace(pace: Optional[float]) -> Optional[str]:
    """Formatiert Pace von Dezimalminuten zu MM:SS."""
    if not pace:
        return None
    minutes = int(pace)
    seconds = int((pace - minutes) * 60)
    return f"{minutes}:{seconds:02d}"


def _calculate_working_laps_metrics(
    laps_raw: list[dict],
) -> tuple[Optional[SessionSummaryResponse], Optional[HRZonesResponse]]:
    """Berechnet Metriken nur fuer Working-Laps (ohne Warmup/Cooldown/Pause)."""
    working = [lap for lap in laps_raw if _get_effective_type(lap) not in EXCLUDED_TYPES]

    if not working:
        return None, None

    total_duration = sum(lap.get("duration_seconds", 0) for lap in working)
    total_distance = sum(lap.get("distance_km", 0) or 0 for lap in working)

    hr_values = [lap["avg_hr_bpm"] for lap in working if lap.get("avg_hr_bpm")]
    cadence_values = [lap["avg_cadence_spm"] for lap in working if lap.get("avg_cadence_spm")]

    avg_pace = (total_duration / 60) / total_distance if total_distance > 0 else None

    summary = SessionSummaryResponse(
        total_duration_seconds=total_duration,
        total_duration_formatted=_format_duration(total_duration),
        total_distance_km=round(total_distance, 2) if total_distance > 0 else None,
        avg_pace_min_per_km=round(avg_pace, 2) if avg_pace else None,
        avg_pace_formatted=_format_pace(avg_pace),
        avg_hr_bpm=round(sum(hr_values) / len(hr_values)) if hr_values else None,
        max_hr_bpm=max(
            (lap.get("max_hr_bpm") or lap.get("avg_hr_bpm", 0) for lap in working),
            default=None,
        ),
        min_hr_bpm=min(
            (lap.get("min_hr_bpm") or lap.get("avg_hr_bpm", 999) for lap in working),
            default=None,
        ),
        avg_cadence_spm=(
            round(sum(cadence_values) / len(cadence_values)) if cadence_values else None
        ),
    )

    # HR Zones fuer Working-Laps (gewichtet nach Dauer)
    zone1 = 0
    zone2 = 0
    zone3 = 0
    for lap in working:
        hr = lap.get("avg_hr_bpm", 0)
        dur = lap.get("duration_seconds", 0)
        if hr < 150:
            zone1 += dur
        elif hr < 160:
            zone2 += dur
        else:
            zone3 += dur

    total_zone_time = zone1 + zone2 + zone3

    hr_zones = HRZonesResponse(
        zone_1_recovery=HRZoneResponse(
            seconds=zone1,
            percentage=round(zone1 / total_zone_time * 100, 1) if total_zone_time > 0 else 0,
            label="< 150 bpm",
        ),
        zone_2_base=HRZoneResponse(
            seconds=zone2,
            percentage=round(zone2 / total_zone_time * 100, 1) if total_zone_time > 0 else 0,
            label="150-160 bpm",
        ),
        zone_3_tempo=HRZoneResponse(
            seconds=zone3,
            percentage=round(zone3 / total_zone_time * 100, 1) if total_zone_time > 0 else 0,
            label="> 160 bpm",
        ),
    )

    return summary, hr_zones
