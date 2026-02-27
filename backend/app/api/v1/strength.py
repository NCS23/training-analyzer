"""Strength Training API Endpoints."""

import json
from datetime import date, datetime
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
        return int(athlete.resting_hr), int(athlete.max_hr)  # type: ignore[arg-type]
    return None, None


def _parse_training_file(content: bytes, filename: str) -> Optional[dict]:
    """Parst eine Trainingsdatei (CSV oder FIT) und gibt das Ergebnis zurueck."""
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
    exercises_json: str = Form(..., description="JSON-Array der Uebungen"),
    training_date: date = Form(..., description="Datum (YYYY-MM-DD)"),
    duration_minutes: int = Form(..., ge=1, le=600, description="Dauer in Minuten"),
    notes: Optional[str] = Form(None, description="Notizen"),
    rpe: Optional[int] = Form(None, ge=1, le=10, description="RPE"),
    training_file: Optional[UploadFile] = File(None, description="Optional: CSV/FIT Datei"),
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
        raise HTTPException(status_code=422, detail="Mindestens eine Uebung erforderlich.")

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

    # Store RPE in notes if provided (alongside user notes)
    notes_parts = []
    if rpe is not None:
        notes_parts.append(f"RPE: {rpe}/10")
    if notes:
        notes_parts.append(notes)
    combined_notes = "\n".join(notes_parts) if notes_parts else None

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
                    hr_values = [
                        int(p["hr_bpm"]) for p in file_hr_timeseries if p.get("hr_bpm")
                    ]
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
    )

    db.add(workout)
    await db.commit()
    await db.refresh(workout)

    return {
        "success": True,
        "session_id": int(workout.id),  # type: ignore[arg-type]
        "metrics": metrics,
        "file_data": {
            "has_file": file_summary is not None,
            "hr_avg": file_summary.get("avg_hr_bpm") if file_summary else None,
            "hr_max": file_summary.get("max_hr_bpm") if file_summary else None,
            "duration_sec": file_duration_sec,
        },
    }


@router.get("/last-exercises")
async def get_last_exercises(
    exercise_name: str = Query(..., min_length=1, description="Name der Uebung"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Gibt die letzten Saetze einer Uebung zurueck (Quick-Add)."""
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
                        session_date=session_date,  # type: ignore[arg-type]
                    ),
                }

    return {"found": False, "exercise": None}
