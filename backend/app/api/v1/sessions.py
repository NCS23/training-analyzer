"""Session API Endpoints — CRUD + CSV Upload mit DB-Persistenz."""

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    AthleteModel,
    PlannedSessionModel,
    WeeklyPlanDayModel,
    WorkoutModel,
)
from app.infrastructure.database.session import get_db
from app.models.ai_analysis import AnalyzeRequest, SessionAnalysisResponse
from app.models.ai_recommendation import (
    RecommendationResponse,
    RecommendationsListResponse,
    RecommendationStatusUpdate,
)
from app.models.segment import ComparisonResponse, laps_to_segments
from app.models.session import (
    DateUpdateRequest,
    LapOverrideRequest,
    LapOverrideResponse,
    LapResponse,
    NotesUpdateRequest,
    PlannedEntryUpdateRequest,
    RecalculateZonesRequest,
    RpeUpdateRequest,
    SessionListResponse,
    SessionParseResponse,
    SessionResponse,
    SessionSummaryResponse,
    SessionUploadResponse,
    TrainingTypeOverrideRequest,
)
from app.models.training import TrainingSubType, TrainingType
from app.models.weekly_plan import RunDetails
from app.services.csv_parser import TrainingCSVParser
from app.services.fit_parser import TrainingFITParser
from app.services.hr_zone_calculator import calculate_zone_distribution
from app.services.km_split_calculator import calculate_km_splits, calculate_session_gap
from app.services.segment_matcher import build_comparison
from app.services.training_type_classifier import classify_training_type

router = APIRouter(prefix="/sessions", tags=["sessions"])

csv_parser = TrainingCSVParser()
fit_parser = TrainingFITParser()

VALID_TRAINING_TYPES = {
    "recovery",
    "easy",
    "long_run",
    "progression",
    "tempo",
    "intervals",
    "repetitions",
    "fartlek",
    "race",
}


# --- B4: Parameter-Objekt für Upload Form-Daten ---


@dataclass
class SessionUploadForm:
    """DTO für Upload-Formular (CSV + FIT gemeinsam)."""

    training_date: date = Form(..., description="Datum des Trainings (YYYY-MM-DD)")
    training_type: TrainingType = Form(..., description="Trainingstyp")
    training_subtype: Optional[TrainingSubType] = Form(None, description="Unter-Typ")
    notes: Optional[str] = Form(None, description="Notizen")
    rpe: Optional[int] = Form(None, ge=1, le=10, description="RPE (1-10)")
    lap_overrides_json: Optional[str] = Form(None, description="JSON: {lap_number: type}")
    training_type_override: Optional[str] = Form(None, description="Manueller Training Type")
    planned_entry_id: Optional[int] = Form(
        None, description="Manuelle Zuordnung zu geplanter Session"
    )


async def _auto_match_planned_entry(
    db: AsyncSession,
    workout: WorkoutModel,
) -> None:
    """Auto-match a workout to a planned session (E17/S10).

    Matches by date + workout_type. Only sets planned_entry_id if unset.
    Now links to planned_sessions instead of weekly_plan_entries.
    """
    if workout.planned_entry_id is not None:
        return  # Already linked

    workout_dt = workout.date
    workout_date = workout_dt.date() if isinstance(workout_dt, datetime) else workout_dt

    # Find the Monday of the week
    week_start = workout_date - timedelta(days=workout_date.weekday())
    day_of_week = workout_date.weekday()  # 0=Mon, 6=Sun

    # Find the day entry
    day_result = await db.execute(
        select(WeeklyPlanDayModel).where(
            WeeklyPlanDayModel.week_start == week_start,
            WeeklyPlanDayModel.day_of_week == day_of_week,
        )
    )
    day = day_result.scalar_one_or_none()
    if not day:
        return

    # Find matching planned session by type
    type_map = {"strength": "strength", "running": "running"}
    session_result = await db.execute(
        select(PlannedSessionModel)
        .where(PlannedSessionModel.day_id == day.id)
        .order_by(PlannedSessionModel.position)
    )
    for session in session_result.scalars().all():
        expected = type_map.get(str(session.training_type), str(session.training_type))
        if str(workout.workout_type) == expected:
            workout.planned_entry_id = session.id
            await db.commit()
            return


async def _get_athlete_hr_settings(db: AsyncSession) -> tuple[Optional[int], Optional[int]]:
    """Holt Ruhe-HR und Max-HR des Athleten (wenn konfiguriert)."""
    result = await db.execute(select(AthleteModel).limit(1))
    athlete = result.scalar_one_or_none()
    if athlete and athlete.resting_hr and athlete.max_hr:
        return athlete.resting_hr, athlete.max_hr
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
        "max_hr": max_hr,
        "metadata": result.get("metadata", {}),
        "gps_track": result.get("gps_track"),
    }


# --- B1: Shared Upload-Hilfsfunktionen ---


async def _validate_upload_file(file: UploadFile, extension: str, label: str) -> bytes:
    """Validiert Dateiendung und liest Inhalt."""
    if not file.filename or not file.filename.lower().endswith(extension):
        raise HTTPException(status_code=400, detail=f"Nur {label}-Dateien werden akzeptiert.")
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail=f"{label}-Datei ist leer.")
    return content


def _apply_lap_overrides(laps: list[dict] | None, overrides_json: str | None) -> None:
    """Wendet Lap-Overrides aus JSON auf Laps an (in-place)."""
    if not overrides_json or not laps:
        return
    try:
        overrides = json.loads(overrides_json)
        for lap in laps:
            lap_num = str(lap["lap_number"])
            if lap_num in overrides:
                lap["user_override"] = overrides[lap_num]
    except (json.JSONDecodeError, KeyError):
        pass


def _validate_type_override(override: str | None) -> str | None:
    """Gibt Override zurück wenn gültig, sonst None."""
    if override and override not in VALID_TRAINING_TYPES:
        return None
    return override


def _build_workout_model(
    form: SessionUploadForm,
    parsed: dict,
    csv_data: str | None,
) -> WorkoutModel:
    """Erstellt WorkoutModel aus Form-Daten und Parse-Ergebnis."""
    summary = parsed["summary"]
    classification = parsed["classification"]
    gps_track = parsed.get("gps_track")
    hr_timeseries = parsed.get("hr_timeseries")
    laps = parsed["laps"]

    return WorkoutModel(
        date=datetime.combine(form.training_date, datetime.min.time()),
        workout_type=form.training_type.value,
        subtype=form.training_subtype.value if form.training_subtype else None,
        training_type_auto=classification.training_type if classification else None,
        training_type_confidence=classification.confidence if classification else None,
        training_type_override=_validate_type_override(form.training_type_override),
        duration_sec=summary.get("total_duration_seconds"),
        distance_km=summary.get("total_distance_km"),
        pace=summary.get("avg_pace_formatted"),
        hr_avg=summary.get("avg_hr_bpm"),
        hr_max=summary.get("max_hr_bpm"),
        hr_min=summary.get("min_hr_bpm"),
        cadence_avg=summary.get("avg_cadence_spm"),
        csv_data=csv_data,
        laps_json=json.dumps(laps) if laps else None,
        hr_zones_json=json.dumps(parsed["hr_zones"]) if parsed["hr_zones"] else None,
        hr_timeseries_json=json.dumps(hr_timeseries) if hr_timeseries else None,
        gps_track_json=json.dumps(gps_track) if gps_track else None,
        has_gps=bool(gps_track),
        athlete_resting_hr=parsed["resting_hr"],
        athlete_max_hr=parsed["max_hr"],
        notes=form.notes,
        rpe=form.rpe,
    )


async def _save_and_respond(
    db: AsyncSession,
    workout: WorkoutModel,
    parsed: dict,
    form: SessionUploadForm,
) -> SessionUploadResponse:
    """Speichert Workout in DB und erstellt Response."""
    if form.planned_entry_id is not None:
        workout.planned_entry_id = form.planned_entry_id

    db.add(workout)
    await db.commit()
    await db.refresh(workout)

    if form.planned_entry_id is None:
        await _auto_match_planned_entry(db, workout)

    classification = parsed["classification"]
    gps_track = parsed.get("gps_track")

    return SessionUploadResponse(
        success=True,
        session_id=workout.id,
        data={
            "laps": parsed["laps"],
            "summary": parsed["summary"],
            "hr_zones": parsed["hr_zones"],
            "hr_timeseries": parsed["hr_timeseries"],
        },
        metadata={
            **parsed["metadata"],
            "training_date": form.training_date.isoformat(),
            "training_subtype": form.training_subtype.value if form.training_subtype else None,
            "notes": form.notes,
            "hr_zone_method": "karvonen" if parsed["resting_hr"] else "fixed_3zone",
            "training_type_auto": classification.training_type if classification else None,
            "training_type_confidence": classification.confidence if classification else None,
            "training_type_reasons": classification.reasons if classification else None,
            "has_gps": bool(gps_track),
        },
    )


async def _upload_session(
    content: bytes,
    parser: TrainingCSVParser | TrainingFITParser,
    form: SessionUploadForm,
    db: AsyncSession,
    csv_data: str | None = None,
    file_name: str | None = None,
    file_format: str | None = None,
) -> SessionUploadResponse:
    """Gemeinsame Upload-Logik für CSV und FIT."""
    parsed = await _parse_and_classify(
        content, form.training_type, form.training_subtype, db, parser=parser
    )
    if not parsed["success"]:
        return SessionUploadResponse(success=False, errors=parsed["errors"])

    _apply_lap_overrides(parsed["laps"], form.lap_overrides_json)
    workout = _build_workout_model(form, parsed, csv_data)

    # Originaldatei mitspeichern fuer Reparse (#349)
    workout.original_file_content = content
    workout.original_file_name = file_name
    workout.original_file_format = file_format

    return await _save_and_respond(db, workout, parsed, form)


async def _parse_session(
    content: bytes,
    parser: TrainingCSVParser | TrainingFITParser,
    training_type: TrainingType,
    training_subtype: TrainingSubType | None,
    db: AsyncSession,
) -> SessionParseResponse:
    """Gemeinsame Parse-Logik für CSV und FIT."""
    parsed = await _parse_and_classify(content, training_type, training_subtype, db, parser=parser)
    if not parsed["success"]:
        return SessionParseResponse(success=False, errors=parsed["errors"])

    classification = parsed["classification"]
    return SessionParseResponse(
        success=True,
        data={"laps": parsed["laps"], "summary": parsed["summary"]},
        metadata={
            **parsed["metadata"],
            "training_type_auto": classification.training_type if classification else None,
            "training_type_confidence": classification.confidence if classification else None,
        },
    )


@router.post("/parse", response_model=SessionParseResponse)
async def parse_csv(
    csv_file: UploadFile = File(..., description="Apple Watch CSV Export"),
    training_date: date = Form(..., description="Datum des Trainings (YYYY-MM-DD)"),  # noqa: ARG001
    training_type: TrainingType = Form(..., description="Trainingstyp"),
    training_subtype: Optional[TrainingSubType] = Form(None, description="Unter-Typ"),
    notes: Optional[str] = Form(None, description="Notizen"),  # noqa: ARG001
    db: AsyncSession = Depends(get_db),
) -> SessionParseResponse:
    """Parse CSV und klassifiziere — ohne Session zu erstellen."""
    content = await _validate_upload_file(csv_file, ".csv", "CSV")
    return await _parse_session(content, csv_parser, training_type, training_subtype, db)


@router.post("/parse/fit", response_model=SessionParseResponse)
async def parse_fit(
    fit_file: UploadFile = File(..., description="Garmin/Wahoo FIT File"),
    training_date: date = Form(..., description="Datum des Trainings (YYYY-MM-DD)"),  # noqa: ARG001
    training_type: TrainingType = Form(..., description="Trainingstyp"),
    training_subtype: Optional[TrainingSubType] = Form(None, description="Unter-Typ"),
    notes: Optional[str] = Form(None, description="Notizen"),  # noqa: ARG001
    db: AsyncSession = Depends(get_db),
) -> SessionParseResponse:
    """Parse FIT file und klassifiziere — ohne Session zu erstellen."""
    content = await _validate_upload_file(fit_file, ".fit", "FIT")
    return await _parse_session(content, fit_parser, training_type, training_subtype, db)


@router.post("/upload/csv", response_model=SessionUploadResponse, status_code=201)
async def upload_csv(
    csv_file: UploadFile = File(..., description="Apple Watch CSV Export"),
    form: SessionUploadForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> SessionUploadResponse:
    """Upload Apple Watch CSV und speichere als Session."""
    content = await _validate_upload_file(csv_file, ".csv", "CSV")
    return await _upload_session(
        content,
        csv_parser,
        form,
        db,
        csv_data=content.decode("utf-8"),
        file_name=csv_file.filename,
        file_format="csv",
    )


@router.post("/upload/fit", response_model=SessionUploadResponse, status_code=201)
async def upload_fit(
    fit_file: UploadFile = File(..., description="Garmin/Wahoo FIT File"),
    form: SessionUploadForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> SessionUploadResponse:
    """Upload FIT file und speichere als Session."""
    content = await _validate_upload_file(fit_file, ".fit", "FIT")
    return await _upload_session(
        content,
        fit_parser,
        form,
        db,
        file_name=fit_file.filename,
        file_format="fit",
    )


@router.get("", response_model=SessionListResponse)
async def list_sessions(
    page: int = Query(1, ge=1, description="Seitennummer"),
    page_size: int = Query(20, ge=1, le=100, description="Eintraege pro Seite"),
    workout_type: Optional[TrainingType] = Query(None, description="Filter nach Workout-Typ"),
    training_type: Optional[str] = Query(None, description="Filter nach Training-Typ (effective)"),
    date_from: Optional[date] = Query(None, description="Datum ab (inklusiv)"),
    date_to: Optional[date] = Query(None, description="Datum bis (inklusiv)"),
    search: Optional[str] = Query(None, description="Freitext-Suche (Notizen)"),
    db: AsyncSession = Depends(get_db),
) -> SessionListResponse:
    """Liste aller Sessions mit Paginierung und Filtern."""
    from app.models.session import SessionListItem

    # Build shared filter conditions
    conditions = []
    if workout_type:
        conditions.append(WorkoutModel.workout_type == workout_type.value)
    if date_from:
        conditions.append(WorkoutModel.date >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        conditions.append(WorkoutModel.date <= datetime.combine(date_to, datetime.max.time()))
    if training_type:
        # Effective type: override takes priority, fallback to auto
        conditions.append(
            func.coalesce(
                WorkoutModel.training_type_override,
                WorkoutModel.training_type_auto,
            )
            == training_type
        )
    if search and search.strip():
        conditions.append(WorkoutModel.notes.ilike(f"%{search.strip()}%"))

    # Count query
    count_query = select(func.count(WorkoutModel.id))
    for cond in conditions:
        count_query = count_query.where(cond)
    total = (await db.execute(count_query)).scalar() or 0

    # Data query
    query = select(WorkoutModel).order_by(WorkoutModel.date.desc())
    for cond in conditions:
        query = query.where(cond)
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    workouts = result.scalars().all()

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


@router.get("/{session_id}/track")
async def get_session_track(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """GPS Track einer Session (separater Endpoint fuer Performance)."""
    query = select(WorkoutModel).where(WorkoutModel.id == session_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden.")

    if not workout.gps_track_json:
        return {"has_gps": False, "track": None}

    track = json.loads(str(workout.gps_track_json))
    return {"has_gps": True, "track": track}


async def _get_athlete_elevation_factors(
    db: AsyncSession,
) -> tuple[Optional[float], Optional[float]]:
    """Holt Elevation-Korrekturfaktoren des Athleten (wenn konfiguriert)."""
    result = await db.execute(select(AthleteModel).limit(1))
    athlete = result.scalar_one_or_none()
    if athlete:
        gain = athlete.elevation_gain_factor if athlete.elevation_gain_factor is not None else None
        loss = athlete.elevation_loss_factor if athlete.elevation_loss_factor is not None else None
        return gain, loss
    return None, None


@router.get("/{session_id}/km-splits")
async def get_km_splits(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Per-Kilometer Splits berechnet aus GPS Track."""
    query = select(WorkoutModel).where(WorkoutModel.id == session_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden.")

    if not workout.gps_track_json:
        return {"has_splits": False, "splits": None, "session_gap": None}

    gain_factor, loss_factor = await _get_athlete_elevation_factors(db)
    track = json.loads(str(workout.gps_track_json))
    splits = calculate_km_splits(track, gain_factor=gain_factor, loss_factor=loss_factor)
    session_gap = calculate_session_gap(splits)

    return {
        "has_splits": bool(splits),
        "splits": splits,
        "session_gap_min_per_km": session_gap,
        "session_gap_formatted": _format_pace(session_gap) if session_gap else None,
        "elevation_factors": {
            "gain_sec_per_100m": gain_factor or 10.0,
            "loss_sec_per_100m": loss_factor or 5.0,
        },
    }


@router.get("/{session_id}/working-zones")
async def get_working_zones(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Berechnet Working-Laps HR-Zonen (ohne DB-Schreibzugriff)."""
    query = select(WorkoutModel).where(WorkoutModel.id == session_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout or not workout.laps_json:
        return {"hr_zones_working": None}

    # Use session's stored athlete settings (historized), fallback to current
    resting_hr: Optional[int] = workout.athlete_resting_hr
    max_hr: Optional[int] = workout.athlete_max_hr
    if resting_hr is None or max_hr is None:
        resting_hr, max_hr = await _get_athlete_hr_settings(db)

    laps_raw = json.loads(str(workout.laps_json))
    gps_track = json.loads(str(workout.gps_track_json)) if workout.gps_track_json else None
    hr_timeseries = (
        json.loads(str(workout.hr_timeseries_json)) if workout.hr_timeseries_json else None
    )
    _, hr_zones = _calculate_working_laps_metrics(
        laps_raw, resting_hr, max_hr, gps_track, hr_timeseries
    )
    return {"hr_zones_working": hr_zones}


@router.get("/{session_id}/comparison", response_model=ComparisonResponse)
async def get_session_comparison(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> ComparisonResponse:
    """Soll/Ist-Vergleich: matcht geplante Segmente mit tatsächlichen Laps."""
    query = select(WorkoutModel).where(WorkoutModel.id == session_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden.")

    if workout.planned_entry_id is None:
        raise HTTPException(status_code=404, detail="Session hat keine zugeordnete Planung.")

    # Load planned session
    ps_query = select(PlannedSessionModel).where(PlannedSessionModel.id == workout.planned_entry_id)
    ps_result = await db.execute(ps_query)
    planned_session = ps_result.scalar_one_or_none()

    if not planned_session or not planned_session.run_details_json:
        raise HTTPException(
            status_code=404, detail="Geplante Session oder Run-Details nicht gefunden."
        )

    # Parse planned segments
    run_details = _parse_run_details(str(planned_session.run_details_json))
    if not run_details or not run_details.segments:
        raise HTTPException(status_code=404, detail="Keine geplanten Segmente vorhanden.")

    # Parse actual laps → segments
    actual_segments = []
    if workout.laps_json:
        from app.models.session import LapResponse as LapResponseCls

        laps_raw = json.loads(str(workout.laps_json))
        laps = [LapResponseCls(**lap) for lap in laps_raw]
        actual_segments = laps_to_segments(laps)

    return build_comparison(
        planned_segments=run_details.segments,
        actual_segments=actual_segments,
        planned_entry_id=workout.planned_entry_id,
        planned_run_type=run_details.run_type,
    )


def _parse_run_details(raw: str | None) -> RunDetails | None:
    """Parse run_details_json string to RunDetails model."""
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return RunDetails(**data)
    except (json.JSONDecodeError, ValueError):
        return None


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
    workout.laps_json = json.dumps(laps_raw)
    await db.commit()
    await db.refresh(workout)

    # Build response with working-laps aggregation (use session's stored settings)
    resting_hr: Optional[int] = workout.athlete_resting_hr
    max_hr: Optional[int] = workout.athlete_max_hr
    if resting_hr is None or max_hr is None:
        resting_hr, max_hr = await _get_athlete_hr_settings(db)
    gps_track = json.loads(str(workout.gps_track_json)) if workout.gps_track_json else None
    hr_timeseries = (
        json.loads(str(workout.hr_timeseries_json)) if workout.hr_timeseries_json else None
    )
    laps = [LapResponse(**lap) for lap in laps_raw]
    summary_working, hr_zones_working = _calculate_working_laps_metrics(
        laps_raw, resting_hr, max_hr, gps_track, hr_timeseries
    )

    return LapOverrideResponse(
        success=True,
        laps=laps,
        summary_working=summary_working,
        hr_zones_working=hr_zones_working,
    )


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
            detail=f"Ungültiger Training Type. Erlaubt: {', '.join(sorted(VALID_TRAINING_TYPES))}",
        )

    query = select(WorkoutModel).where(WorkoutModel.id == session_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden.")

    workout.training_type_override = body.training_type
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

    workout.notes = body.notes
    await db.commit()
    await db.refresh(workout)

    return SessionResponse.from_db(workout)


@router.patch("/{session_id}/rpe", response_model=SessionResponse)
async def update_rpe(
    session_id: int,
    body: RpeUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Aktualisiert die RPE einer Session."""
    query = select(WorkoutModel).where(WorkoutModel.id == session_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden.")

    workout.rpe = body.rpe
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

    workout.date = datetime.combine(body.date, datetime.min.time())
    await db.commit()
    await db.refresh(workout)

    return SessionResponse.from_db(workout)


@router.patch("/{session_id}/planned-entry", response_model=SessionResponse)
async def update_planned_entry(
    session_id: int,
    body: PlannedEntryUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Aktualisiert die Zuordnung zu einer geplanten Session."""
    query = select(WorkoutModel).where(WorkoutModel.id == session_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden.")

    # Validate planned_entry_id exists if provided
    if body.planned_entry_id is not None:
        ps_query = select(PlannedSessionModel).where(
            PlannedSessionModel.id == body.planned_entry_id
        )
        ps_result = await db.execute(ps_query)
        if not ps_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Geplante Session nicht gefunden.")

    workout.planned_entry_id = body.planned_entry_id
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


@router.post("/{session_id}/analyze", response_model=SessionAnalysisResponse)
async def analyze_session(
    session_id: int,
    body: Optional[AnalyzeRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> SessionAnalysisResponse:
    """KI-gestützte Analyse einer Session (Cache-First)."""
    from app.services.session_analysis_service import (
        analyze_session as run_analysis,
    )

    force = body.force_refresh if body else False
    try:
        return await run_analysis(session_id, db, force_refresh=force)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI-Analyse fehlgeschlagen: {e}") from e


# --- KI-Empfehlungen (E06-S02) ---


@router.post("/{session_id}/recommendations", response_model=RecommendationsListResponse)
async def generate_recommendations(
    session_id: int,
    body: Optional[AnalyzeRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> RecommendationsListResponse:
    """Generiert KI-gestuetzte Trainingsempfehlungen basierend auf Session-Analyse."""
    from app.services.recommendation_service import (
        generate_recommendations as run_recommendations,
    )

    force = body.force_refresh if body else False
    try:
        return await run_recommendations(session_id, db, force_refresh=force)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=502, detail=f"Empfehlungsgenerierung fehlgeschlagen: {e}"
        ) from e


@router.get("/{session_id}/recommendations", response_model=RecommendationsListResponse)
async def get_session_recommendations(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> RecommendationsListResponse:
    """Laedt gespeicherte Empfehlungen fuer eine Session."""
    from app.services.recommendation_service import get_recommendations

    return await get_recommendations(session_id, db)


@router.patch("/recommendations/{recommendation_id}/status", response_model=RecommendationResponse)
async def update_recommendation_status(
    recommendation_id: int,
    body: RecommendationStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> RecommendationResponse:
    """Aktualisiert den Status einer Empfehlung (applied/dismissed)."""
    from app.services.recommendation_service import (
        update_recommendation_status as update_status,
    )

    try:
        return await update_status(recommendation_id, body.status, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.post("/{session_id}/recalculate-zones")
async def recalculate_session_zones(
    session_id: int,
    body: Optional[RecalculateZonesRequest] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Berechnet HR-Zonen einer einzelnen Session neu.

    Optionale HR-Werte im Body; ohne Body werden aktuelle Athleten-Einstellungen verwendet.
    """
    query = select(WorkoutModel).where(WorkoutModel.id == session_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden.")

    # Determine HR settings: body > current athlete settings
    resting_hr = body.resting_hr if body and body.resting_hr else None
    max_hr = body.max_hr if body and body.max_hr else None
    if resting_hr is None or max_hr is None:
        current_resting, current_max = await _get_athlete_hr_settings(db)
        resting_hr = resting_hr or current_resting
        max_hr = max_hr or current_max

    hr_values = _extract_hr_from_stored_data(workout)
    if not hr_values:
        raise HTTPException(status_code=400, detail="Keine HR-Daten vorhanden für Neuberechnung.")

    new_zones = calculate_zone_distribution(hr_values, resting_hr, max_hr)
    if not new_zones:
        raise HTTPException(status_code=400, detail="Zonen konnten nicht berechnet werden.")

    workout.hr_zones_json = json.dumps(new_zones)
    # Update athlete snapshot on session
    if resting_hr:
        workout.athlete_resting_hr = resting_hr
    if max_hr:
        workout.athlete_max_hr = max_hr

    await db.commit()
    return {
        "success": True,
        "hr_zones": new_zones,
        "athlete_resting_hr": resting_hr,
        "athlete_max_hr": max_hr,
    }


# --- Helper ---


def _extract_hr_from_stored_data(workout: WorkoutModel) -> list[int]:
    """Extract per-second HR values from stored session data.

    Priority: GPS track (per-second) > HR timeseries > CSV re-parse > empty.
    """
    # 1. GPS track points (best: per-second HR)
    if workout.gps_track_json:
        track = json.loads(str(workout.gps_track_json))
        points = track.get("points", [])
        hr_values = [int(p["hr"]) for p in points if p.get("hr") is not None]
        if hr_values:
            return hr_values

    # 2. Stored HR timeseries (FIT files without GPS)
    if workout.hr_timeseries_json:
        ts = json.loads(str(workout.hr_timeseries_json))
        if ts:
            hr_values = [int(p["hr_bpm"]) for p in ts if p.get("hr_bpm")]
            if hr_values:
                return hr_values

    # 3. CSV data (re-parse for HR timeseries)
    if workout.csv_data:
        try:
            result = csv_parser.parse(
                workout.csv_data.encode("utf-8"),
                TrainingType(str(workout.workout_type)),
                None,
            )
            if result.get("success"):
                ts = result.get("hr_timeseries", [])
                if ts:
                    return [int(p["hr_bpm"]) for p in ts if p.get("hr_bpm")]
        except Exception:
            pass

    return []


def _extract_hr_values_from_result(result: dict) -> list[int]:
    """Extrahiert HR-Werte aus dem Parse-Ergebnis fuer die Zonen-Berechnung.

    Prioritaet: GPS-Track (per-Sekunde) > HR-Timeseries (Kraft) > Lap-Durchschnitte.
    """
    # 1. GPS-Track (per-Sekunde HR — beste Qualitaet)
    gps_track = result.get("gps_track")
    if gps_track:
        points = gps_track.get("points", [])
        hr_values = [int(p["hr"]) for p in points if p.get("hr") is not None]
        if hr_values:
            return hr_values

    # 2. HR-Timeseries (Krafttraining)
    timeseries = result.get("hr_timeseries", [])
    if timeseries:
        return [int(p["hr_bpm"]) for p in timeseries if p.get("hr_bpm")]

    # 3. Fallback: Lap-Durchschnitte gewichtet nach Dauer (ungenau)
    laps = result.get("laps", [])
    hr_values = []
    for lap in laps:
        avg_hr = lap.get("avg_hr_bpm")
        duration = lap.get("duration_seconds", 0)
        if avg_hr and duration > 0:
            hr_values.extend([int(avg_hr)] * duration)
    return hr_values


EXCLUDED_TYPES = {"warmup", "cooldown", "pause"}


def _get_effective_type(lap: dict) -> str:
    """Gibt den effektiven Lap-Typ zurück (Override > Suggested)."""
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
    resting_hr: Optional[int] = None,
    max_hr: Optional[int] = None,
    gps_track: Optional[dict] = None,
    hr_timeseries: Optional[list[dict]] = None,
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

    # HR Zones: prefer per-second data over lap averages
    # Priority: GPS-Track > HR-Timeseries > Lap-Durchschnitte
    working_hr_values = _extract_working_hr_from_gps(laps_raw, gps_track)

    if not working_hr_values and hr_timeseries:
        working_hr_values = _extract_working_hr_from_timeseries(laps_raw, hr_timeseries)

    if not working_hr_values:
        # Fallback: expand lap averages (less accurate)
        working_hr_values = []
        for lap in working:
            avg_hr = lap.get("avg_hr_bpm", 0)
            dur = lap.get("duration_seconds", 0)
            if avg_hr and dur > 0:
                working_hr_values.extend([int(avg_hr)] * dur)

    hr_zones = calculate_zone_distribution(working_hr_values, resting_hr, max_hr)

    return summary, hr_zones


def _extract_working_hr_from_gps(
    laps_raw: list[dict],
    gps_track: Optional[dict],
) -> list[int]:
    """Extract per-second HR values from GPS track for working laps only.

    Computes time ranges for each lap, filters to working laps,
    then collects GPS HR values that fall within those time ranges.
    """
    if not gps_track or "points" not in gps_track:
        return []

    points = gps_track["points"]
    if not points or not any(p.get("hr") for p in points):
        return []

    # Build time ranges for working laps
    working_ranges: list[tuple[float, float]] = []
    elapsed = 0.0
    for lap in laps_raw:
        dur = lap.get("duration_seconds", 0)
        if dur <= 0:
            continue
        lap_start = elapsed
        lap_end = elapsed + dur
        elapsed = lap_end

        if _get_effective_type(lap) not in EXCLUDED_TYPES:
            working_ranges.append((lap_start, lap_end))

    if not working_ranges:
        return []

    # Collect GPS HR values within working time ranges
    hr_values: list[int] = []
    range_idx = 0
    for p in points:
        sec = p.get("seconds", 0)
        hr = p.get("hr")
        if hr is None:
            continue

        # Advance range index if past current range
        while range_idx < len(working_ranges) and sec >= working_ranges[range_idx][1]:
            range_idx += 1

        if range_idx >= len(working_ranges):
            break

        if working_ranges[range_idx][0] <= sec < working_ranges[range_idx][1]:
            hr_values.append(int(hr))

    return hr_values


def _extract_working_hr_from_timeseries(
    laps_raw: list[dict],
    hr_timeseries: list[dict],
) -> list[int]:
    """Extract per-second HR values from HR timeseries for working laps only.

    Uses the same time-range filtering as GPS track extraction.
    HR timeseries entries have 'seconds' and 'hr_bpm' fields.
    """
    if not hr_timeseries:
        return []

    # Build time ranges for working laps
    working_ranges: list[tuple[float, float]] = []
    elapsed = 0.0
    for lap in laps_raw:
        dur = lap.get("duration_seconds", 0)
        if dur <= 0:
            continue
        lap_start = elapsed
        lap_end = elapsed + dur
        elapsed = lap_end

        if _get_effective_type(lap) not in EXCLUDED_TYPES:
            working_ranges.append((lap_start, lap_end))

    if not working_ranges:
        return []

    # Collect HR values within working time ranges
    hr_values: list[int] = []
    range_idx = 0
    for entry in hr_timeseries:
        sec = entry.get("seconds", 0)
        hr = entry.get("hr_bpm")
        if hr is None:
            continue

        while range_idx < len(working_ranges) and sec >= working_ranges[range_idx][1]:
            range_idx += 1

        if range_idx >= len(working_ranges):
            break

        if working_ranges[range_idx][0] <= sec < working_ranges[range_idx][1]:
            hr_values.append(int(hr))

    return hr_values


# --- Reparse (#349) ---


@router.post("/{session_id}/reparse")
async def reparse_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Parst eine Session neu aus der gespeicherten Originaldatei.

    Aktualisiert Laps, HR-Daten, HR-Zonen, GPS. Behaelt User-Overrides
    (Segment-Types, Training-Type-Override, Notes, RPE, geplanter Eintrag).
    """
    query = select(WorkoutModel).where(WorkoutModel.id == session_id)
    result = await db.execute(query)
    workout = result.scalar_one_or_none()
    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden.")

    if not workout.original_file_content or not workout.original_file_format:
        raise HTTPException(
            status_code=409,
            detail="Keine Originaldatei gespeichert. Session muss manuell neu hochgeladen werden.",
        )

    return await _reparse_workout(workout, db)


@router.post("/reparse-all")
async def reparse_all_sessions(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Parst alle Sessions mit gespeicherter Originaldatei neu.

    Nuetzlich nach Parser-Fixes um alle bestehenden Sessions zu aktualisieren.
    """
    query = select(WorkoutModel).where(
        WorkoutModel.original_file_content.isnot(None),
        WorkoutModel.original_file_format.isnot(None),
    )
    result = await db.execute(query)
    workouts = result.scalars().all()

    results: list[dict] = []
    for workout in workouts:
        try:
            reparse_result = await _reparse_workout(workout, db, commit=False)
            results.append(
                {
                    "session_id": workout.id,
                    "success": True,
                    "changes": reparse_result.get("changes"),
                }
            )
        except HTTPException as e:
            results.append({"session_id": workout.id, "success": False, "error": e.detail})
        except Exception as e:
            results.append({"session_id": workout.id, "success": False, "error": str(e)})

    await db.commit()

    succeeded = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"])

    return {
        "total": len(results),
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }


def _apply_parsed_data_to_workout(
    workout: WorkoutModel,
    parsed: dict,
    new_laps: list[dict] | None,
    file_format: str,
    file_content: bytes,
) -> None:
    """Aktualisiert Workout-Felder aus Parse-Ergebnis (ohne User-Einstellungen)."""
    summary = parsed["summary"]
    workout.duration_sec = summary.get("total_duration_seconds")
    workout.distance_km = summary.get("total_distance_km")
    workout.pace = summary.get("avg_pace_formatted")
    workout.hr_avg = summary.get("avg_hr_bpm")
    workout.hr_max = summary.get("max_hr_bpm")
    workout.hr_min = summary.get("min_hr_bpm")
    workout.cadence_avg = summary.get("avg_cadence_spm")
    workout.laps_json = json.dumps(new_laps) if new_laps else None
    workout.hr_zones_json = json.dumps(parsed["hr_zones"]) if parsed["hr_zones"] else None

    hr_timeseries = parsed.get("hr_timeseries")
    if hr_timeseries:
        workout.hr_timeseries_json = json.dumps(hr_timeseries)

    gps_track = parsed.get("gps_track")
    if gps_track:
        workout.gps_track_json = json.dumps(gps_track)
        workout.has_gps = True

    if file_format == "csv":
        workout.csv_data = file_content.decode("utf-8")

    classification = parsed["classification"]
    if classification:
        workout.training_type_auto = classification.training_type
        workout.training_type_confidence = classification.confidence

    workout.athlete_resting_hr = parsed["resting_hr"]
    workout.athlete_max_hr = parsed["max_hr"]


async def _reparse_workout(
    workout: WorkoutModel,
    db: AsyncSession,
    commit: bool = True,
) -> dict:
    """Interne Reparse-Logik fuer ein einzelnes Workout."""
    if not workout.original_file_content or not workout.original_file_format:
        raise HTTPException(status_code=409, detail="Keine Originaldatei gespeichert.")

    file_content: bytes = workout.original_file_content
    file_format = workout.original_file_format.lower()
    if file_format == "fit":
        parser: TrainingCSVParser | TrainingFITParser = fit_parser
    elif file_format == "csv":
        parser = csv_parser
    else:
        raise HTTPException(status_code=400, detail=f"Unbekanntes Dateiformat: {file_format}")

    # User-Overrides vor Reparse sichern
    old_laps = json.loads(workout.laps_json) if workout.laps_json else []
    lap_overrides: dict[str, str] = {}
    for lap in old_laps:
        if lap.get("user_override"):
            lap_overrides[str(lap["lap_number"])] = lap["user_override"]

    # Neu parsen
    training_type = TrainingType(workout.workout_type)
    subtype_str = workout.subtype
    training_subtype = TrainingSubType(subtype_str) if subtype_str else None

    parsed = await _parse_and_classify(
        file_content,
        training_type,
        training_subtype,
        db,
        parser=parser,
    )
    if not parsed["success"]:
        raise HTTPException(status_code=500, detail=f"Reparse fehlgeschlagen: {parsed['errors']}")

    # User-Overrides wieder anwenden
    new_laps = parsed["laps"]
    if new_laps and lap_overrides:
        _apply_lap_overrides(new_laps, json.dumps(lap_overrides))

    # Workout-Felder aktualisieren
    _apply_parsed_data_to_workout(workout, parsed, new_laps, file_format, file_content)

    if commit:
        await db.commit()

    return {
        "success": True,
        "session_id": workout.id,
        "message": f"Session {workout.id} erfolgreich neu geparst.",
        "changes": {
            "hr_avg": workout.hr_avg,
            "hr_max": workout.hr_max,
            "hr_min": workout.hr_min,
            "laps_count": len(new_laps) if new_laps else 0,
            "has_hr_zones": bool(parsed["hr_zones"]),
            "has_gps": workout.has_gps,
            "lap_overrides_restored": len(lap_overrides),
        },
    }
