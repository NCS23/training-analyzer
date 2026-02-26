"""Session API Endpoints — CRUD + CSV Upload mit DB-Persistenz."""

import json
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import AthleteModel, WorkoutModel
from app.infrastructure.database.session import get_db
from app.models.session import (
    DateUpdateRequest,
    LapOverrideRequest,
    LapOverrideResponse,
    LapResponse,
    NotesUpdateRequest,
    SessionListResponse,
    SessionParseResponse,
    SessionResponse,
    SessionSummaryResponse,
    SessionUploadResponse,
    TrainingTypeOverrideRequest,
)
from app.models.training import TrainingSubType, TrainingType
from app.services.csv_parser import TrainingCSVParser
from app.services.fit_parser import TrainingFITParser
from app.services.hr_zone_calculator import calculate_zone_distribution
from app.services.training_type_classifier import classify_training_type

router = APIRouter(prefix="/sessions", tags=["sessions"])

csv_parser = TrainingCSVParser()
fit_parser = TrainingFITParser()


async def _get_athlete_hr_settings(db: AsyncSession) -> tuple[Optional[int], Optional[int]]:
    """Holt Ruhe-HR und Max-HR des Athleten (wenn konfiguriert)."""
    result = await db.execute(select(AthleteModel).limit(1))
    athlete = result.scalar_one_or_none()
    if athlete and athlete.resting_hr and athlete.max_hr:
        return int(athlete.resting_hr), int(athlete.max_hr)  # type: ignore[arg-type]
    return None, None


async def _parse_and_classify(
    content: bytes,
    training_type: TrainingType,
    training_subtype: Optional[TrainingSubType],
    db: AsyncSession,
    parser=None,
) -> dict:
    """Parst Trainingsdatei und klassifiziert — ohne DB-Schreibzugriff.

    Returns dict mit keys: success, errors?, result, summary, laps,
    hr_timeseries, hr_zones, classification, resting_hr, metadata.
    """
    active_parser = parser or csv_parser
    result = active_parser.parse(content, training_type, training_subtype)

    if not result["success"]:
        return {"success": False, "errors": result.get("errors", ["Unbekannter Parse-Fehler"])}

    summary = result.get("summary", {})
    laps = result.get("laps")
    hr_timeseries = result.get("hr_timeseries")

    # HR-Zonen
    resting_hr, max_hr = await _get_athlete_hr_settings(db)
    raw_hr_values = _extract_hr_values_from_result(result)
    hr_zones = calculate_zone_distribution(raw_hr_values, resting_hr, max_hr)

    # Training Type Klassifizierung (nur Running)
    classification = None
    if training_type == TrainingType.RUNNING:
        classification = classify_training_type(
            duration_sec=summary.get("total_duration_seconds", 0),
            hr_avg=summary.get("avg_hr_bpm"),
            hr_max=summary.get("max_hr_bpm"),
            distance_km=summary.get("total_distance_km"),
            laps=laps,
            hr_zone_distribution=hr_zones or None,
        )

    return {
        "success": True,
        "result": result,
        "summary": summary,
        "laps": laps,
        "hr_timeseries": hr_timeseries,
        "hr_zones": hr_zones,
        "classification": classification,
        "resting_hr": resting_hr,
        "metadata": result.get("metadata", {}),
    }


@router.post("/parse", response_model=SessionParseResponse)
async def parse_csv(
    csv_file: UploadFile = File(..., description="Apple Watch CSV Export"),
    training_date: date = Form(..., description="Datum des Trainings (YYYY-MM-DD)"),
    training_type: TrainingType = Form(..., description="Trainingstyp"),
    training_subtype: Optional[TrainingSubType] = Form(None, description="Unter-Typ"),
    notes: Optional[str] = Form(None, description="Notizen"),
    db: AsyncSession = Depends(get_db),
) -> SessionParseResponse:
    """Parse CSV und klassifiziere — ohne Session zu erstellen."""
    if not csv_file.filename or not csv_file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Nur CSV-Dateien werden akzeptiert.")

    content = await csv_file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="CSV-Datei ist leer.")

    parsed = await _parse_and_classify(content, training_type, training_subtype, db)

    if not parsed["success"]:
        return SessionParseResponse(success=False, errors=parsed["errors"])

    return SessionParseResponse(
        success=True,
        data={
            "laps": parsed["laps"],
            "summary": parsed["summary"],
        },
        metadata={
            **parsed["metadata"],
            "training_type_auto": parsed["classification"].training_type if parsed["classification"] else None,
            "training_type_confidence": parsed["classification"].confidence if parsed["classification"] else None,
        },
    )


@router.post("/parse/fit", response_model=SessionParseResponse)
async def parse_fit(
    fit_file: UploadFile = File(..., description="Garmin/Wahoo FIT File"),
    training_date: date = Form(..., description="Datum des Trainings (YYYY-MM-DD)"),
    training_type: TrainingType = Form(..., description="Trainingstyp"),
    training_subtype: Optional[TrainingSubType] = Form(None, description="Unter-Typ"),
    notes: Optional[str] = Form(None, description="Notizen"),
    db: AsyncSession = Depends(get_db),
) -> SessionParseResponse:
    """Parse FIT file und klassifiziere — ohne Session zu erstellen."""
    if not fit_file.filename or not fit_file.filename.lower().endswith(".fit"):
        raise HTTPException(status_code=400, detail="Nur FIT-Dateien werden akzeptiert.")

    content = await fit_file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="FIT-Datei ist leer.")

    parsed = await _parse_and_classify(content, training_type, training_subtype, db, parser=fit_parser)

    if not parsed["success"]:
        return SessionParseResponse(success=False, errors=parsed["errors"])

    return SessionParseResponse(
        success=True,
        data={
            "laps": parsed["laps"],
            "summary": parsed["summary"],
        },
        metadata={
            **parsed["metadata"],
            "training_type_auto": parsed["classification"].training_type if parsed["classification"] else None,
            "training_type_confidence": parsed["classification"].confidence if parsed["classification"] else None,
        },
    )


@router.post("/upload/csv", response_model=SessionUploadResponse, status_code=201)
async def upload_csv(
    csv_file: UploadFile = File(..., description="Apple Watch CSV Export"),
    training_date: date = Form(..., description="Datum des Trainings (YYYY-MM-DD)"),
    training_type: TrainingType = Form(..., description="Trainingstyp"),
    training_subtype: Optional[TrainingSubType] = Form(None, description="Unter-Typ"),
    notes: Optional[str] = Form(None, description="Notizen"),
    lap_overrides_json: Optional[str] = Form(None, description="JSON: {lap_number: type}"),
    training_type_override: Optional[str] = Form(None, description="Manueller Training Type"),
    db: AsyncSession = Depends(get_db),
) -> SessionUploadResponse:
    """Upload Apple Watch CSV und speichere als Session."""
    if not csv_file.filename or not csv_file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Nur CSV-Dateien werden akzeptiert.")

    content = await csv_file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="CSV-Datei ist leer.")

    parsed = await _parse_and_classify(content, training_type, training_subtype, db)

    if not parsed["success"]:
        return SessionUploadResponse(success=False, errors=parsed["errors"])

    summary = parsed["summary"]
    laps = parsed["laps"]
    classification = parsed["classification"]

    # Apply lap overrides from review step
    if lap_overrides_json and laps:
        try:
            overrides = json.loads(lap_overrides_json)
            for lap in laps:
                lap_num = str(lap["lap_number"])
                if lap_num in overrides:
                    lap["user_override"] = overrides[lap_num]
        except (json.JSONDecodeError, KeyError):
            pass  # Ignore malformed overrides

    # Apply training type override from review step
    effective_training_type_override = training_type_override
    if effective_training_type_override and effective_training_type_override not in VALID_TRAINING_TYPES:
        effective_training_type_override = None

    # Erstelle DB-Eintrag
    workout = WorkoutModel(
        date=datetime.combine(training_date, datetime.min.time()),
        workout_type=training_type.value,
        subtype=training_subtype.value if training_subtype else None,
        training_type_auto=classification.training_type if classification else None,
        training_type_confidence=classification.confidence if classification else None,
        training_type_override=effective_training_type_override,
        duration_sec=summary.get("total_duration_seconds"),
        distance_km=summary.get("total_distance_km"),
        pace=summary.get("avg_pace_formatted"),
        hr_avg=summary.get("avg_hr_bpm"),
        hr_max=summary.get("max_hr_bpm"),
        hr_min=summary.get("min_hr_bpm"),
        cadence_avg=summary.get("avg_cadence_spm"),
        csv_data=content.decode("utf-8"),
        laps_json=json.dumps(laps) if laps else None,
        hr_zones_json=json.dumps(parsed["hr_zones"]) if parsed["hr_zones"] else None,
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
            "hr_zones": parsed["hr_zones"],
            "hr_timeseries": parsed["hr_timeseries"],
        },
        metadata={
            **parsed["metadata"],
            "training_date": training_date.isoformat(),
            "training_subtype": training_subtype.value if training_subtype else None,
            "notes": notes,
            "hr_zone_method": "karvonen" if parsed["resting_hr"] else "fixed_3zone",
            "training_type_auto": classification.training_type if classification else None,
            "training_type_confidence": classification.confidence if classification else None,
            "training_type_reasons": classification.reasons if classification else None,
        },
    )


@router.post("/upload/fit", response_model=SessionUploadResponse, status_code=201)
async def upload_fit(
    fit_file: UploadFile = File(..., description="Garmin/Wahoo FIT File"),
    training_date: date = Form(..., description="Datum des Trainings (YYYY-MM-DD)"),
    training_type: TrainingType = Form(..., description="Trainingstyp"),
    training_subtype: Optional[TrainingSubType] = Form(None, description="Unter-Typ"),
    notes: Optional[str] = Form(None, description="Notizen"),
    lap_overrides_json: Optional[str] = Form(None, description="JSON: {lap_number: type}"),
    training_type_override: Optional[str] = Form(None, description="Manueller Training Type"),
    db: AsyncSession = Depends(get_db),
) -> SessionUploadResponse:
    """Upload FIT file und speichere als Session."""
    if not fit_file.filename or not fit_file.filename.lower().endswith(".fit"):
        raise HTTPException(status_code=400, detail="Nur FIT-Dateien werden akzeptiert.")

    content = await fit_file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="FIT-Datei ist leer.")

    parsed = await _parse_and_classify(content, training_type, training_subtype, db, parser=fit_parser)

    if not parsed["success"]:
        return SessionUploadResponse(success=False, errors=parsed["errors"])

    summary = parsed["summary"]
    laps = parsed["laps"]
    classification = parsed["classification"]

    # Apply lap overrides
    if lap_overrides_json and laps:
        try:
            overrides = json.loads(lap_overrides_json)
            for lap in laps:
                lap_num = str(lap["lap_number"])
                if lap_num in overrides:
                    lap["user_override"] = overrides[lap_num]
        except (json.JSONDecodeError, KeyError):
            pass

    # Apply training type override
    effective_training_type_override = training_type_override
    if effective_training_type_override and effective_training_type_override not in VALID_TRAINING_TYPES:
        effective_training_type_override = None

    workout = WorkoutModel(
        date=datetime.combine(training_date, datetime.min.time()),
        workout_type=training_type.value,
        subtype=training_subtype.value if training_subtype else None,
        training_type_auto=classification.training_type if classification else None,
        training_type_confidence=classification.confidence if classification else None,
        training_type_override=effective_training_type_override,
        duration_sec=summary.get("total_duration_seconds"),
        distance_km=summary.get("total_distance_km"),
        pace=summary.get("avg_pace_formatted"),
        hr_avg=summary.get("avg_hr_bpm"),
        hr_max=summary.get("max_hr_bpm"),
        hr_min=summary.get("min_hr_bpm"),
        cadence_avg=summary.get("avg_cadence_spm"),
        csv_data=None,  # No CSV for FIT files
        laps_json=json.dumps(laps) if laps else None,
        hr_zones_json=json.dumps(parsed["hr_zones"]) if parsed["hr_zones"] else None,
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
            "hr_zones": parsed["hr_zones"],
            "hr_timeseries": parsed["hr_timeseries"],
        },
        metadata={
            **parsed["metadata"],
            "training_date": training_date.isoformat(),
            "training_subtype": training_subtype.value if training_subtype else None,
            "notes": notes,
            "hr_zone_method": "karvonen" if parsed["resting_hr"] else "fixed_3zone",
            "training_type_auto": classification.training_type if classification else None,
            "training_type_confidence": classification.confidence if classification else None,
            "training_type_reasons": classification.reasons if classification else None,
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


VALID_TRAINING_TYPES = {
    "recovery",
    "easy",
    "long_run",
    "tempo",
    "intervals",
    "race",
    "hill_repeats",
}


@router.patch("/{session_id}/training-type", response_model=SessionResponse)
async def update_training_type(
    session_id: int,
    body: TrainingTypeOverrideRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Setzt manuellen Training Type Override."""
    if body.training_type not in VALID_TRAINING_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Ungueltiger Training Type. Erlaubt: {', '.join(sorted(VALID_TRAINING_TYPES))}",
        )

    query = select(WorkoutModel).where(WorkoutModel.id == session_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden.")

    workout.training_type_override = body.training_type  # type: ignore[assignment]
    await db.commit()
    await db.refresh(workout)

    return SessionResponse.from_db(workout)


@router.patch("/{session_id}/notes", response_model=SessionResponse)
async def update_notes(
    session_id: int,
    body: NotesUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Aktualisiert die Notizen einer Session."""
    query = select(WorkoutModel).where(WorkoutModel.id == session_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden.")

    workout.notes = body.notes  # type: ignore[assignment]
    await db.commit()
    await db.refresh(workout)

    return SessionResponse.from_db(workout)


@router.patch("/{session_id}/date", response_model=SessionResponse)
async def update_date(
    session_id: int,
    body: DateUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Aktualisiert das Datum einer Session."""
    query = select(WorkoutModel).where(WorkoutModel.id == session_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden.")

    workout.date = body.date  # type: ignore[assignment]
    await db.commit()
    await db.refresh(workout)

    return SessionResponse.from_db(workout)


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


def _extract_hr_values_from_result(result: dict) -> list[int]:
    """Extrahiert HR-Werte aus dem Parse-Ergebnis fuer die Zonen-Berechnung."""
    # Aus HR-Timeseries (Krafttraining)
    timeseries = result.get("hr_timeseries", [])
    if timeseries:
        return [int(p["hr_bpm"]) for p in timeseries if p.get("hr_bpm")]

    # Aus Laps (Lauftraining) — verwende avg_hr_bpm pro Lap, gewichtet nach Dauer
    laps = result.get("laps", [])
    hr_values = []
    for lap in laps:
        avg_hr = lap.get("avg_hr_bpm")
        duration = lap.get("duration_seconds", 0)
        if avg_hr and duration > 0:
            # Simuliere Sekundenwerte mit dem Durchschnitts-HR
            hr_values.extend([int(avg_hr)] * duration)
    return hr_values


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
) -> tuple[Optional[SessionSummaryResponse], Optional[dict]]:
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

    # HR Zones fuer Working-Laps (gewichtet nach Dauer, 3-Zonen Fallback)
    working_hr_values: list[int] = []
    for lap in working:
        avg_hr = lap.get("avg_hr_bpm", 0)
        dur = lap.get("duration_seconds", 0)
        if avg_hr and dur > 0:
            working_hr_values.extend([int(avg_hr)] * dur)

    hr_zones = calculate_zone_distribution(working_hr_values)

    return summary, hr_zones
