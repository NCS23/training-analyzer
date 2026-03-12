"""Strength Training API Endpoints."""

import json
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import TypeAdapter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import WorkoutModel
from app.infrastructure.database.session import get_db
from app.models.strength import (
    ExerciseInput,
    LastExerciseSets,
    SetResponse,
)
from app.services.csv_parser import TrainingCSVParser
from app.services.fit_parser import TrainingFITParser
from app.services.hr_zone_calculator import calculate_zone_distribution
from app.services.tonnage_calculator import calculate_strength_metrics

router = APIRouter(prefix="/sessions/strength", tags=["strength"])

csv_parser = TrainingCSVParser()
fit_parser = TrainingFITParser()

ExerciseListAdapter = TypeAdapter(list[ExerciseInput])


async def _get_athlete_hr_settings(db: AsyncSession) -> tuple[Optional[int], Optional[int]]:
    """Holt Ruhe-HR und Max-HR des Athleten (wenn konfiguriert)."""
    from app.infrastructure.database.models import AthleteModel

    result = await db.execute(select(AthleteModel).limit(1))
    athlete = result.scalar_one_or_none()
    if athlete and athlete.resting_hr and athlete.max_hr:
        return athlete.resting_hr, athlete.max_hr
    return None, None


def _parse_training_file(content: bytes, filename: str) -> Optional[dict]:
    """Parst eine Trainingsdatei (CSV oder FIT) und gibt das Ergebnis zurück."""
    from app.models.training import TrainingType

    lower = filename.lower()
    if lower.endswith(".fit"):
        result = fit_parser.parse(content, TrainingType.STRENGTH)
    elif lower.endswith(".csv"):
        result = csv_parser.parse(content, TrainingType.STRENGTH)
    else:
        return None

    if not result.get("success"):
        return None
    return result


@router.post("", status_code=201)
async def create_strength_session(
    exercises_json: str = Form(..., description="JSON-Array der Übungen"),
    training_date: date = Form(..., description="Datum (YYYY-MM-DD)"),
    duration_minutes: int = Form(..., ge=1, le=600, description="Dauer in Minuten"),
    notes: Optional[str] = Form(None, description="Notizen"),
    rpe: Optional[int] = Form(None, ge=1, le=10, description="RPE"),
    training_file: Optional[UploadFile] = File(None, description="Optional: CSV/FIT Datei"),
    planned_entry_id: Optional[int] = Form(
        None, description="Manuelle Zuordnung zu geplanter Session"
    ),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Erstellt eine neue Krafttraining-Session.

    Exercises werden als JSON-String im Form-Feld gesendet.
    Optional kann eine CSV/FIT Datei mitgeschickt werden,
    aus der HR-Daten und Dauer extrahiert werden.
    """
    # Parse exercises JSON
    from pydantic import ValidationError

    try:
        exercises = ExerciseListAdapter.validate_json(exercises_json)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    if len(exercises) == 0:
        raise HTTPException(status_code=422, detail="Mindestens eine Übung erforderlich.")

    exercises_data = [
        {
            "name": ex.name,
            "category": ex.category.value,
            "sets": [
                {"reps": s.reps, "weight_kg": s.weight_kg, "status": s.status.value}
                for s in ex.sets
            ],
        }
        for ex in exercises
    ]

    metrics = calculate_strength_metrics(exercises_data)

    # Notes (RPE is stored as a dedicated column now)
    combined_notes = notes if notes else None

    # Parse optional training file for HR data
    file_summary: Optional[dict] = None
    file_hr_zones: Optional[dict] = None
    file_hr_timeseries: Optional[list] = None
    file_duration_sec: Optional[int] = None
    resting_hr: Optional[int] = None
    max_hr: Optional[int] = None

    if training_file and training_file.filename:
        file_content = await training_file.read()
        if len(file_content) > 0:
            parsed = _parse_training_file(file_content, training_file.filename)
            if parsed:
                file_summary = parsed.get("summary", {})
                file_hr_timeseries = parsed.get("hr_timeseries")

                # Duration from file (more accurate than manual)
                if file_summary and file_summary.get("total_duration_seconds"):
                    file_duration_sec = file_summary["total_duration_seconds"]

                # HR zones from raw data
                hr_values: list[int] = []
                if file_hr_timeseries:
                    hr_values = [int(p["hr_bpm"]) for p in file_hr_timeseries if p.get("hr_bpm")]
                resting_hr, max_hr = await _get_athlete_hr_settings(db)
                if hr_values:
                    file_hr_zones = calculate_zone_distribution(hr_values, resting_hr, max_hr)

    # Use file duration if available, otherwise manual
    effective_duration_sec = file_duration_sec or (duration_minutes * 60)

    workout = WorkoutModel(
        date=datetime.combine(training_date, datetime.min.time()),
        workout_type="strength",
        duration_sec=effective_duration_sec,
        exercises_json=json.dumps(exercises_data),
        hr_avg=file_summary.get("avg_hr_bpm") if file_summary else None,
        hr_max=file_summary.get("max_hr_bpm") if file_summary else None,
        hr_min=file_summary.get("min_hr_bpm") if file_summary else None,
        hr_zones_json=json.dumps(file_hr_zones) if file_hr_zones else None,
        athlete_resting_hr=resting_hr,
        athlete_max_hr=max_hr,
        notes=combined_notes,
        rpe=rpe,
        planned_entry_id=planned_entry_id,
    )

    db.add(workout)

    # Sync exercises to library (auto-register + increment usage)
    from app.services.exercise_sync import sync_exercises_from_session

    await sync_exercises_from_session(
        db,
        exercises_data,
        session_date=datetime.combine(training_date, datetime.min.time()),
    )

    await db.commit()
    await db.refresh(workout)

    return {
        "success": True,
        "session_id": workout.id,
        "metrics": metrics,
        "file_data": {
            "has_file": file_summary is not None,
            "hr_avg": file_summary.get("avg_hr_bpm") if file_summary else None,
            "hr_max": file_summary.get("max_hr_bpm") if file_summary else None,
            "duration_sec": file_duration_sec,
        },
    }


@router.patch("/{session_id}/exercises")
async def update_strength_exercises(
    session_id: int,
    exercises_json: str = Form(..., description="JSON-Array der Übungen"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Aktualisiert die Übungen einer bestehenden Krafttraining-Session."""
    from pydantic import ValidationError

    # Session laden
    result = await db.execute(select(WorkoutModel).where(WorkoutModel.id == session_id))
    workout = result.scalar_one_or_none()
    if not workout:
        raise HTTPException(status_code=404, detail="Session nicht gefunden.")
    if workout.workout_type != "strength":
        raise HTTPException(status_code=400, detail="Nur Kraftsessions können bearbeitet werden.")

    # Exercises validieren
    try:
        exercises = ExerciseListAdapter.validate_json(exercises_json)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    if len(exercises) == 0:
        raise HTTPException(status_code=422, detail="Mindestens eine Übung erforderlich.")

    exercises_data = [
        {
            "name": ex.name,
            "category": ex.category.value,
            "sets": [
                {"reps": s.reps, "weight_kg": s.weight_kg, "status": s.status.value}
                for s in ex.sets
            ],
        }
        for ex in exercises
    ]

    # Update exercises + recalculate metrics
    workout.exercises_json = json.dumps(exercises_data)
    metrics = calculate_strength_metrics(exercises_data)

    # Sync exercises to library
    from app.services.exercise_sync import sync_exercises_from_session

    model_date = workout.date
    if isinstance(model_date, datetime):
        session_date = model_date
    else:
        session_date = datetime.combine(date.today(), datetime.min.time())
    await sync_exercises_from_session(db, exercises_data, session_date=session_date)

    await db.commit()

    return {
        "success": True,
        "session_id": session_id,
        "exercises": exercises_data,
        "metrics": metrics,
    }


@router.get("/last-complete")
async def get_last_complete_session(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Gibt die letzte vollstaendige Strength-Session zurueck (fuer Clone + Tonnage-Delta)."""
    query = (
        select(WorkoutModel)
        .where(WorkoutModel.workout_type == "strength")
        .where(WorkoutModel.exercises_json.isnot(None))
        .order_by(WorkoutModel.date.desc())
        .limit(1)
    )
    result = await db.execute(query)
    workout = result.scalar_one_or_none()

    if not workout or not workout.exercises_json:
        return {"found": False, "session": None}

    exercises_raw = json.loads(str(workout.exercises_json))
    metrics = calculate_strength_metrics(exercises_raw)
    model_date = workout.date
    session_date = model_date.date() if isinstance(model_date, datetime) else model_date

    return {
        "found": True,
        "session": {
            "id": workout.id,
            "date": session_date.isoformat(),
            "exercises": exercises_raw,
            "total_tonnage_kg": metrics["total_tonnage_kg"],
            "duration_minutes": ((workout.duration_sec // 60) if workout.duration_sec else None),
        },
    }


@router.get("/last-exercises")
async def get_last_exercises(
    exercise_name: str = Query(..., min_length=1, description="Name der Übung"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Gibt die letzten Sätze einer Übung zurück (Quick-Add)."""
    query = (
        select(WorkoutModel)
        .where(WorkoutModel.workout_type == "strength")
        .where(WorkoutModel.exercises_json.isnot(None))
        .order_by(WorkoutModel.date.desc())
        .limit(20)
    )
    result = await db.execute(query)
    workouts = result.scalars().all()

    for workout in workouts:
        if not workout.exercises_json:
            continue
        exercises_raw = json.loads(str(workout.exercises_json))
        for ex in exercises_raw:
            if ex["name"].lower() == exercise_name.lower():
                model_date = workout.date
                session_date = model_date.date() if isinstance(model_date, datetime) else model_date
                return {
                    "found": True,
                    "exercise": LastExerciseSets(
                        exercise_name=ex["name"],
                        category=ex["category"],
                        sets=[
                            SetResponse(
                                reps=s["reps"],
                                weight_kg=s["weight_kg"],
                                status=s["status"],
                            )
                            for s in ex["sets"]
                        ],
                        session_date=session_date,
                    ),
                }

    return {"found": False, "exercise": None}


# --- Progression Tracking (Issue #17) ---


async def _load_strength_sessions(db: AsyncSession) -> list[dict]:
    """Laedt alle Strength-Sessions mit geparsten Exercises."""
    query = (
        select(WorkoutModel)
        .where(WorkoutModel.workout_type == "strength")
        .where(WorkoutModel.exercises_json.isnot(None))
        .order_by(WorkoutModel.date.asc())
    )
    result = await db.execute(query)
    workouts = result.scalars().all()

    sessions = []
    for w in workouts:
        if not w.exercises_json:
            continue
        model_date = w.date
        date_str = (
            model_date.date().isoformat() if isinstance(model_date, datetime) else str(model_date)
        )
        sessions.append(
            {
                "id": w.id,
                "date": date_str,
                "exercises": json.loads(str(w.exercises_json)),
            }
        )

    return sessions


@router.get("/exercises")
async def list_exercises(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Liste aller verwendeten Übungen mit Metadaten."""
    from app.services.progression_tracker import get_all_exercise_names

    sessions = await _load_strength_sessions(db)
    exercises = get_all_exercise_names(sessions)
    return {"exercises": exercises}


@router.get("/progression")
async def get_exercise_progression(
    exercise_name: str = Query(..., min_length=1, description="Name der Übung"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Gewichtsverlauf einer Übung über die Zeit."""
    from app.services.progression_tracker import get_exercise_history

    sessions = await _load_strength_sessions(db)
    history = get_exercise_history(exercise_name, sessions)

    if not history:
        return {
            "exercise_name": exercise_name,
            "data_points": [],
            "current_max_weight": 0,
            "previous_max_weight": None,
            "weight_progression": None,
        }

    current_max = history[-1]["max_weight_kg"]
    previous_max = history[-2]["max_weight_kg"] if len(history) >= 2 else None
    progression = round(current_max - previous_max, 1) if previous_max is not None else None

    return {
        "exercise_name": exercise_name,
        "data_points": history,
        "current_max_weight": current_max,
        "previous_max_weight": previous_max,
        "weight_progression": progression,
    }


@router.get("/prs")
async def get_personal_records(
    session_id: Optional[int] = Query(None, description="Nur PRs dieser Session"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Persönliche Bestleistungen (PRs) pro Übung."""
    from app.services.progression_tracker import detect_personal_records

    sessions = await _load_strength_sessions(db)
    all_prs = detect_personal_records(sessions)

    if session_id is not None:
        session_prs = [pr for pr in all_prs if pr["session_id"] == session_id]
        return {"records": all_prs, "new_prs_session": session_prs}

    return {"records": all_prs, "new_prs_session": None}


@router.get("/tonnage-trend")
async def get_tonnage_trend(
    days: int = Query(default=90, ge=7, le=365, description="Zeitraum in Tagen"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Woechentlicher Tonnage-Trend fuer Krafttraining."""
    from app.services.progression_tracker import calculate_weekly_tonnage

    # Filter by date
    cutoff = datetime.utcnow() - timedelta(days=days)
    query = (
        select(WorkoutModel)
        .where(WorkoutModel.workout_type == "strength")
        .where(WorkoutModel.exercises_json.isnot(None))
        .where(WorkoutModel.date >= cutoff)
        .order_by(WorkoutModel.date.asc())
    )
    result = await db.execute(query)
    workouts = result.scalars().all()

    sessions = []
    for w in workouts:
        if not w.exercises_json:
            continue
        model_date = w.date
        date_str = (
            model_date.date().isoformat() if isinstance(model_date, datetime) else str(model_date)
        )
        sessions.append(
            {
                "id": w.id,
                "date": date_str,
                "exercises": json.loads(str(w.exercises_json)),
            }
        )

    weeks = calculate_weekly_tonnage(sessions)
    total = sum(w["total_tonnage_kg"] for w in weeks)
    avg = round(total / len(weeks), 1) if weeks else 0.0

    # Trend direction
    trend_direction = None
    if len(weeks) >= 2:
        first_half = sum(w["total_tonnage_kg"] for w in weeks[: len(weeks) // 2])
        second_half = sum(w["total_tonnage_kg"] for w in weeks[len(weeks) // 2 :])
        if second_half > first_half * 1.1:
            trend_direction = "up"
        elif second_half < first_half * 0.9:
            trend_direction = "down"
        else:
            trend_direction = "stable"

    return {
        "weeks": weeks,
        "total_tonnage_kg": round(total, 1),
        "avg_weekly_tonnage_kg": avg,
        "trend_direction": trend_direction,
    }
