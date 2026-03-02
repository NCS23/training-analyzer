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
    WeeklyPlanEntryModel,
)
from app.infrastructure.database.session import get_db
from app.models.training_plan import (
    GenerateWeeklyPlansResponse,
    GoalSummary,
    PhaseFocus,
    PhaseTargetMetrics,
    PhaseWeeklyTemplate,
    PhaseWeeklyTemplates,
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
from app.services.plan_generator import generate_weekly_plans

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
    raw_metrics = _parse_json(str(phase.target_metrics_json) if phase.target_metrics_json else None)
    if raw_metrics:
        target_metrics = PhaseTargetMetrics(**raw_metrics)

    weekly_template: Optional[PhaseWeeklyTemplate] = None
    raw_template = _parse_json(
        str(phase.weekly_template_json) if phase.weekly_template_json else None
    )
    if raw_template:
        weekly_template = PhaseWeeklyTemplate(**raw_template)

    weekly_templates: Optional[PhaseWeeklyTemplates] = None
    raw_templates = _parse_json(
        str(phase.weekly_templates_json) if phase.weekly_templates_json else None
    )
    if raw_templates:
        weekly_templates = PhaseWeeklyTemplates(**raw_templates)

    return TrainingPhaseResponse(
        id=int(phase.id),  # type: ignore[arg-type]
        training_plan_id=int(phase.training_plan_id),  # type: ignore[arg-type]
        name=str(phase.name),
        phase_type=str(phase.phase_type),
        start_week=int(phase.start_week),  # type: ignore[arg-type]
        end_week=int(phase.end_week),  # type: ignore[arg-type]
        focus=focus,
        target_metrics=target_metrics,
        weekly_template=weekly_template,
        weekly_templates=weekly_templates,
        notes=str(phase.notes) if phase.notes else None,
        created_at=phase.created_at.isoformat() if phase.created_at else "",  # type: ignore[union-attr]
    )


async def _get_goal_summary(
    db: AsyncSession,
    goal_id: Optional[int],
) -> Optional[GoalSummary]:
    if goal_id is None:
        return None
    goal_id_int = int(goal_id)
    result = await db.execute(
        select(RaceGoalModel.id, RaceGoalModel.title).where(RaceGoalModel.id == goal_id_int)
    )
    row = result.one_or_none()
    if not row:
        return None
    return GoalSummary(id=int(row.id), title=str(row.title))  # type: ignore[arg-type]


async def _plan_to_response(
    db: AsyncSession,
    plan: TrainingPlanModel,
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
    raw_ws = _parse_json(str(plan.weekly_structure_json) if plan.weekly_structure_json else None)
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
    db: AsyncSession,
    plan: TrainingPlanModel,
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
    plan_id: int,
    data: TrainingPhaseCreate,
) -> TrainingPhaseModel:
    focus_json: Optional[str] = None
    if data.focus:
        focus_json = json.dumps(data.focus.model_dump())
    target_metrics_json: Optional[str] = None
    if data.target_metrics:
        target_metrics_json = json.dumps(data.target_metrics.model_dump())
    weekly_template_json: Optional[str] = None
    if data.weekly_template:
        weekly_template_json = json.dumps(data.weekly_template.model_dump())
    weekly_templates_json: Optional[str] = None
    if data.weekly_templates:
        weekly_templates_json = json.dumps(data.weekly_templates.model_dump())

    return TrainingPhaseModel(
        training_plan_id=plan_id,
        name=data.name,
        phase_type=data.phase_type,
        start_week=data.start_week,
        end_week=data.end_week,
        focus_json=focus_json,
        target_metrics_json=target_metrics_json,
        weekly_template_json=weekly_template_json,
        weekly_templates_json=weekly_templates_json,
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
    """Create a new training plan with optional phases and auto-create goal."""
    if data.end_date <= data.start_date:
        raise HTTPException(
            status_code=422,
            detail="Enddatum muss nach Startdatum liegen.",
        )

    # Auto-create or resolve goal
    goal_id = data.goal_id
    if data.goal and not goal_id:
        # Check if a goal with this title already exists
        existing_result = await db.execute(
            select(RaceGoalModel).where(func.lower(RaceGoalModel.title) == data.goal.title.lower())
        )
        existing_goal = existing_result.scalar_one_or_none()
        if existing_goal:
            goal_id = int(existing_goal.id)  # type: ignore[arg-type]
        else:
            # Create new goal — race_date defaults to target_event_date or end_date
            race_date = data.goal.race_date or data.target_event_date or data.end_date
            new_goal = RaceGoalModel(
                title=data.goal.title,
                race_date=race_date,
                distance_km=data.goal.distance_km,
                target_time_seconds=data.goal.target_time_seconds,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(new_goal)
            await db.flush()
            goal_id = int(new_goal.id)  # type: ignore[arg-type]

    weekly_structure_json: Optional[str] = None
    if data.weekly_structure:
        weekly_structure_json = json.dumps(data.weekly_structure.model_dump())

    plan = TrainingPlanModel(
        name=data.name,
        description=data.description,
        goal_id=goal_id,
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
                int(plan.id),
                phase_data,  # type: ignore[arg-type]
            )
            db.add(phase)

    # S09: Set bidirectional link on goal
    if goal_id:
        goal_result = await db.execute(select(RaceGoalModel).where(RaceGoalModel.id == goal_id))
        goal_obj = goal_result.scalar_one_or_none()
        if goal_obj:
            goal_obj.training_plan_id = plan.id  # type: ignore[assignment]

    await db.commit()
    await db.refresh(plan)
    return await _plan_to_response(db, plan)


def _parse_time_to_seconds(time_str: str) -> int:
    """Parse 'H:MM:SS' or 'MM:SS' to total seconds."""
    parts = str(time_str).split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return int(time_str)


def _yaml_to_plan_create(data: dict) -> dict:  # type: ignore[type-arg]
    """Map YAML fields to TrainingPlanCreate schema fields."""
    result = {k: v for k, v in data.items() if k not in ("phases", "goal_title")}

    # Handle goal block — convert target_time string to target_time_seconds
    if "goal" in result and isinstance(result["goal"], dict):
        goal = dict(result["goal"])
        if "target_time" in goal and "target_time_seconds" not in goal:
            goal["target_time_seconds"] = _parse_time_to_seconds(goal.pop("target_time"))
        elif "target_time" in goal:
            goal.pop("target_time")  # target_time_seconds takes precedence
        result["goal"] = goal

    if "phases" in data and data["phases"]:
        result["phases"] = []
        for phase in data["phases"]:
            mapped = dict(phase)
            if "type" in mapped and "phase_type" not in mapped:
                mapped["phase_type"] = mapped.pop("type")

            # Convert YAML weekly_template shorthand to PhaseWeeklyTemplate
            if "weekly_template" in mapped and isinstance(mapped["weekly_template"], list):
                days = []
                for day_entry in mapped["weekly_template"]:
                    if not isinstance(day_entry, dict):
                        continue
                    day_of_week = day_entry.get("day", 0)
                    is_rest = day_entry.get("rest", False)
                    training_type = day_entry.get("type") if not is_rest else None
                    run_type = day_entry.get("run_type") if training_type == "running" else None
                    days.append(
                        {
                            "day_of_week": day_of_week,
                            "training_type": training_type,
                            "is_rest_day": bool(is_rest),
                            "run_type": run_type,
                            "template_id": None,
                            "notes": day_entry.get("notes"),
                            "run_details": day_entry.get("run_details"),
                        }
                    )
                mapped["weekly_template"] = {"days": days}

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

    # Resolve goal_title -> goal_id (backward compat, lookup only)
    goal_title = raw.get("goal_title")
    if goal_title and not raw.get("goal_id") and not raw.get("goal"):
        result = await db.execute(
            select(RaceGoalModel.id).where(func.lower(RaceGoalModel.title) == goal_title.lower())
        )
        found_goal_id = result.scalar_one_or_none()
        if found_goal_id:
            raw["goal_id"] = int(found_goal_id)

    mapped = _yaml_to_plan_create(raw)

    try:
        plan_data = TrainingPlanCreate(**mapped)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Validierungsfehler: {exc}",
        ) from None

    return await create_plan(data=plan_data, db=db)


@router.post(
    "/{plan_id}/generate",
    response_model=GenerateWeeklyPlansResponse,
)
async def generate_plan_weeks(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
) -> GenerateWeeklyPlansResponse:
    """Generate weekly plans from a training plan's phases.

    Always replaces all previously generated entries for this plan.
    Manual entries (plan_id=NULL) are preserved.
    """
    # Load plan
    result = await db.execute(select(TrainingPlanModel).where(TrainingPlanModel.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Trainingsplan nicht gefunden")

    # Load phases
    phase_result = await db.execute(
        select(TrainingPhaseModel)
        .where(TrainingPhaseModel.training_plan_id == plan_id)
        .order_by(TrainingPhaseModel.start_week)
    )
    phases = list(phase_result.scalars().all())
    if not phases:
        raise HTTPException(
            status_code=400,
            detail="Trainingsplan hat keine Phasen. Bitte zuerst Phasen anlegen.",
        )

    # Load goal (optional, for pace calculation)
    goal: Optional[RaceGoalModel] = None
    if plan.goal_id:
        goal_result = await db.execute(
            select(RaceGoalModel).where(
                RaceGoalModel.id == int(plan.goal_id)  # type: ignore[arg-type]
            )
        )
        goal = goal_result.scalar_one_or_none()

    # Parse rest days from weekly_structure
    rest_days = [6]  # Default: Sunday
    if plan.weekly_structure_json:
        try:
            ws = json.loads(str(plan.weekly_structure_json))
            rest_days = ws.get("rest_days", [6])
        except (json.JSONDecodeError, ValueError):
            pass

    # Generate
    weekly_plans = generate_weekly_plans(plan, phases, rest_days, goal)

    # Collect all week_start dates that will be generated
    new_week_starts = [ws for ws, _ in weekly_plans]

    # Delete old entries: (1) by plan_id, (2) by week_start for legacy/manual
    old_by_plan = await db.execute(
        select(WeeklyPlanEntryModel).where(WeeklyPlanEntryModel.plan_id == plan_id)
    )
    for old_entry in old_by_plan.scalars().all():
        await db.delete(old_entry)

    if new_week_starts:
        old_by_week = await db.execute(
            select(WeeklyPlanEntryModel).where(
                WeeklyPlanEntryModel.week_start.in_(new_week_starts),
                WeeklyPlanEntryModel.plan_id.is_(None),
            )
        )
        for old_entry in old_by_week.scalars().all():
            await db.delete(old_entry)

    await db.flush()

    # Insert new entries (with plan_id link)
    weeks_generated = 0
    for week_start, entries in weekly_plans:
        for plan_entry in entries:
            run_details_str: Optional[str] = None
            if plan_entry.run_details is not None:
                run_details_str = json.dumps(plan_entry.run_details.model_dump())

            db_entry = WeeklyPlanEntryModel(
                plan_id=plan_id,
                week_start=week_start,
                day_of_week=plan_entry.day_of_week,
                training_type=plan_entry.training_type,
                is_rest_day=plan_entry.is_rest_day,
                notes=plan_entry.notes,
                run_details_json=run_details_str,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(db_entry)
        weeks_generated += 1

    await db.commit()

    return GenerateWeeklyPlansResponse(
        weeks_generated=weeks_generated,
        total_weeks=len(weekly_plans),
    )


@router.get("/{plan_id}", response_model=TrainingPlanResponse)
async def get_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
) -> TrainingPlanResponse:
    """Get a training plan with its phases and goal summary."""
    result = await db.execute(select(TrainingPlanModel).where(TrainingPlanModel.id == plan_id))
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
    result = await db.execute(select(TrainingPlanModel).where(TrainingPlanModel.id == plan_id))
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
    result = await db.execute(select(TrainingPlanModel).where(TrainingPlanModel.id == plan_id))
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
        select(TrainingPhaseModel).where(TrainingPhaseModel.training_plan_id == plan_id)
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
    plan_result = await db.execute(select(TrainingPlanModel).where(TrainingPlanModel.id == plan_id))
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
    if data.weekly_template is not None:
        phase.weekly_template_json = json.dumps(data.weekly_template.model_dump())  # type: ignore[assignment]
    if data.weekly_templates is not None:
        phase.weekly_templates_json = json.dumps(data.weekly_templates.model_dump())  # type: ignore[assignment]
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
