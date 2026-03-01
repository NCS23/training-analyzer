"""API routes for Session Templates (renamed from Training Plans)."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import SessionTemplateModel, WorkoutModel
from app.infrastructure.database.session import get_db
from app.models.session_template import (
    SessionTemplateCreate,
    SessionTemplateListResponse,
    SessionTemplateResponse,
    SessionTemplateSummary,
    SessionTemplateUpdate,
    TemplateExercise,
)
from app.models.weekly_plan import RunDetails

router = APIRouter(prefix="/session-templates")


def _parse_run_details(raw: Optional[str]) -> Optional[RunDetails]:
    """Parse run_details_json string to RunDetails model."""
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return RunDetails(**data)
    except (json.JSONDecodeError, ValueError):
        return None


def _model_to_response(tmpl: SessionTemplateModel) -> SessionTemplateResponse:
    exercises: list[TemplateExercise] = []
    if tmpl.exercises_json:
        raw = json.loads(str(tmpl.exercises_json))
        exercises = [TemplateExercise(**ex) for ex in raw]

    run_details = _parse_run_details(str(tmpl.run_details_json) if tmpl.run_details_json else None)

    return SessionTemplateResponse(
        id=int(tmpl.id),  # type: ignore[arg-type]
        name=str(tmpl.name),
        description=str(tmpl.description) if tmpl.description else None,
        session_type=str(tmpl.session_type),
        exercises=exercises,
        run_details=run_details,
        is_template=bool(tmpl.is_template),
        created_at=tmpl.created_at,  # type: ignore[arg-type]
        updated_at=tmpl.updated_at,  # type: ignore[arg-type]
    )


def _model_to_summary(tmpl: SessionTemplateModel) -> SessionTemplateSummary:
    exercises = []
    if tmpl.exercises_json:
        exercises = json.loads(str(tmpl.exercises_json))

    run_type: Optional[str] = None
    if tmpl.run_details_json:
        run_details = _parse_run_details(str(tmpl.run_details_json))
        if run_details:
            run_type = run_details.run_type

    return SessionTemplateSummary(
        id=int(tmpl.id),  # type: ignore[arg-type]
        name=str(tmpl.name),
        session_type=str(tmpl.session_type),
        exercise_count=len(exercises),
        total_sets=sum(ex.get("sets", 0) for ex in exercises),
        run_type=run_type,
        created_at=tmpl.created_at,  # type: ignore[arg-type]
        updated_at=tmpl.updated_at,  # type: ignore[arg-type]
    )


@router.get("", response_model=SessionTemplateListResponse)
async def list_templates(
    session_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> SessionTemplateListResponse:
    """List all session templates."""
    query = select(SessionTemplateModel).order_by(SessionTemplateModel.updated_at.desc())
    if session_type:
        query = query.where(SessionTemplateModel.session_type == session_type)

    result = await db.execute(query)
    templates = list(result.scalars().all())

    count_query = select(func.count(SessionTemplateModel.id))
    if session_type:
        count_query = count_query.where(SessionTemplateModel.session_type == session_type)
    total = (await db.execute(count_query)).scalar() or 0

    return SessionTemplateListResponse(
        templates=[_model_to_summary(t) for t in templates],
        total=total,
    )


@router.get("/{template_id}", response_model=SessionTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
) -> SessionTemplateResponse:
    """Get a session template with exercises."""
    result = await db.execute(
        select(SessionTemplateModel).where(SessionTemplateModel.id == template_id)
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template nicht gefunden")
    return _model_to_response(tmpl)


@router.post("", response_model=SessionTemplateResponse, status_code=201)
async def create_template(
    data: SessionTemplateCreate,
    db: AsyncSession = Depends(get_db),
) -> SessionTemplateResponse:
    """Create a new session template."""
    if data.session_type == "strength" and not data.exercises:
        raise HTTPException(
            status_code=422,
            detail="Krafttraining-Template braucht mindestens eine Uebung.",
        )
    if data.session_type == "running" and not data.run_details:
        raise HTTPException(
            status_code=422,
            detail="Lauf-Template braucht Run-Details.",
        )

    exercises_data: Optional[str] = None
    if data.exercises:
        exercises_data = json.dumps([ex.model_dump() for ex in data.exercises])

    run_details_data: Optional[str] = None
    if data.run_details:
        run_details_data = json.dumps(data.run_details.model_dump())

    tmpl = SessionTemplateModel(
        name=data.name,
        description=data.description,
        session_type=data.session_type,
        exercises_json=exercises_data,
        run_details_json=run_details_data,
        is_template=True,
    )
    db.add(tmpl)
    await db.commit()
    await db.refresh(tmpl)
    return _model_to_response(tmpl)


@router.patch("/{template_id}", response_model=SessionTemplateResponse)
async def update_template(
    template_id: int,
    data: SessionTemplateUpdate,
    db: AsyncSession = Depends(get_db),
) -> SessionTemplateResponse:
    """Update a session template."""
    result = await db.execute(
        select(SessionTemplateModel).where(SessionTemplateModel.id == template_id)
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template nicht gefunden")

    if data.name is not None:
        tmpl.name = data.name  # type: ignore[assignment]
    if data.description is not None:
        tmpl.description = data.description  # type: ignore[assignment]
    if data.exercises is not None:
        tmpl.exercises_json = json.dumps([ex.model_dump() for ex in data.exercises])  # type: ignore[assignment]
    if data.run_details is not None:
        tmpl.run_details_json = json.dumps(data.run_details.model_dump())  # type: ignore[assignment]

    await db.commit()
    await db.refresh(tmpl)
    return _model_to_response(tmpl)


@router.delete("/{template_id}", status_code=204)
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a session template."""
    result = await db.execute(
        select(SessionTemplateModel).where(SessionTemplateModel.id == template_id)
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template nicht gefunden")

    await db.delete(tmpl)
    await db.commit()


@router.post("/{template_id}/duplicate", response_model=SessionTemplateResponse, status_code=201)
async def duplicate_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
) -> SessionTemplateResponse:
    """Duplicate a session template."""
    result = await db.execute(
        select(SessionTemplateModel).where(SessionTemplateModel.id == template_id)
    )
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template nicht gefunden")

    new_tmpl = SessionTemplateModel(
        name=f"{tmpl.name} (Kopie)",
        description=tmpl.description,
        session_type=tmpl.session_type,
        exercises_json=tmpl.exercises_json,
        run_details_json=tmpl.run_details_json,
        is_template=True,
    )
    db.add(new_tmpl)
    await db.commit()
    await db.refresh(new_tmpl)
    return _model_to_response(new_tmpl)


def _classify_run_type(
    distance_km: Optional[float],
    training_type: Optional[str],
) -> str:
    """Classify a running session into a run_type for templates."""
    if training_type:
        type_map = {
            "recovery": "recovery",
            "easy": "easy",
            "long_run": "long_run",
            "tempo": "tempo",
            "intervals": "intervals",
            "threshold": "tempo",
        }
        if training_type in type_map:
            return type_map[training_type]

    if distance_km and distance_km >= 15:
        return "long_run"
    return "easy"


@router.post(
    "/from-session/{session_id}",
    response_model=SessionTemplateResponse,
    status_code=201,
)
async def create_from_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> SessionTemplateResponse:
    """Create a template from an existing session."""
    result = await db.execute(select(WorkoutModel).where(WorkoutModel.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")

    workout_type = str(session.workout_type)

    if workout_type == "strength":
        exercises_data: Optional[str] = None
        if session.exercises_json:
            raw_exercises = json.loads(str(session.exercises_json))
            template_exercises = []
            for ex in raw_exercises:
                sets = ex.get("sets", [])
                template_exercises.append(
                    {
                        "name": ex.get("name", "Unbekannt"),
                        "category": ex.get("category", "legs"),
                        "sets": len(sets)
                        if isinstance(sets, list)
                        else int(ex.get("sets_count", 1)),
                        "reps": int(sets[0].get("reps", 10))
                        if isinstance(sets, list) and sets
                        else 10,
                        "weight_kg": float(sets[0].get("weight_kg", 0))
                        if isinstance(sets, list) and sets
                        else None,
                        "exercise_type": ex.get("exercise_type", "kraft"),
                        "notes": ex.get("notes"),
                    }
                )
            exercises_data = json.dumps(template_exercises)

        tmpl = SessionTemplateModel(
            name=f"Template aus Session #{session_id}",
            session_type="strength",
            exercises_json=exercises_data,
            is_template=True,
        )
    else:
        training_type = str(session.training_type_override or session.training_type_auto or "")
        run_type = _classify_run_type(
            float(session.distance_km) if session.distance_km else None,
            training_type if training_type else None,
        )
        duration_min: Optional[int] = None
        if session.duration_sec:
            duration_min = round(int(session.duration_sec) / 60)

        run_details = {
            "run_type": run_type,
            "target_duration_minutes": duration_min,
            "target_pace_min": str(session.pace) if session.pace else None,
            "target_pace_max": None,
            "target_hr_min": None,
            "target_hr_max": None,
            "intervals": None,
        }

        tmpl = SessionTemplateModel(
            name=f"Template aus Session #{session_id}",
            session_type="running",
            run_details_json=json.dumps(run_details),
            is_template=True,
        )

    db.add(tmpl)
    await db.commit()
    await db.refresh(tmpl)
    return _model_to_response(tmpl)
