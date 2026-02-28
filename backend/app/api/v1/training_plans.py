"""API routes for Training Plans (Issue #14)."""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import TrainingPlanModel
from app.infrastructure.database.session import get_db
from app.models.training_plan import (
    PlanExercise,
    TrainingPlanCreate,
    TrainingPlanListResponse,
    TrainingPlanResponse,
    TrainingPlanSummary,
    TrainingPlanUpdate,
)

router = APIRouter(prefix="/plans")


def _model_to_response(plan: TrainingPlanModel) -> TrainingPlanResponse:
    exercises: list[PlanExercise] = []
    if plan.exercises_json:
        raw = json.loads(str(plan.exercises_json))
        exercises = [PlanExercise(**ex) for ex in raw]

    return TrainingPlanResponse(
        id=int(plan.id),  # type: ignore[arg-type]
        name=str(plan.name),
        description=str(plan.description) if plan.description else None,
        session_type=str(plan.session_type),
        exercises=exercises,
        is_template=bool(plan.is_template),
        created_at=plan.created_at,  # type: ignore[arg-type]
        updated_at=plan.updated_at,  # type: ignore[arg-type]
    )


def _model_to_summary(plan: TrainingPlanModel) -> TrainingPlanSummary:
    exercises = []
    if plan.exercises_json:
        exercises = json.loads(str(plan.exercises_json))

    return TrainingPlanSummary(
        id=int(plan.id),  # type: ignore[arg-type]
        name=str(plan.name),
        session_type=str(plan.session_type),
        exercise_count=len(exercises),
        total_sets=sum(ex.get("sets", 0) for ex in exercises),
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
    exercises_data = [ex.model_dump() for ex in data.exercises]

    plan = TrainingPlanModel(
        name=data.name,
        description=data.description,
        session_type=data.session_type,
        exercises_json=json.dumps(exercises_data),
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
        is_template=True,
    )
    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)
    return _model_to_response(new_plan)
