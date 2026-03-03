"""API routes for Training Plans and Training Phases (S07, S08, S09)."""

import json
from datetime import datetime
from typing import Optional

import yaml
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    PlanChangeLogModel,
    PlannedSessionModel,
    RaceGoalModel,
    TrainingPhaseModel,
    TrainingPlanModel,
    WeeklyPlanDayModel,
    WorkoutModel,
)
from app.infrastructure.database.session import get_db
from app.models.plan_changelog import (
    PlanChangeLogEntry,
    PlanChangeLogReasonUpdate,
    PlanChangeLogResponse,
)
from app.models.training_plan import (
    GenerateWeeklyPlansResponse,
    GenerationPreviewResponse,
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
from app.models.yaml_validation import YamlValidationIssue, YamlValidationResult
from app.services.plan_generator import generate_weekly_plans
from app.services.yaml_validator import validate_yaml_plan

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

    # Weekly plan week count
    wp_result = await db.execute(
        select(func.count(func.distinct(WeeklyPlanDayModel.week_start))).where(
            WeeklyPlanDayModel.plan_id == plan.id
        )
    )
    weekly_plan_week_count = wp_result.scalar() or 0

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
        weekly_plan_week_count=weekly_plan_week_count,
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

    # Weekly plan week count
    wp_result = await db.execute(
        select(func.count(func.distinct(WeeklyPlanDayModel.week_start))).where(
            WeeklyPlanDayModel.plan_id == plan.id
        )
    )
    weekly_plan_week_count = wp_result.scalar() or 0

    return TrainingPlanSummary(
        id=int(plan.id),  # type: ignore[arg-type]
        name=str(plan.name),
        status=str(plan.status),
        start_date=plan.start_date.isoformat() if plan.start_date else "",  # type: ignore[union-attr]
        end_date=plan.end_date.isoformat() if plan.end_date else "",  # type: ignore[union-attr]
        phase_count=phase_count,
        weekly_plan_week_count=weekly_plan_week_count,
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


_CHANGE_TYPE_CATEGORY: dict[str, str] = {
    "weekly_generated": "technical",
    "yaml_import": "technical",
    "back_sync": "technical",
    "phase_added": "structure",
    "phase_deleted": "structure",
    "manual_edit": "content",
    "plan_created": "meta",
}


async def log_plan_change(
    db: AsyncSession,
    plan_id: int,
    change_type: str,
    summary: str,
    details: Optional[dict[str, object]] = None,
    reason: Optional[str] = None,
    category: Optional[str] = None,
) -> None:
    """Log a change to a training plan (audit trail)."""
    resolved_category = category or _CHANGE_TYPE_CATEGORY.get(change_type)
    entry = PlanChangeLogModel(
        plan_id=plan_id,
        change_type=change_type,
        category=resolved_category,
        summary=summary,
        details_json=json.dumps(details) if details else None,
        reason=reason,
        created_at=datetime.utcnow(),
    )
    db.add(entry)


def _changelog_to_response(entry: PlanChangeLogModel) -> PlanChangeLogEntry:
    details: Optional[dict[str, object]] = None
    if entry.details_json:
        details = _parse_json(str(entry.details_json))
    return PlanChangeLogEntry(
        id=int(entry.id),  # type: ignore[arg-type]
        plan_id=int(entry.plan_id),  # type: ignore[arg-type]
        change_type=str(entry.change_type),
        category=str(entry.category) if entry.category else None,
        summary=str(entry.summary),
        details=details,
        reason=str(entry.reason) if entry.reason else None,
        created_by=str(entry.created_by) if entry.created_by else None,
        created_at=entry.created_at.isoformat() if entry.created_at else "",  # type: ignore[union-attr]
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

    await log_plan_change(
        db,
        int(plan.id),  # type: ignore[arg-type]
        "plan_created",
        f"Trainingsplan '{data.name}' erstellt",
        details={
            "category": "meta",
            "source": "user",
            "phase_count": len(data.phases) if data.phases else 0,
        },
    )
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


@router.post("/validate-yaml", response_model=YamlValidationResult)
async def validate_yaml_endpoint(
    yaml_file: UploadFile = File(..., description="YAML-Trainingsplan (.yaml/.yml)"),
) -> YamlValidationResult:
    """Validate a YAML training plan file and return structured errors/warnings."""
    if not yaml_file.filename or not yaml_file.filename.lower().endswith((".yaml", ".yml")):
        return YamlValidationResult(
            valid=False,
            errors=[
                YamlValidationIssue(
                    code="invalid_file_extension",
                    level="error",
                    message="Nur YAML-Dateien (.yaml, .yml) werden akzeptiert.",
                )
            ],
            warnings=[],
        )

    content = await yaml_file.read()
    if len(content) == 0:
        return YamlValidationResult(
            valid=False,
            errors=[
                YamlValidationIssue(
                    code="empty_file",
                    level="error",
                    message="Die YAML-Datei ist leer.",
                )
            ],
            warnings=[],
        )

    try:
        raw = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        return YamlValidationResult(
            valid=False,
            errors=[
                YamlValidationIssue(
                    code="yaml_syntax_error",
                    level="error",
                    message=f"YAML-Syntaxfehler: {exc}",
                )
            ],
            warnings=[],
        )

    if not isinstance(raw, dict):
        return YamlValidationResult(
            valid=False,
            errors=[
                YamlValidationIssue(
                    code="yaml_not_mapping",
                    level="error",
                    message="YAML muss ein Objekt auf oberster Ebene enthalten.",
                )
            ],
            warnings=[],
        )

    return validate_yaml_plan(raw)


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

    # Semantic validation before Pydantic parsing
    validation = validate_yaml_plan(raw)
    if not validation.valid:
        messages = "; ".join(e.message for e in validation.errors)
        raise HTTPException(
            status_code=422,
            detail=f"Validierungsfehler: {messages}",
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

    created_plan = await create_plan(data=plan_data, db=db)
    await log_plan_change(
        db,
        created_plan.id,
        "yaml_import",
        f"Plan aus YAML importiert: {yaml_file.filename}",
        details={
            "category": "technical",
            "source": "user",
            "filename": yaml_file.filename or "",
            "phase_count": len(created_plan.phases),
        },
    )
    await db.commit()
    return created_plan


@router.get(
    "/{plan_id}/generation-preview",
    response_model=GenerationPreviewResponse,
)
async def get_generation_preview(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
) -> GenerationPreviewResponse:
    """Preview what re-generation would affect: count edited vs unedited weeks."""
    result = await db.execute(select(TrainingPlanModel).where(TrainingPlanModel.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Trainingsplan nicht gefunden")

    days_result = await db.execute(
        select(WeeklyPlanDayModel)
        .where(WeeklyPlanDayModel.plan_id == plan_id)
        .order_by(WeeklyPlanDayModel.week_start)
    )
    days = list(days_result.scalars().all())

    weeks: dict[str, list[WeeklyPlanDayModel]] = {}
    for e in days:
        ws_key = str(e.week_start)
        if ws_key not in weeks:
            weeks[ws_key] = []
        weeks[ws_key].append(e)

    edited_week_starts: list[str] = []
    for ws_key in sorted(weeks.keys()):
        if any(bool(e.edited) for e in weeks[ws_key]):
            edited_week_starts.append(ws_key)

    return GenerationPreviewResponse(
        total_generated_weeks=len(weeks),
        edited_week_count=len(edited_week_starts),
        edited_week_starts=edited_week_starts,
        unedited_week_count=len(weeks) - len(edited_week_starts),
    )


@router.post(
    "/{plan_id}/generate",
    response_model=GenerateWeeklyPlansResponse,
)
async def generate_plan_weeks(
    plan_id: int,
    strategy: str = "all",
    db: AsyncSession = Depends(get_db),
) -> GenerateWeeklyPlansResponse:
    """Generate weekly plans from a training plan's phases.

    strategy=all: replaces all previously generated entries (default).
    strategy=unedited_only: preserves weeks with manually edited entries.
    """
    if strategy not in ("all", "unedited_only"):
        raise HTTPException(
            status_code=422,
            detail="strategy muss 'all' oder 'unedited_only' sein.",
        )

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
    new_week_starts = [ws for ws, _ in weekly_plans]

    # Determine edited weeks to skip (for unedited_only strategy)
    from datetime import date as date_type

    edited_weeks: set[date_type] = set()
    if strategy == "unedited_only":
        edited_result = await db.execute(
            select(WeeklyPlanDayModel.week_start)
            .where(
                WeeklyPlanDayModel.plan_id == plan_id,
                WeeklyPlanDayModel.edited.is_(True),
            )
            .distinct()
        )
        edited_weeks = {row[0] for row in edited_result.all()}

    # Delete old days + sessions by plan_id (skip edited weeks if strategy=unedited_only)
    old_by_plan = await db.execute(
        select(WeeklyPlanDayModel).where(WeeklyPlanDayModel.plan_id == plan_id)
    )
    for old_day in old_by_plan.scalars().all():
        if strategy == "unedited_only" and old_day.week_start in edited_weeks:
            continue
        # Delete associated sessions first
        old_sessions = await db.execute(
            select(PlannedSessionModel).where(PlannedSessionModel.day_id == old_day.id)
        )
        for old_sess in old_sessions.scalars().all():
            await db.delete(old_sess)
        await db.delete(old_day)

    # Delete manual entries for weeks that will be regenerated
    weeks_to_generate = (
        [ws for ws in new_week_starts if ws not in edited_weeks]
        if strategy == "unedited_only"
        else new_week_starts
    )

    if weeks_to_generate:
        old_by_week = await db.execute(
            select(WeeklyPlanDayModel).where(
                WeeklyPlanDayModel.week_start.in_(weeks_to_generate),
                WeeklyPlanDayModel.plan_id.is_(None),
            )
        )
        for old_day in old_by_week.scalars().all():
            old_sessions = await db.execute(
                select(PlannedSessionModel).where(PlannedSessionModel.day_id == old_day.id)
            )
            for old_sess in old_sessions.scalars().all():
                await db.delete(old_sess)
            await db.delete(old_day)

    await db.flush()

    # Insert new days + sessions (skip edited weeks if strategy=unedited_only)
    weeks_generated = 0
    for week_start, entries in weekly_plans:
        if strategy == "unedited_only" and week_start in edited_weeks:
            continue

        for plan_entry in entries:
            db_day = WeeklyPlanDayModel(
                plan_id=plan_id,
                week_start=week_start,
                day_of_week=plan_entry.day_of_week,
                is_rest_day=plan_entry.is_rest_day,
                notes=plan_entry.notes,
                edited=False,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(db_day)
            await db.flush()  # get db_day.id

            for sess in plan_entry.sessions:
                run_details_str: Optional[str] = None
                if sess.run_details is not None:
                    run_details_str = json.dumps(sess.run_details.model_dump())
                db_sess = PlannedSessionModel(
                    day_id=db_day.id,
                    position=sess.position,
                    training_type=sess.training_type,
                    template_id=sess.template_id,
                    run_details_json=run_details_str,
                    notes=sess.notes,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(db_sess)
        weeks_generated += 1

    await log_plan_change(
        db,
        plan_id,
        "weekly_generated",
        f"{weeks_generated} Wochen generiert (Strategie: {strategy})",
        details={
            "category": "technical",
            "source": "system",
            "weeks_generated": weeks_generated,
            "strategy": strategy,
        },
    )
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

    _FIELD_LABELS: dict[str, str] = {
        "name": "Name",
        "description": "Beschreibung",
        "status": "Status",
        "start_date": "Startdatum",
        "end_date": "Enddatum",
        "target_event_date": "Wettkampfdatum",
        "goal_id": "Ziel",
        "weekly_structure": "Wochenstruktur",
    }
    _META_FIELDS = {"name", "description", "status"}
    _STRUCTURE_FIELDS = {
        "start_date",
        "end_date",
        "target_event_date",
        "weekly_structure",
        "goal_id",
    }

    field_changes: list[dict[str, object]] = []
    changed_meta = False
    changed_structure = False

    def _track(field: str, old_val: object, new_val: object) -> None:
        nonlocal changed_meta, changed_structure
        field_changes.append(
            {
                "field": field,
                "from": str(old_val) if old_val is not None else None,
                "to": str(new_val) if new_val is not None else None,
                "label": _FIELD_LABELS.get(field, field),
            }
        )
        if field in _META_FIELDS:
            changed_meta = True
        if field in _STRUCTURE_FIELDS:
            changed_structure = True

    if data.name is not None:
        _track("name", plan.name, data.name)
        plan.name = data.name  # type: ignore[assignment]
    if data.description is not None:
        _track("description", plan.description, data.description)
        plan.description = data.description  # type: ignore[assignment]
    if data.start_date is not None:
        _track("start_date", plan.start_date, data.start_date)
        plan.start_date = data.start_date  # type: ignore[assignment]
    if data.end_date is not None:
        _track("end_date", plan.end_date, data.end_date)
        plan.end_date = data.end_date  # type: ignore[assignment]
    if data.target_event_date is not None:
        _track("target_event_date", plan.target_event_date, data.target_event_date)
        plan.target_event_date = data.target_event_date  # type: ignore[assignment]
    if data.weekly_structure is not None:
        _track(
            "weekly_structure",
            plan.weekly_structure_json,
            json.dumps(data.weekly_structure.model_dump()),
        )
        plan.weekly_structure_json = json.dumps(data.weekly_structure.model_dump())  # type: ignore[assignment]
    if data.status is not None:
        _track("status", plan.status, data.status)
        plan.status = data.status  # type: ignore[assignment]

    # S09: Update goal link
    if data.goal_id is not None:
        old_goal_id = plan.goal_id
        _track("goal_id", old_goal_id, data.goal_id)
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

    category = "structure" if changed_structure else "meta" if changed_meta else "meta"

    plan.updated_at = datetime.utcnow()  # type: ignore[assignment]
    await log_plan_change(
        db,
        plan_id,
        "plan_updated",
        "Plan aktualisiert",
        details={
            "category": category,
            "source": "user",
            "field_changes": field_changes,
        }
        if field_changes
        else None,
        category=category,
    )
    await db.commit()
    await db.refresh(plan)
    return await _plan_to_response(db, plan)


@router.delete("/{plan_id}", status_code=204)
async def delete_plan(
    plan_id: int,
    include_weekly_plans: bool = False,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a training plan and cascade-delete its phases.

    If include_weekly_plans=True, also deletes all linked weekly plan
    days (and their planned sessions). Workout references are cleared.
    Changelog entries are always cleaned up.
    """
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

    # Optionally delete linked weekly plan days + sessions
    if include_weekly_plans:
        weekly_days_result = await db.execute(
            select(WeeklyPlanDayModel).where(WeeklyPlanDayModel.plan_id == plan_id)
        )
        for day in weekly_days_result.scalars().all():
            sessions_result = await db.execute(
                select(PlannedSessionModel).where(PlannedSessionModel.day_id == day.id)
            )
            session_ids: list[int] = []
            for session in sessions_result.scalars().all():
                session_ids.append(int(session.id))  # type: ignore[arg-type]
                await db.delete(session)
            # Clear workout references to deleted sessions
            if session_ids:
                workout_result = await db.execute(
                    select(WorkoutModel).where(
                        WorkoutModel.planned_entry_id.in_(session_ids)  # type: ignore[union-attr]
                    )
                )
                for workout in workout_result.scalars().all():
                    workout.planned_entry_id = None  # type: ignore[assignment]
            await db.delete(day)

    # Always clean up changelog entries
    changelog_result = await db.execute(
        select(PlanChangeLogModel).where(PlanChangeLogModel.plan_id == plan_id)
    )
    for log_entry in changelog_result.scalars().all():
        await db.delete(log_entry)

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
    await log_plan_change(
        db,
        plan_id,
        "phase_added",
        f"Phase '{data.name}' hinzugefuegt (Woche {data.start_week}-{data.end_week})",
        details={
            "category": "structure",
            "source": "user",
            "phase_name": data.name,
            "phase_type": data.phase_type,
            "start_week": data.start_week,
            "end_week": data.end_week,
        },
    )
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

    _PHASE_LABELS: dict[str, str] = {
        "name": "Name",
        "phase_type": "Phasentyp",
        "start_week": "Startwoche",
        "end_week": "Endwoche",
        "focus": "Fokus",
        "target_metrics": "Zielmetriken",
        "weekly_template": "Wochenvorlage",
        "notes": "Notizen",
    }
    _PHASE_STRUCTURE = {"name", "phase_type", "start_week", "end_week"}

    phase_changes: list[dict[str, object]] = []
    has_structure_change = False
    has_content_change = False

    if data.name is not None:
        phase_changes.append(
            {
                "field": "name",
                "from": str(phase.name),
                "to": data.name,
                "label": _PHASE_LABELS["name"],
            }
        )
        has_structure_change = True
        phase.name = data.name  # type: ignore[assignment]
    if data.phase_type is not None:
        phase_changes.append(
            {
                "field": "phase_type",
                "from": str(phase.phase_type),
                "to": data.phase_type,
                "label": _PHASE_LABELS["phase_type"],
            }
        )
        has_structure_change = True
        phase.phase_type = data.phase_type  # type: ignore[assignment]
    if data.start_week is not None:
        phase_changes.append(
            {
                "field": "start_week",
                "from": int(phase.start_week),
                "to": data.start_week,
                "label": _PHASE_LABELS["start_week"],
            }
        )  # type: ignore[arg-type]
        has_structure_change = True
        phase.start_week = data.start_week  # type: ignore[assignment]
    if data.end_week is not None:
        phase_changes.append(
            {
                "field": "end_week",
                "from": int(phase.end_week),
                "to": data.end_week,
                "label": _PHASE_LABELS["end_week"],
            }
        )  # type: ignore[arg-type]
        has_structure_change = True
        phase.end_week = data.end_week  # type: ignore[assignment]
    if data.focus is not None:
        has_content_change = True
        phase.focus_json = json.dumps(data.focus.model_dump())  # type: ignore[assignment]
    if data.target_metrics is not None:
        has_content_change = True
        phase.target_metrics_json = json.dumps(data.target_metrics.model_dump())  # type: ignore[assignment]
    if data.weekly_template is not None:
        has_content_change = True
        phase.weekly_template_json = json.dumps(data.weekly_template.model_dump())  # type: ignore[assignment]
    if data.weekly_templates is not None:
        has_content_change = True
        phase.weekly_templates_json = json.dumps(data.weekly_templates.model_dump())  # type: ignore[assignment]
    if data.notes is not None:
        phase_changes.append(
            {
                "field": "notes",
                "from": str(phase.notes) if phase.notes else None,
                "to": data.notes,
                "label": _PHASE_LABELS["notes"],
            }
        )
        phase.notes = data.notes  # type: ignore[assignment]

    phase_category = (
        "structure" if has_structure_change else "content" if has_content_change else "meta"
    )

    await log_plan_change(
        db,
        plan_id,
        "phase_updated",
        f"Phase '{phase.name}' aktualisiert",
        details={
            "category": phase_category,
            "source": "user",
            "field_changes": phase_changes,
        }
        if phase_changes or has_content_change
        else None,
        category=phase_category,
    )
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

    phase_name = str(phase.name)
    await log_plan_change(
        db,
        plan_id,
        "phase_deleted",
        f"Phase '{phase_name}' geloescht",
        details={
            "category": "structure",
            "source": "user",
            "phase_name": phase_name,
        },
    )
    await db.delete(phase)
    await db.commit()


# --- Change Log ---


@router.get("/{plan_id}/changelog", response_model=PlanChangeLogResponse)
async def get_changelog(
    plan_id: int,
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> PlanChangeLogResponse:
    """Get the change log for a training plan (paginated, newest first)."""
    # Verify plan exists
    plan_result = await db.execute(
        select(TrainingPlanModel.id).where(TrainingPlanModel.id == plan_id)
    )
    if not plan_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Trainingsplan nicht gefunden")

    # Build base filter
    base_filter = PlanChangeLogModel.plan_id == plan_id
    if category:
        base_filter = base_filter & (PlanChangeLogModel.category == category)  # type: ignore[assignment]

    # Total count
    count_result = await db.execute(select(func.count(PlanChangeLogModel.id)).where(base_filter))
    total = count_result.scalar() or 0

    # Fetch entries
    result = await db.execute(
        select(PlanChangeLogModel)
        .where(base_filter)
        .order_by(PlanChangeLogModel.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    entries = [_changelog_to_response(e) for e in result.scalars().all()]

    return PlanChangeLogResponse(entries=entries, total=total)


@router.patch(
    "/{plan_id}/changelog/{log_id}",
    response_model=PlanChangeLogEntry,
)
async def update_changelog_reason(
    plan_id: int,
    log_id: int,
    data: PlanChangeLogReasonUpdate,
    db: AsyncSession = Depends(get_db),
) -> PlanChangeLogEntry:
    """Set or update the reason on a changelog entry."""
    result = await db.execute(
        select(PlanChangeLogModel).where(
            PlanChangeLogModel.id == log_id,
            PlanChangeLogModel.plan_id == plan_id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Changelog-Eintrag nicht gefunden")

    entry.reason = data.reason  # type: ignore[assignment]
    await db.commit()
    await db.refresh(entry)
    return _changelog_to_response(entry)
