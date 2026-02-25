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
    SessionListResponse,
    SessionResponse,
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
