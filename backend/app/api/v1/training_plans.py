"""API routes for Training Plans (Issue #14, #29)."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import TrainingPlanModel, WorkoutModel
from app.infrastructure.database.session import get_db
from app.models.training_plan import (
    PlanExercise,
    TrainingPlanCreate,
    TrainingPlanListResponse,
    TrainingPlanResponse,
    TrainingPlanSummary,
    TrainingPlanUpdate,
)
from app.models.weekly_plan import RunDetails

router = APIRouter(prefix="/plans")


def _parse_run_details(raw: Optional[str]) -> Optional[RunDetails]:
    """Parse run_details_json string to RunDetails model."""
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return RunDetails(**data)
    except (json.JSONDecodeError, ValueError):
        return None


def _model_to_response(plan: TrainingPlanModel) -> TrainingPlanResponse:
    exercises: list[PlanExercise] = []
    if plan.exercises_json:
        raw = json.loads(str(plan.exercises_json))
        exercises = [PlanExercise(**ex) for ex in raw]

    run_details = _parse_run_details(
        str(plan.run_details_json) if plan.run_details_json else None
    )

    return TrainingPlanResponse(
        id=int(plan.id),  # type: ignore[arg-type]
        name=str(plan.name),
        description=str(plan.description) if plan.description else None,
        session_type=str(plan.session_type),
        exercises=exercises,
        run_details=run_details,
        is_template=bool(plan.is_template),
        created_at=plan.created_at,  # type: ignore[arg-type]
        updated_at=plan.updated_at,  # type: ignore[arg-type]
    )


def _model_to_summary(plan: TrainingPlanModel) -> TrainingPlanSummary:
    exercises = []
    if plan.exercises_json:
        exercises = json.loads(str(plan.exercises_json))

    run_type: Optional[str] = None
    if plan.run_details_json:
        run_details = _parse_run_details(str(plan.run_details_json))
        if run_details:
            run_type = run_details.run_type

    return TrainingPlanSummary(
        id=int(plan.id),  # type: ignore[arg-type]
        name=str(plan.name),
        session_type=str(plan.session_type),
        exercise_count=len(exercises),
        total_sets=sum(ex.get("sets", 0) for ex in exercises),
        run_type=run_type,
        created_at=plan.created_at,  # type: ignore[arg-type]
        updated_at=plan.updated_at,  # type: ignore[arg-type]
    )


@router.get("", response_model=TrainingPlanListResponse)
async def list_plans(
    session_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanListResponse:
    """List all training plans."""
    query = select(TrainingPlanModel).order_by(TrainingPlanModel.updated_at.desc())
    if session_type:
        query = query.where(TrainingPlanModel.session_type == session_type)

    result = await db.execute(query)
    plans = list(result.scalars().all())

    count_query = select(func.count(TrainingPlanModel.id))
    if session_type:
        count_query = count_query.where(TrainingPlanModel.session_type == session_type)
    total = (await db.execute(count_query)).scalar() or 0

    return TrainingPlanListResponse(
        plans=[_model_to_summary(p) for p in plans],
        total=total,
    )


@router.get("/{plan_id}", response_model=TrainingPlanResponse)
async def get_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanResponse:
    """Get a training plan with exercises."""
    result = await db.execute(
        select(TrainingPlanModel).where(TrainingPlanModel.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan nicht gefunden")
    return _model_to_response(plan)


@router.post("", response_model=TrainingPlanResponse, status_code=201)
async def create_plan(
    data: TrainingPlanCreate,
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanResponse:
    """Create a new training plan."""
    # Validate: strength needs exercises, running needs run_details
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

    plan = TrainingPlanModel(
        name=data.name,
        description=data.description,
        session_type=data.session_type,
        exercises_json=exercises_data,
        run_details_json=run_details_data,
        is_template=True,
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return _model_to_response(plan)


@router.patch("/{plan_id}", response_model=TrainingPlanResponse)
async def update_plan(
    plan_id: int,
    data: TrainingPlanUpdate,
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanResponse:
    """Update a training plan."""
    result = await db.execute(
        select(TrainingPlanModel).where(TrainingPlanModel.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan nicht gefunden")

    if data.name is not None:
        plan.name = data.name  # type: ignore[assignment]
    if data.description is not None:
        plan.description = data.description  # type: ignore[assignment]
    if data.exercises is not None:
        plan.exercises_json = json.dumps([ex.model_dump() for ex in data.exercises])  # type: ignore[assignment]
    if data.run_details is not None:
        plan.run_details_json = json.dumps(data.run_details.model_dump())  # type: ignore[assignment]

    await db.commit()
    await db.refresh(plan)
    return _model_to_response(plan)


@router.delete("/{plan_id}", status_code=204)
async def delete_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a training plan."""
    result = await db.execute(
        select(TrainingPlanModel).where(TrainingPlanModel.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan nicht gefunden")

    await db.delete(plan)
    await db.commit()


@router.post("/{plan_id}/duplicate", response_model=TrainingPlanResponse, status_code=201)
async def duplicate_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanResponse:
    """Duplicate a training plan."""
    result = await db.execute(
        select(TrainingPlanModel).where(TrainingPlanModel.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan nicht gefunden")

    new_plan = TrainingPlanModel(
        name=f"{plan.name} (Kopie)",
        description=plan.description,
        session_type=plan.session_type,
        exercises_json=plan.exercises_json,
        run_details_json=plan.run_details_json,
        is_template=True,
    )
    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)
    return _model_to_response(new_plan)


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

    # Fallback: classify by distance
    if distance_km and distance_km >= 15:
        return "long_run"
    return "easy"


@router.post(
    "/from-session/{session_id}",
    response_model=TrainingPlanResponse,
    status_code=201,
)
async def create_from_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanResponse:
    """Create a template from an existing session."""
    result = await db.execute(
        select(WorkoutModel).where(WorkoutModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session nicht gefunden")

    workout_type = str(session.workout_type)

    if workout_type == "strength":
        exercises_data: Optional[str] = None
        if session.exercises_json:
            # Parse and re-serialize to ensure valid format
            raw_exercises = json.loads(str(session.exercises_json))
            # Convert session exercise format to plan exercise format
            plan_exercises = []
            for ex in raw_exercises:
                sets = ex.get("sets", [])
                plan_exercises.append({
                    "name": ex.get("name", "Unbekannt"),
                    "category": ex.get("category", "legs"),
                    "sets": len(sets) if isinstance(sets, list) else int(ex.get("sets_count", 1)),
                    "reps": int(sets[0].get("reps", 10)) if isinstance(sets, list) and sets else 10,
                    "weight_kg": float(sets[0].get("weight_kg", 0)) if isinstance(sets, list) and sets else None,
                    "exercise_type": ex.get("exercise_type", "kraft"),
                    "notes": ex.get("notes"),
                })
            exercises_data = json.dumps(plan_exercises)

        plan = TrainingPlanModel(
            name=f"Template aus Session #{session_id}",
            session_type="strength",
            exercises_json=exercises_data,
            is_template=True,
        )
    else:
        # Running session — create running template
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

        plan = TrainingPlanModel(
            name=f"Template aus Session #{session_id}",
            session_type="running",
            run_details_json=json.dumps(run_details),
            is_template=True,
        )

    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return _model_to_response(plan)
