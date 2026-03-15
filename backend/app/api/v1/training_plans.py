"""API routes for Training Plans and Training Phases (S07, S08, S09)."""

import contextlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import yaml
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import ValidationError
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    ExerciseModel,
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
from app.models.taxonomy import SEGMENT_TYPE_MIGRATION, SESSION_TYPE_MIGRATION
from app.models.training_plan import (
    AutoGenerationResult,
    AutoRegenerationResult,
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
from app.models.yaml_validation import ExerciseCheck, YamlValidationIssue, YamlValidationResult
from app.services.exercise_enrichment import find_similar_exercises
from app.services.plan_generator import generate_weekly_plans
from app.services.yaml_validator import extract_exercise_names, validate_yaml_plan

router = APIRouter(prefix="/training-plans")


# --- Helpers ---


def _parse_json(raw: Optional[str]) -> Optional[dict[str, Any]]:
    """Parse a JSON string or return None."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return None


def _phase_to_response(
    phase: TrainingPhaseModel,
    auto_regeneration: Optional[AutoRegenerationResult] = None,
) -> TrainingPhaseResponse:
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
        id=phase.id,
        training_plan_id=phase.training_plan_id,
        name=str(phase.name),
        phase_type=str(phase.phase_type),
        start_week=phase.start_week,
        end_week=phase.end_week,
        focus=focus,
        target_metrics=target_metrics,
        weekly_template=weekly_template,
        weekly_templates=weekly_templates,
        notes=str(phase.notes) if phase.notes else None,
        auto_regeneration=auto_regeneration,
        created_at=phase.created_at.isoformat() if phase.created_at else "",
    )


async def _get_goal_summary(
    db: AsyncSession,
    goal_id: Optional[int],
) -> Optional[GoalSummary]:
    if goal_id is None:
        return None
    goal_id_int = int(goal_id)
    result = await db.execute(
        select(
            RaceGoalModel.id,
            RaceGoalModel.title,
            RaceGoalModel.race_date,
            RaceGoalModel.target_time_seconds,
        ).where(RaceGoalModel.id == goal_id_int)
    )
    row = result.one_or_none()
    if not row:
        return None

    # Format target time (#152)
    target_secs = int(row.target_time_seconds) if row.target_time_seconds else None
    time_fmt: Optional[str] = None
    if target_secs:
        hours = target_secs // 3600
        mins = (target_secs % 3600) // 60
        secs = target_secs % 60
        time_fmt = f"{hours}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins}:{secs:02d}"

    # Days until race (#152)
    days_until: Optional[int] = None
    race_date_iso: Optional[str] = None
    if row.race_date:
        race_dt = row.race_date
        if hasattr(race_dt, "date"):
            race_dt = race_dt.date()
        race_date_iso = race_dt.isoformat()
        days_until = (race_dt - date.today()).days

    return GoalSummary(
        id=row.id,
        title=row.title,
        race_date=race_date_iso,
        target_time_formatted=time_fmt,
        days_until=days_until,
    )


async def _plan_to_response(
    db: AsyncSession,
    plan: TrainingPlanModel,
    auto_generation_result: Optional[AutoGenerationResult] = None,
) -> TrainingPlanResponse:
    # Fetch phases
    result = await db.execute(
        select(TrainingPhaseModel)
        .where(TrainingPhaseModel.training_plan_id == plan.id)
        .order_by(TrainingPhaseModel.start_week)
    )
    phases = [_phase_to_response(p) for p in result.scalars().all()]

    # Goal summary
    g_id = plan.goal_id if plan.goal_id else None
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
        id=plan.id,
        name=str(plan.name),
        description=str(plan.description) if plan.description else None,
        goal_id=plan.goal_id if plan.goal_id else None,
        start_date=plan.start_date.isoformat() if plan.start_date else "",
        end_date=plan.end_date.isoformat() if plan.end_date else "",
        target_event_date=plan.target_event_date.isoformat() if plan.target_event_date else None,
        weekly_structure=weekly_structure,
        status=str(plan.status),
        phases=phases,
        goal_summary=goal_summary,
        weekly_plan_week_count=weekly_plan_week_count,
        auto_generation_result=auto_generation_result,
        created_at=plan.created_at.isoformat() if plan.created_at else "",
        updated_at=plan.updated_at.isoformat() if plan.updated_at else "",
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
            select(RaceGoalModel.title).where(RaceGoalModel.id == plan.goal_id)
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
        id=plan.id,
        name=str(plan.name),
        status=str(plan.status),
        start_date=plan.start_date.isoformat() if plan.start_date else "",
        end_date=plan.end_date.isoformat() if plan.end_date else "",
        phase_count=phase_count,
        weekly_plan_week_count=weekly_plan_week_count,
        goal_title=goal_title,
        created_at=plan.created_at.isoformat() if plan.created_at else "",
        updated_at=plan.updated_at.isoformat() if plan.updated_at else "",
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
        id=entry.id,
        plan_id=entry.plan_id,
        change_type=str(entry.change_type),
        category=str(entry.category) if entry.category else None,
        summary=str(entry.summary),
        details=details,
        reason=str(entry.reason) if entry.reason else None,
        created_by=str(entry.created_by) if entry.created_by else None,
        created_at=entry.created_at.isoformat() if entry.created_at else "",
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
            goal_id = existing_goal.id
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
            goal_id = new_goal.id

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
                plan.id,
                phase_data,
            )
            db.add(phase)

    # S09: Set bidirectional link on goal
    if goal_id:
        goal_result = await db.execute(select(RaceGoalModel).where(RaceGoalModel.id == goal_id))
        goal_obj = goal_result.scalar_one_or_none()
        if goal_obj:
            goal_obj.training_plan_id = plan.id

    await log_plan_change(
        db,
        plan.id,
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


_DOW_NAMES_DE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]


def _format_field_path(loc: tuple[str | int, ...]) -> str:
    """Convert Pydantic field path to human-readable German string."""
    parts: list[str] = []
    i = 0
    loc_list = list(loc)
    while i < len(loc_list):
        segment = loc_list[i]
        next_val = loc_list[i + 1] if i + 1 < len(loc_list) else None
        if segment == "phases" and isinstance(next_val, int):
            parts.append(f"Phase {next_val + 1}")
            i += 2
        elif segment == "days" and isinstance(next_val, int):
            day_name = _DOW_NAMES_DE[next_val] if 0 <= next_val <= 6 else str(next_val)
            parts.append(
                f"Tag {next_val} ({day_name})" if 0 <= next_val <= 6 else f"Tag {next_val}"
            )
            i += 2
        elif segment == "intervals" and isinstance(next_val, int):
            parts.append(f"Intervall {next_val + 1}")
            i += 2
        elif segment == "sessions" and isinstance(next_val, int):
            parts.append(f"Session {next_val + 1}")
            i += 2
        elif isinstance(segment, int):
            parts.append(f"#{segment + 1}")
            i += 1
        elif segment in ("weekly_template", "weekly_templates", "run_details", "body"):
            i += 1  # skip structural nesting
        else:
            parts.append(str(segment))
            i += 1
    return " → ".join(parts) if parts else "Unbekanntes Feld"


def _format_pydantic_errors(exc: ValidationError) -> str:
    """Convert Pydantic ValidationError to human-readable German message."""
    messages: list[str] = []
    for err in exc.errors():
        loc = err.get("loc", ())
        loc_str = _format_field_path(loc)
        input_val = err.get("input", "")
        err_type = err.get("type", "")

        if err_type == "string_pattern_mismatch":
            messages.append(f"{loc_str}: Wert '{input_val}' ist ungueltig.")
        elif err_type == "greater_than":
            ctx = err.get("ctx", {})
            messages.append(
                f"{loc_str}: Wert muss groesser als {ctx.get('gt', '?')} sein (ist: {input_val})."
            )
        elif err_type == "less_than_equal":
            ctx = err.get("ctx", {})
            messages.append(
                f"{loc_str}: Wert darf maximal {ctx.get('le', '?')} sein (ist: {input_val})."
            )
        elif err_type == "missing":
            messages.append(f"{loc_str}: Pflichtfeld fehlt.")
        else:
            messages.append(f"{loc_str}: {err.get('msg', str(err))}")

    return "\n".join(f"• {m}" for m in messages)


async def _check_unknown_exercises(
    raw: dict[str, object],
    result: YamlValidationResult,
    db: AsyncSession,
) -> YamlValidationResult:
    """Check exercise_name values in YAML against the Exercise Library.

    Adds ``unknown_exercises`` entries + warnings for each unknown name.
    Does NOT block import (``valid`` remains unchanged).
    """
    from collections import defaultdict

    exercise_refs = extract_exercise_names(raw)
    if not exercise_refs:
        return result

    db_result = await db.execute(select(ExerciseModel.name))
    known_names = [str(n) for n in db_result.scalars().all()]
    known_set = {n.lower() for n in known_names}

    grouped: dict[str, list[str]] = defaultdict(list)
    for name, loc in exercise_refs:
        if name.lower() not in known_set:
            grouped[name].append(loc)

    if not grouped:
        return result

    unknown_exercises: list[ExerciseCheck] = []
    new_warnings: list[YamlValidationIssue] = list(result.warnings)
    for name, locs in grouped.items():
        suggestions = find_similar_exercises(name, known_names)
        unknown_exercises.append(
            ExerciseCheck(
                exercise_name=name,
                locations=locs,
                suggestions=suggestions,
            )
        )
        new_warnings.append(
            YamlValidationIssue(
                code="unknown_exercise_name",
                level="warning",
                message=(
                    f"Uebung '{name}' existiert nicht in der Bibliothek "
                    "und wird beim Import neu erstellt."
                ),
                location=locs[0],
            )
        )

    return YamlValidationResult(
        valid=result.valid,
        errors=result.errors,
        warnings=new_warnings,
        unknown_exercises=unknown_exercises,
    )


async def _auto_create_unknown_exercises(
    raw: dict[str, object],
    db: AsyncSession,
) -> list[str]:
    """Create ExerciseModel entries for any unknown exercise_name values.

    Returns the list of newly created exercise names.
    """
    exercise_refs = extract_exercise_names(raw)
    if not exercise_refs:
        return []

    db_result = await db.execute(select(ExerciseModel.name))
    known_set = {str(n).lower() for n in db_result.scalars().all()}

    created: list[str] = []
    for name, _ in exercise_refs:
        if name.lower() not in known_set:
            exercise = ExerciseModel(
                name=name,
                category="drills",
                is_custom=True,
                is_favorite=False,
            )
            db.add(exercise)
            known_set.add(name.lower())
            created.append(name)

    if created:
        await db.flush()
    return created


def _replace_in_run_details(rd: object, replacements: dict[str, str]) -> None:
    """Replace exercise_name values in a run_details block (in-place)."""
    if not isinstance(rd, dict):
        return
    intervals = rd.get("intervals")
    if not isinstance(intervals, list):
        return
    for interval in intervals:
        if isinstance(interval, dict):
            ex_name = interval.get("exercise_name")
            if ex_name and str(ex_name) in replacements:
                interval["exercise_name"] = replacements[str(ex_name)]


def _apply_exercise_replacements(
    raw: dict[str, object],
    replacements: dict[str, str],
) -> None:
    """Replace exercise_name values in a parsed YAML dict (in-place).

    Supports both current sessions[] format and legacy flat format.
    """
    phases = raw.get("phases")
    if not isinstance(phases, list):
        return
    for phase in phases:
        if not isinstance(phase, dict):
            continue
        wt = phase.get("weekly_template")
        if not isinstance(wt, list):
            continue
        for day_entry in wt:
            if not isinstance(day_entry, dict):
                continue
            # Current format: sessions[]
            sessions = day_entry.get("sessions")
            if isinstance(sessions, list):
                for session in sessions:
                    if isinstance(session, dict):
                        _replace_in_run_details(session.get("run_details"), replacements)
            else:
                # Legacy flat format
                _replace_in_run_details(day_entry.get("run_details"), replacements)


def _migrate_run_details(rd: dict[str, Any]) -> dict[str, Any]:
    """Auto-migrate legacy types in run_details."""
    rd = dict(rd)
    if rd.get("run_type") and str(rd["run_type"]) in SESSION_TYPE_MIGRATION:
        rd["run_type"] = SESSION_TYPE_MIGRATION[str(rd["run_type"])]
    intervals = rd.get("intervals")
    if isinstance(intervals, list):
        migrated: list[dict[str, Any]] = []
        for iv in intervals:
            if isinstance(iv, dict) and iv.get("type"):
                seg_t = str(iv["type"])
                if seg_t in SEGMENT_TYPE_MIGRATION:
                    iv = dict(iv)
                    iv["type"] = SEGMENT_TYPE_MIGRATION[seg_t]
            migrated.append(iv)
        rd["intervals"] = migrated
    return rd


def _map_yaml_day_entry(day_entry: dict[str, Any]) -> dict[str, Any]:
    """Map a single YAML day entry to PhaseWeeklyTemplateDayEntry format.

    Supports both current sessions[] format and legacy flat format.
    """
    # Detect format: current uses "day_of_week", legacy uses "day"
    day_of_week = day_entry.get("day_of_week", day_entry.get("day", 0))
    is_rest = day_entry.get("is_rest_day", day_entry.get("rest", False))
    notes = day_entry.get("notes")

    # Current format: sessions[] already present
    sessions_raw = day_entry.get("sessions")
    if isinstance(sessions_raw, list) and not is_rest:
        sessions = []
        for s in sessions_raw:
            if not isinstance(s, dict):
                continue
            s = dict(s)
            # Auto-migrate legacy run_type in session
            if s.get("run_type") and str(s["run_type"]) in SESSION_TYPE_MIGRATION:
                s["run_type"] = SESSION_TYPE_MIGRATION[str(s["run_type"])]
            rd = s.get("run_details")
            if isinstance(rd, dict):
                s["run_details"] = _migrate_run_details(rd)
            sessions.append(s)
        return {
            "day_of_week": day_of_week,
            "is_rest_day": bool(is_rest),
            "sessions": sessions,
            "notes": notes,
        }

    # Legacy flat format: type/run_type/run_details on day level
    training_type = day_entry.get("type") if not is_rest else None
    run_type = day_entry.get("run_type") if training_type == "running" else None

    if run_type and str(run_type) in SESSION_TYPE_MIGRATION:
        run_type = SESSION_TYPE_MIGRATION[str(run_type)]

    rd = day_entry.get("run_details")
    if isinstance(rd, dict):
        rd = _migrate_run_details(rd)

    return {
        "day_of_week": day_of_week,
        "training_type": training_type,
        "is_rest_day": bool(is_rest),
        "run_type": run_type,
        "template_id": None,
        "notes": notes,
        "run_details": rd if isinstance(rd, dict) else day_entry.get("run_details"),
    }


def _yaml_to_plan_create(data: dict[str, Any]) -> dict[str, Any]:  # noqa: C901  # TODO: E16 Refactoring
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

            # Convert YAML weekly_template list to PhaseWeeklyTemplate
            if "weekly_template" in mapped and isinstance(mapped["weekly_template"], list):
                days = []
                for day_entry in mapped["weekly_template"]:
                    if not isinstance(day_entry, dict):
                        continue
                    days.append(_map_yaml_day_entry(day_entry))
                mapped["weekly_template"] = {"days": days}

            result["phases"].append(mapped)

    return result


_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "static" / "template-trainingsplan.yaml"


@router.get("/template")
async def get_template_yaml() -> FileResponse:
    """Download a YAML template file for training plan import."""
    if not _TEMPLATE_PATH.exists():
        raise HTTPException(status_code=404, detail="Template-Datei nicht gefunden.")
    return FileResponse(
        path=str(_TEMPLATE_PATH),
        media_type="application/x-yaml",
        filename="template-trainingsplan.yaml",
    )


@router.post("/validate-yaml", response_model=YamlValidationResult)
async def validate_yaml_endpoint(
    yaml_file: UploadFile = File(..., description="YAML-Trainingsplan (.yaml/.yml)"),
    db: AsyncSession = Depends(get_db),
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

    result = validate_yaml_plan(raw)

    # DB-aware exercise name check (only if basic validation passed)
    if result.valid:
        result = await _check_unknown_exercises(raw, result, db)

    return result


@router.post("/import", response_model=TrainingPlanResponse, status_code=201)
async def import_plan_from_yaml(
    yaml_file: UploadFile = File(..., description="YAML-Trainingsplan (.yaml/.yml)"),
    exercise_replacements: Optional[str] = Form(
        None,
        description='JSON mapping {"OldName": "ExistingName"} for exercise name substitutions',
    ),
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

    # Apply exercise name replacements from the validation UI
    replacements: dict[str, str] = {}
    if exercise_replacements:
        with contextlib.suppress(json.JSONDecodeError, ValueError):
            replacements = json.loads(exercise_replacements)
    if replacements:
        _apply_exercise_replacements(raw, replacements)

    # Auto-create unknown exercises in the library
    await _auto_create_unknown_exercises(raw, db)

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
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Validierungsfehler:\n{_format_pydantic_errors(exc)}",
        ) from None
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


# --- Shared Generation Helpers ---
# Used by generate_plan_weeks() endpoint and auto-generation triggers.


async def _load_generation_context(
    db: AsyncSession,
    plan_id: int,
) -> tuple[TrainingPlanModel, list[TrainingPhaseModel], Optional[RaceGoalModel], list[int]]:
    """Load plan, phases, goal, and rest_days for weekly plan generation.

    Raises HTTPException if plan not found or has no phases.
    Returns (plan, phases, goal, rest_days).
    """
    result = await db.execute(select(TrainingPlanModel).where(TrainingPlanModel.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Trainingsplan nicht gefunden")

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

    goal: Optional[RaceGoalModel] = None
    if plan.goal_id:
        goal_result = await db.execute(
            select(RaceGoalModel).where(RaceGoalModel.id == plan.goal_id)
        )
        goal = goal_result.scalar_one_or_none()

    rest_days = [6]  # Default: Sunday
    if plan.weekly_structure_json:
        try:
            ws = json.loads(str(plan.weekly_structure_json))
            rest_days = ws.get("rest_days", [6])
        except (json.JSONDecodeError, ValueError):
            pass

    return plan, phases, goal, rest_days


async def _get_edited_weeks(db: AsyncSession, plan_id: int) -> set[date]:
    """Get week_start dates that have at least one manually edited day."""
    edited_result = await db.execute(
        select(WeeklyPlanDayModel.week_start)
        .where(
            WeeklyPlanDayModel.plan_id == plan_id,
            WeeklyPlanDayModel.edited.is_(True),
        )
        .distinct()
    )
    return {row[0] for row in edited_result.all()}


async def _persist_generated_weeks(
    db: AsyncSession,
    plan_id: int,
    weekly_plans: list[tuple[date, list]],
    skip_weeks: set[date] | None = None,
) -> int:
    """Delete old and insert new weekly plan days + sessions.

    Skips weeks in skip_weeks (e.g. edited weeks for unedited_only strategy).
    Does NOT commit — caller is responsible for commit.
    Returns number of weeks generated.
    """
    if skip_weeks is None:
        skip_weeks = set()

    weeks_to_generate = [ws for ws, _ in weekly_plans if ws not in skip_weeks]

    # Delete ALL existing days for target weeks (regardless of plan_id).
    # This handles: same plan re-generation, orphaned entries from deleted
    # plans, and manual entries — preventing UniqueConstraint violations.
    if weeks_to_generate:
        old_days_result = await db.execute(
            select(WeeklyPlanDayModel).where(
                WeeklyPlanDayModel.week_start.in_(weeks_to_generate),
            )
        )
        for old_day in old_days_result.scalars().all():
            old_sessions = await db.execute(
                select(PlannedSessionModel).where(PlannedSessionModel.day_id == old_day.id)
            )
            for old_sess in old_sessions.scalars().all():
                await db.delete(old_sess)
            await db.delete(old_day)

    await db.flush()

    # Insert new days + sessions
    weeks_generated = 0
    for week_start, entries in weekly_plans:
        if week_start in skip_weeks:
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
                exercises_str: Optional[str] = None
                if sess.exercises is not None:
                    exercises_str = json.dumps([ex.model_dump() for ex in sess.exercises])
                db_sess = PlannedSessionModel(
                    day_id=db_day.id,
                    position=sess.position,
                    training_type=sess.training_type,
                    template_id=sess.template_id,
                    run_details_json=run_details_str,
                    exercises_json=exercises_str,
                    notes=sess.notes,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(db_sess)
        weeks_generated += 1

    return weeks_generated


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

    plan, phases, goal, rest_days = await _load_generation_context(db, plan_id)
    weekly_plans = generate_weekly_plans(plan, phases, rest_days, goal)

    skip_weeks = await _get_edited_weeks(db, plan_id) if strategy == "unedited_only" else set()
    weeks_generated = await _persist_generated_weeks(db, plan_id, weekly_plans, skip_weeks)

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
async def update_plan(  # noqa: C901, PLR0912, PLR0915  # TODO: E16 Refactoring
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
        plan.name = data.name
    if data.description is not None:
        _track("description", plan.description, data.description)
        plan.description = data.description
    if data.start_date is not None:
        _track("start_date", plan.start_date, data.start_date)
        plan.start_date = data.start_date
    if data.end_date is not None:
        _track("end_date", plan.end_date, data.end_date)
        plan.end_date = data.end_date
    if data.target_event_date is not None:
        _track("target_event_date", plan.target_event_date, data.target_event_date)
        plan.target_event_date = data.target_event_date
    if data.weekly_structure is not None:
        _track(
            "weekly_structure",
            plan.weekly_structure_json,
            json.dumps(data.weekly_structure.model_dump()),
        )
        plan.weekly_structure_json = json.dumps(data.weekly_structure.model_dump())
    old_status = str(plan.status)
    if data.status is not None:
        _track("status", plan.status, data.status)
        plan.status = data.status

    # S09: Update goal link
    if data.goal_id is not None:
        old_goal_id = plan.goal_id
        _track("goal_id", old_goal_id, data.goal_id)
        plan.goal_id = data.goal_id

        # Remove old bidirectional link
        if old_goal_id:
            old_goal_result = await db.execute(
                select(RaceGoalModel).where(RaceGoalModel.id == old_goal_id)
            )
            old_goal = old_goal_result.scalar_one_or_none()
            if old_goal and old_goal.training_plan_id == plan.id:
                old_goal.training_plan_id = None

        # Set new bidirectional link
        if data.goal_id:
            new_goal_result = await db.execute(
                select(RaceGoalModel).where(RaceGoalModel.id == data.goal_id)
            )
            new_goal = new_goal_result.scalar_one_or_none()
            if new_goal:
                new_goal.training_plan_id = plan.id

    category = "structure" if changed_structure else "meta" if changed_meta else "meta"

    plan.updated_at = datetime.utcnow()
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

    # Auto-generate weekly plans on activation
    auto_gen_result: Optional[AutoGenerationResult] = None
    new_status = str(plan.status)
    if new_status == "active" and old_status != "active":
        # Check prerequisites: plan needs phases + start/end date
        phase_count_result = await db.execute(
            select(func.count(TrainingPhaseModel.id)).where(
                TrainingPhaseModel.training_plan_id == plan_id
            )
        )
        has_phases = (phase_count_result.scalar() or 0) > 0
        has_dates = plan.start_date is not None and plan.end_date is not None

        if has_phases and has_dates:
            strategy = "all" if old_status == "draft" else "unedited_only"
            gen_plan, gen_phases, gen_goal, gen_rest_days = await _load_generation_context(
                db, plan_id
            )
            weekly_plans = generate_weekly_plans(gen_plan, gen_phases, gen_rest_days, gen_goal)

            skip_weeks = (
                await _get_edited_weeks(db, plan_id) if strategy == "unedited_only" else set()
            )
            weeks_generated = await _persist_generated_weeks(db, plan_id, weekly_plans, skip_weeks)

            await log_plan_change(
                db,
                plan_id,
                "weekly_auto_generated",
                f"{weeks_generated} Wochenpläne automatisch generiert",
                details={
                    "category": "technical",
                    "source": "system",
                    "trigger": "plan_activation",
                    "strategy": strategy,
                    "weeks_generated": weeks_generated,
                    "total_weeks": len(weekly_plans),
                },
            )

            auto_gen_result = AutoGenerationResult(
                weeks_generated=weeks_generated,
                total_weeks=len(weekly_plans),
            )

    await db.commit()
    await db.refresh(plan)
    return await _plan_to_response(db, plan, auto_generation_result=auto_gen_result)


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
            select(RaceGoalModel).where(RaceGoalModel.id == plan.goal_id)
        )
        goal = goal_result.scalar_one_or_none()
        if goal and goal.training_plan_id == plan.id:
            goal.training_plan_id = None

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
                session_ids.append(session.id)
                await db.delete(session)
            # Clear workout references to deleted sessions
            if session_ids:
                workout_result = await db.execute(
                    select(WorkoutModel).where(WorkoutModel.planned_entry_id.in_(session_ids))
                )
                for workout in workout_result.scalars().all():
                    workout.planned_entry_id = None
            await db.delete(day)
    else:
        # Detach weekly plan days from deleted plan (prevent orphaned plan_id)
        await db.execute(
            update(WeeklyPlanDayModel)
            .where(WeeklyPlanDayModel.plan_id == plan_id)
            .values(plan_id=None)
        )

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
async def update_phase(  # noqa: C901, PLR0912, PLR0915  # TODO: E16 Refactoring
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
        phase.name = data.name
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
        phase.phase_type = data.phase_type
    if data.start_week is not None:
        phase_changes.append(
            {
                "field": "start_week",
                "from": phase.start_week,
                "to": data.start_week,
                "label": _PHASE_LABELS["start_week"],
            }
        )
        has_structure_change = True
        phase.start_week = data.start_week
    if data.end_week is not None:
        phase_changes.append(
            {
                "field": "end_week",
                "from": phase.end_week,
                "to": data.end_week,
                "label": _PHASE_LABELS["end_week"],
            }
        )
        has_structure_change = True
        phase.end_week = data.end_week
    if data.focus is not None:
        has_content_change = True
        phase.focus_json = json.dumps(data.focus.model_dump())
    if data.target_metrics is not None:
        has_content_change = True
        phase.target_metrics_json = json.dumps(data.target_metrics.model_dump())
    if data.weekly_template is not None:
        has_content_change = True
        phase.weekly_template_json = json.dumps(data.weekly_template.model_dump())
    if data.weekly_templates is not None:
        has_content_change = True
        phase.weekly_templates_json = json.dumps(data.weekly_templates.model_dump())
    if data.notes is not None:
        phase_changes.append(
            {
                "field": "notes",
                "from": str(phase.notes) if phase.notes else None,
                "to": data.notes,
                "label": _PHASE_LABELS["notes"],
            }
        )
        phase.notes = data.notes

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

    # Auto-regenerate weekly plans when template changes on active plan
    auto_regen: Optional[AutoRegenerationResult] = None
    if has_content_change:
        plan_result = await db.execute(
            select(TrainingPlanModel).where(TrainingPlanModel.id == plan_id)
        )
        parent_plan = plan_result.scalar_one_or_none()
        if parent_plan and str(parent_plan.status) == "active" and parent_plan.start_date:
            from datetime import timedelta

            # Compute week_start dates for this phase
            plan_start = date(
                parent_plan.start_date.year,
                parent_plan.start_date.month,
                parent_plan.start_date.day,
            )
            plan_start = plan_start - timedelta(days=plan_start.weekday())  # Monday

            phase_start_week = phase.start_week
            phase_end_week = phase.end_week
            phase_week_starts: list[date] = []
            for wn in range(phase_start_week, phase_end_week + 1):
                ws = plan_start + timedelta(weeks=wn - 1)
                phase_week_starts.append(ws)

            # Filter: only future weeks (week_start >= Monday of current week)
            today = date.today()
            current_monday = today - timedelta(days=today.weekday())
            future_weeks = {ws for ws in phase_week_starts if ws >= current_monday}

            if future_weeks:
                # Get edited weeks
                edited_weeks = await _get_edited_weeks(db, plan_id)
                edited_in_scope = future_weeks & edited_weeks
                weeks_to_regen = future_weeks - edited_weeks

                if weeks_to_regen:
                    # Full generation (reuses same logic)
                    gen_plan, gen_phases, gen_goal, gen_rest_days = await _load_generation_context(
                        db, plan_id
                    )
                    weekly_plans = generate_weekly_plans(
                        gen_plan, gen_phases, gen_rest_days, gen_goal
                    )

                    # Only persist weeks that belong to this phase and are in scope
                    phase_plans = [
                        (ws, entries) for ws, entries in weekly_plans if ws in weeks_to_regen
                    ]
                    weeks_regenerated = await _persist_generated_weeks(db, plan_id, phase_plans)

                    past_weeks = len(phase_week_starts) - len(future_weeks)

                    await log_plan_change(
                        db,
                        plan_id,
                        "weekly_auto_generated",
                        f"{weeks_regenerated} Wochenpläne nach Template-Änderung aktualisiert",
                        details={
                            "category": "technical",
                            "source": "system",
                            "trigger": "template_change",
                            "phase_id": phase_id,
                            "weeks_regenerated": weeks_regenerated,
                            "weeks_skipped_edited": len(edited_in_scope),
                            "weeks_skipped_past": past_weeks,
                        },
                    )

                    auto_regen = AutoRegenerationResult(
                        weeks_regenerated=weeks_regenerated,
                        weeks_skipped_edited=len(edited_in_scope),
                        weeks_skipped_past=past_weeks,
                    )

    await db.commit()
    await db.refresh(phase)
    return _phase_to_response(phase, auto_regeneration=auto_regen)


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
        base_filter = base_filter & (PlanChangeLogModel.category == category)

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

    entry.reason = data.reason
    await db.commit()
    await db.refresh(entry)
    return _changelog_to_response(entry)
