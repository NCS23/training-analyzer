"""API routes for Training Plans and Training Phases (S07, S08, S09)."""

import json
from datetime import datetime
from typing import Optional

import yaml
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    RaceGoalModel,
    TrainingPhaseModel,
    TrainingPlanModel,
)
from app.infrastructure.database.session import get_db
from app.models.training_plan import (
    GoalSummary,
    PhaseFocus,
    PhaseTargetMetrics,
    TrainingPhaseCreate,
    TrainingPhaseResponse,
    TrainingPhaseUpdate,
    TrainingPlanCreate,
    TrainingPlanListResponse,
    TrainingPlanResponse,
    TrainingPlanSummary,
    TrainingPlanUpdate,
    WeeklyStructure,
)

router = APIRouter(prefix="/training-plans")


# --- Helpers ---


def _parse_json(raw: Optional[str]) -> Optional[dict]:  # type: ignore[type-arg]
    """Parse a JSON string or return None."""
    if not raw:
        return None
    try:
        return json.loads(raw)  # type: ignore[no-any-return]
    except (json.JSONDecodeError, ValueError):
        return None


def _phase_to_response(phase: TrainingPhaseModel) -> TrainingPhaseResponse:
    focus: Optional[PhaseFocus] = None
    raw_focus = _parse_json(str(phase.focus_json) if phase.focus_json else None)
    if raw_focus:
        focus = PhaseFocus(**raw_focus)

    target_metrics: Optional[PhaseTargetMetrics] = None
    raw_metrics = _parse_json(
        str(phase.target_metrics_json) if phase.target_metrics_json else None
    )
    if raw_metrics:
        target_metrics = PhaseTargetMetrics(**raw_metrics)

    return TrainingPhaseResponse(
        id=int(phase.id),  # type: ignore[arg-type]
        training_plan_id=int(phase.training_plan_id),  # type: ignore[arg-type]
        name=str(phase.name),
        phase_type=str(phase.phase_type),
        start_week=int(phase.start_week),  # type: ignore[arg-type]
        end_week=int(phase.end_week),  # type: ignore[arg-type]
        focus=focus,
        target_metrics=target_metrics,
        notes=str(phase.notes) if phase.notes else None,
        created_at=phase.created_at.isoformat() if phase.created_at else "",  # type: ignore[union-attr]
    )


async def _get_goal_summary(
    db: AsyncSession, goal_id: Optional[int],
) -> Optional[GoalSummary]:
    if goal_id is None:
        return None
    goal_id_int = int(goal_id)
    result = await db.execute(
        select(RaceGoalModel.id, RaceGoalModel.title).where(
            RaceGoalModel.id == goal_id_int
        )
    )
    row = result.one_or_none()
    if not row:
        return None
    return GoalSummary(id=int(row.id), title=str(row.title))  # type: ignore[arg-type]


async def _plan_to_response(
    db: AsyncSession, plan: TrainingPlanModel,
) -> TrainingPlanResponse:
    # Fetch phases
    result = await db.execute(
        select(TrainingPhaseModel)
        .where(TrainingPhaseModel.training_plan_id == plan.id)
        .order_by(TrainingPhaseModel.start_week)
    )
    phases = [_phase_to_response(p) for p in result.scalars().all()]

    # Goal summary
    g_id = int(plan.goal_id) if plan.goal_id else None  # type: ignore[arg-type]
    goal_summary = await _get_goal_summary(db, g_id)

    # Weekly structure
    weekly_structure: Optional[WeeklyStructure] = None
    raw_ws = _parse_json(
        str(plan.weekly_structure_json) if plan.weekly_structure_json else None
    )
    if raw_ws:
        weekly_structure = WeeklyStructure(**raw_ws)

    return TrainingPlanResponse(
        id=int(plan.id),  # type: ignore[arg-type]
        name=str(plan.name),
        description=str(plan.description) if plan.description else None,
        goal_id=int(plan.goal_id) if plan.goal_id else None,  # type: ignore[arg-type]
        start_date=plan.start_date.isoformat() if plan.start_date else "",  # type: ignore[union-attr]
        end_date=plan.end_date.isoformat() if plan.end_date else "",  # type: ignore[union-attr]
        target_event_date=plan.target_event_date.isoformat() if plan.target_event_date else None,  # type: ignore[union-attr]
        weekly_structure=weekly_structure,
        status=str(plan.status),
        phases=phases,
        goal_summary=goal_summary,
        created_at=plan.created_at.isoformat() if plan.created_at else "",  # type: ignore[union-attr]
        updated_at=plan.updated_at.isoformat() if plan.updated_at else "",  # type: ignore[union-attr]
    )


async def _plan_to_summary(
    db: AsyncSession, plan: TrainingPlanModel,
) -> TrainingPlanSummary:
    # Phase count
    result = await db.execute(
        select(func.count(TrainingPhaseModel.id)).where(
            TrainingPhaseModel.training_plan_id == plan.id
        )
    )
    phase_count = result.scalar() or 0

    # Goal title
    goal_title: Optional[str] = None
    if plan.goal_id:
        goal_result = await db.execute(
            select(RaceGoalModel.title).where(
                RaceGoalModel.id == int(plan.goal_id)  # type: ignore[arg-type]
            )
        )
        row = goal_result.scalar_one_or_none()
        if row:
            goal_title = str(row)

    return TrainingPlanSummary(
        id=int(plan.id),  # type: ignore[arg-type]
        name=str(plan.name),
        status=str(plan.status),
        start_date=plan.start_date.isoformat() if plan.start_date else "",  # type: ignore[union-attr]
        end_date=plan.end_date.isoformat() if plan.end_date else "",  # type: ignore[union-attr]
        phase_count=phase_count,
        goal_title=goal_title,
        created_at=plan.created_at.isoformat() if plan.created_at else "",  # type: ignore[union-attr]
        updated_at=plan.updated_at.isoformat() if plan.updated_at else "",  # type: ignore[union-attr]
    )


def _create_phase_model(
    plan_id: int, data: TrainingPhaseCreate,
) -> TrainingPhaseModel:
    focus_json: Optional[str] = None
    if data.focus:
        focus_json = json.dumps(data.focus.model_dump())
    target_metrics_json: Optional[str] = None
    if data.target_metrics:
        target_metrics_json = json.dumps(data.target_metrics.model_dump())

    return TrainingPhaseModel(
        training_plan_id=plan_id,
        name=data.name,
        phase_type=data.phase_type,
        start_week=data.start_week,
        end_week=data.end_week,
        focus_json=focus_json,
        target_metrics_json=target_metrics_json,
        notes=data.notes,
        created_at=datetime.utcnow(),
    )


# --- Plan CRUD ---


@router.get("", response_model=TrainingPlanListResponse)
async def list_plans(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanListResponse:
    """List all training plans, optionally filtered by status."""
    query = select(TrainingPlanModel).order_by(TrainingPlanModel.updated_at.desc())
    if status:
        query = query.where(TrainingPlanModel.status == status)

    result = await db.execute(query)
    plans = list(result.scalars().all())

    count_query = select(func.count(TrainingPlanModel.id))
    if status:
        count_query = count_query.where(TrainingPlanModel.status == status)
    total = (await db.execute(count_query)).scalar() or 0

    summaries = [await _plan_to_summary(db, p) for p in plans]
    return TrainingPlanListResponse(plans=summaries, total=total)


@router.post("", response_model=TrainingPlanResponse, status_code=201)
async def create_plan(
    data: TrainingPlanCreate,
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanResponse:
    """Create a new training plan with optional phases."""
    if data.end_date <= data.start_date:
        raise HTTPException(
            status_code=422,
            detail="Enddatum muss nach Startdatum liegen.",
        )

    weekly_structure_json: Optional[str] = None
    if data.weekly_structure:
        weekly_structure_json = json.dumps(data.weekly_structure.model_dump())

    plan = TrainingPlanModel(
        name=data.name,
        description=data.description,
        goal_id=data.goal_id,
        start_date=data.start_date,
        end_date=data.end_date,
        target_event_date=data.target_event_date,
        weekly_structure_json=weekly_structure_json,
        status=data.status or "draft",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(plan)
    await db.flush()  # Get plan.id before adding phases

    # Create phases
    if data.phases:
        for phase_data in data.phases:
            phase = _create_phase_model(
                int(plan.id), phase_data,  # type: ignore[arg-type]
            )
            db.add(phase)

    # S09: Set bidirectional link on goal
    if data.goal_id:
        goal_result = await db.execute(
            select(RaceGoalModel).where(RaceGoalModel.id == data.goal_id)
        )
        goal = goal_result.scalar_one_or_none()
        if goal:
            goal.training_plan_id = plan.id  # type: ignore[assignment]

    await db.commit()
    await db.refresh(plan)
    return await _plan_to_response(db, plan)


def _yaml_to_plan_create(data: dict) -> dict:  # type: ignore[type-arg]
    """Map YAML fields to TrainingPlanCreate schema fields."""
    result = {k: v for k, v in data.items() if k not in ("phases", "goal_title")}

    if "phases" in data and data["phases"]:
        result["phases"] = []
        for phase in data["phases"]:
            mapped = dict(phase)
            if "type" in mapped and "phase_type" not in mapped:
                mapped["phase_type"] = mapped.pop("type")
            result["phases"].append(mapped)

    return result


@router.post("/import", response_model=TrainingPlanResponse, status_code=201)
async def import_plan_from_yaml(
    yaml_file: UploadFile = File(..., description="YAML-Trainingsplan (.yaml/.yml)"),
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanResponse:
    """Import a training plan from a YAML file."""
    if not yaml_file.filename or not yaml_file.filename.lower().endswith((".yaml", ".yml")):
        raise HTTPException(
            status_code=400,
            detail="Nur YAML-Dateien (.yaml, .yml) werden akzeptiert.",
        )

    content = await yaml_file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="YAML-Datei ist leer.")

    try:
        raw = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"YAML-Parsing fehlgeschlagen: {exc}",
        ) from None

    if not isinstance(raw, dict):
        raise HTTPException(
            status_code=400,
            detail="YAML muss ein Objekt (Mapping) auf oberster Ebene enthalten.",
        )

    # Resolve goal_title -> goal_id
    goal_title = raw.get("goal_title")
    if goal_title and not raw.get("goal_id"):
        result = await db.execute(
            select(RaceGoalModel.id).where(
                func.lower(RaceGoalModel.title) == goal_title.lower()
            )
        )
        goal_id = result.scalar_one_or_none()
        if goal_id:
            raw["goal_id"] = int(goal_id)

    mapped = _yaml_to_plan_create(raw)

    try:
        plan_data = TrainingPlanCreate(**mapped)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Validierungsfehler: {exc}",
        ) from None

    return await create_plan(data=plan_data, db=db)


@router.get("/{plan_id}", response_model=TrainingPlanResponse)
async def get_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanResponse:
    """Get a training plan with its phases and goal summary."""
    result = await db.execute(
        select(TrainingPlanModel).where(TrainingPlanModel.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Trainingsplan nicht gefunden")
    return await _plan_to_response(db, plan)


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
        raise HTTPException(status_code=404, detail="Trainingsplan nicht gefunden")

    if data.name is not None:
        plan.name = data.name  # type: ignore[assignment]
    if data.description is not None:
        plan.description = data.description  # type: ignore[assignment]
    if data.start_date is not None:
        plan.start_date = data.start_date  # type: ignore[assignment]
    if data.end_date is not None:
        plan.end_date = data.end_date  # type: ignore[assignment]
    if data.target_event_date is not None:
        plan.target_event_date = data.target_event_date  # type: ignore[assignment]
    if data.weekly_structure is not None:
        plan.weekly_structure_json = json.dumps(data.weekly_structure.model_dump())  # type: ignore[assignment]
    if data.status is not None:
        plan.status = data.status  # type: ignore[assignment]

    # S09: Update goal link
    if data.goal_id is not None:
        old_goal_id = plan.goal_id
        plan.goal_id = data.goal_id  # type: ignore[assignment]

        # Remove old bidirectional link
        if old_goal_id:
            old_goal_result = await db.execute(
                select(RaceGoalModel).where(RaceGoalModel.id == int(old_goal_id))  # type: ignore[arg-type]
            )
            old_goal = old_goal_result.scalar_one_or_none()
            if old_goal and old_goal.training_plan_id == plan.id:
                old_goal.training_plan_id = None  # type: ignore[assignment]

        # Set new bidirectional link
        if data.goal_id:
            new_goal_result = await db.execute(
                select(RaceGoalModel).where(RaceGoalModel.id == data.goal_id)
            )
            new_goal = new_goal_result.scalar_one_or_none()
            if new_goal:
                new_goal.training_plan_id = plan.id  # type: ignore[assignment]

    plan.updated_at = datetime.utcnow()  # type: ignore[assignment]
    await db.commit()
    await db.refresh(plan)
    return await _plan_to_response(db, plan)


@router.delete("/{plan_id}", status_code=204)
async def delete_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a training plan and cascade-delete its phases."""
    result = await db.execute(
        select(TrainingPlanModel).where(TrainingPlanModel.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Trainingsplan nicht gefunden")

    # Remove bidirectional link from goal
    if plan.goal_id:
        goal_result = await db.execute(
            select(RaceGoalModel).where(RaceGoalModel.id == int(plan.goal_id))  # type: ignore[arg-type]
        )
        goal = goal_result.scalar_one_or_none()
        if goal and goal.training_plan_id == plan.id:
            goal.training_plan_id = None  # type: ignore[assignment]

    # Delete all phases
    phase_result = await db.execute(
        select(TrainingPhaseModel).where(
            TrainingPhaseModel.training_plan_id == plan_id
        )
    )
    for phase in phase_result.scalars().all():
        await db.delete(phase)

    await db.delete(plan)
    await db.commit()


# --- Phase CRUD (nested) ---


@router.get("/{plan_id}/phases", response_model=list[TrainingPhaseResponse])
async def list_phases(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[TrainingPhaseResponse]:
    """List all phases of a training plan."""
    # Verify plan exists
    plan_result = await db.execute(
        select(TrainingPlanModel.id).where(TrainingPlanModel.id == plan_id)
    )
    if not plan_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Trainingsplan nicht gefunden")

    result = await db.execute(
        select(TrainingPhaseModel)
        .where(TrainingPhaseModel.training_plan_id == plan_id)
        .order_by(TrainingPhaseModel.start_week)
    )
    return [_phase_to_response(p) for p in result.scalars().all()]


@router.post(
    "/{plan_id}/phases",
    response_model=TrainingPhaseResponse,
    status_code=201,
)
async def create_phase(
    plan_id: int,
    data: TrainingPhaseCreate,
    db: AsyncSession = Depends(get_db),
) -> TrainingPhaseResponse:
    """Add a phase to a training plan."""
    plan_result = await db.execute(
        select(TrainingPlanModel).where(TrainingPlanModel.id == plan_id)
    )
    if not plan_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Trainingsplan nicht gefunden")

    if data.end_week < data.start_week:
        raise HTTPException(
            status_code=422,
            detail="end_week muss >= start_week sein.",
        )

    phase = _create_phase_model(plan_id, data)
    db.add(phase)
    await db.commit()
    await db.refresh(phase)
    return _phase_to_response(phase)


@router.patch(
    "/{plan_id}/phases/{phase_id}",
    response_model=TrainingPhaseResponse,
)
async def update_phase(
    plan_id: int,
    phase_id: int,
    data: TrainingPhaseUpdate,
    db: AsyncSession = Depends(get_db),
) -> TrainingPhaseResponse:
    """Update a phase in a training plan."""
    result = await db.execute(
        select(TrainingPhaseModel).where(
            TrainingPhaseModel.id == phase_id,
            TrainingPhaseModel.training_plan_id == plan_id,
        )
    )
    phase = result.scalar_one_or_none()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase nicht gefunden")

    if data.name is not None:
        phase.name = data.name  # type: ignore[assignment]
    if data.phase_type is not None:
        phase.phase_type = data.phase_type  # type: ignore[assignment]
    if data.start_week is not None:
        phase.start_week = data.start_week  # type: ignore[assignment]
    if data.end_week is not None:
        phase.end_week = data.end_week  # type: ignore[assignment]
    if data.focus is not None:
        phase.focus_json = json.dumps(data.focus.model_dump())  # type: ignore[assignment]
    if data.target_metrics is not None:
        phase.target_metrics_json = json.dumps(data.target_metrics.model_dump())  # type: ignore[assignment]
    if data.notes is not None:
        phase.notes = data.notes  # type: ignore[assignment]

    await db.commit()
    await db.refresh(phase)
    return _phase_to_response(phase)


@router.delete("/{plan_id}/phases/{phase_id}", status_code=204)
async def delete_phase(
    plan_id: int,
    phase_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a phase from a training plan."""
    result = await db.execute(
        select(TrainingPhaseModel).where(
            TrainingPhaseModel.id == phase_id,
            TrainingPhaseModel.training_plan_id == plan_id,
        )
    )
    phase = result.scalar_one_or_none()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase nicht gefunden")

    await db.delete(phase)
    await db.commit()
