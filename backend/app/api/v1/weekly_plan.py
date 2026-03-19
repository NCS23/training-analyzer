"""API routes for Weekly Plan (Issue #26, #27, #28, E17-S02)."""

import json
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.training_plans import log_plan_change
from app.infrastructure.database.models import (
    PlanChangeLogModel,
    PlannedSessionModel,
    SessionTemplateModel,
    TrainingPhaseModel,
    TrainingPlanModel,
    WeeklyPlanDayModel,
    WorkoutModel,
)
from app.infrastructure.database.session import get_db
from app.models.exercise import TemplateExercise
from app.models.training_plan import (
    PhaseWeeklyTemplate,
    PhaseWeeklyTemplateDayEntry,
    PhaseWeeklyTemplateSessionEntry,
)
from app.models.weekly_plan import (
    ActualSession,
    ApplyRecommendationsRequest,
    ApplyRecommendationsResponse,
    CategoryTonnage,
    ComplianceDayEntry,
    ComplianceResponse,
    PlannedSession,
    PlannedSessionOption,
    RunDetails,
    SyncToPlanRequest,
    SyncToPlanResponse,
    UndoResponse,
    UndoStatusResponse,
    WeeklyPlanEntry,
    WeeklyPlanResponse,
    WeeklyPlanSaveRequest,
    WeeklyStrengthSummary,
)
from app.services.tonnage_calculator import (
    calculate_category_tonnage,
    calculate_strength_metrics,
)

router = APIRouter(prefix="/weekly-plan")

DAY_NAMES = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def _monday_of_week(d: date) -> date:
    """Return the Monday of the week containing `d`."""
    return d - timedelta(days=d.weekday())


async def _get_template_names(
    db: AsyncSession,
    template_ids: list[int],
) -> dict[int, str]:
    """Fetch template names for a list of template IDs."""
    if not template_ids:
        return {}
    result = await db.execute(
        select(SessionTemplateModel.id, SessionTemplateModel.name).where(
            SessionTemplateModel.id.in_(template_ids)
        )
    )
    return {row.id: str(row.name) for row in result.all()}


async def _get_template_exercise_counts(
    db: AsyncSession,
    template_ids: list[int],
) -> dict[int, int]:
    """Fetch exercise counts from templates (#149)."""
    if not template_ids:
        return {}
    result = await db.execute(
        select(SessionTemplateModel.id, SessionTemplateModel.exercises_json).where(
            SessionTemplateModel.id.in_(template_ids)
        )
    )
    counts: dict[int, int] = {}
    for row in result.all():
        ex_json = row.exercises_json
        if ex_json:
            try:
                exercises = json.loads(str(ex_json))
                counts[row.id] = len(exercises)
            except (json.JSONDecodeError, TypeError):
                counts[row.id] = 0
        else:
            counts[row.id] = 0
    return counts


def _parse_run_details(raw: Optional[str]) -> Optional[RunDetails]:
    """Parse run_details_json string to RunDetails model."""
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return RunDetails(**data)
    except (json.JSONDecodeError, ValueError):
        return None


def _parse_exercises(raw: Optional[str]) -> Optional[list[TemplateExercise]]:
    """Parse exercises_json string to list of TemplateExercise."""
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return [TemplateExercise(**ex) for ex in data]
    except (json.JSONDecodeError, ValueError):
        return None


async def _load_days_with_sessions(
    db: AsyncSession,
    week_start: date,
) -> dict[int, tuple[WeeklyPlanDayModel, list[PlannedSessionModel]]]:
    """Load all days and their sessions for a week. Returns {day_of_week: (day, sessions)}."""
    day_result = await db.execute(
        select(WeeklyPlanDayModel)
        .where(WeeklyPlanDayModel.week_start == week_start)
        .order_by(WeeklyPlanDayModel.day_of_week)
    )
    days = {int(d.day_of_week): d for d in day_result.scalars().all()}

    if not days:
        return {}

    day_ids = [d.id for d in days.values()]
    session_result = await db.execute(
        select(PlannedSessionModel)
        .where(PlannedSessionModel.day_id.in_(day_ids))
        .order_by(PlannedSessionModel.day_id, PlannedSessionModel.position)
    )
    all_sessions = session_result.scalars().all()

    # Group sessions by day_id
    sessions_by_day_id: dict[int, list[PlannedSessionModel]] = {}
    for s in all_sessions:
        did = int(s.day_id)
        if did not in sessions_by_day_id:
            sessions_by_day_id[did] = []
        sessions_by_day_id[did].append(s)

    result: dict[int, tuple[WeeklyPlanDayModel, list[PlannedSessionModel]]] = {}
    for dow, day in days.items():
        day_id = day.id
        result[dow] = (day, sessions_by_day_id.get(day_id, []))

    return result


def _build_week_snapshot(
    week_start: date,
    old_data: dict[int, tuple[WeeklyPlanDayModel, list[PlannedSessionModel]]],
    phase_id: int | None = None,
    phase_templates_json: str | None = None,
) -> dict:
    """Build a complete snapshot of the week's state for undo."""
    days: list[dict] = []
    for dow in range(7):
        if dow not in old_data:
            continue
        day, sessions = old_data[dow]
        days.append(
            {
                "day_of_week": dow,
                "is_rest_day": bool(day.is_rest_day),
                "notes": day.notes,
                "plan_id": day.plan_id,
                "edited": bool(day.edited),
                "sessions": [
                    {
                        "position": int(s.position),
                        "training_type": str(s.training_type),
                        "template_id": s.template_id,
                        "run_details_json": s.run_details_json,
                        "exercises_json": s.exercises_json,
                        "notes": s.notes,
                        "status": str(s.status) if s.status else "active",
                    }
                    for s in sorted(sessions, key=lambda x: int(x.position))
                ],
            }
        )
    return {
        "week_start": str(week_start),
        "days": days,
        "phase_id": phase_id,
        "phase_weekly_templates_json": phase_templates_json,
    }


async def _load_linked_phase_template(
    db: AsyncSession,
    old_data: dict[int, tuple[WeeklyPlanDayModel, list[PlannedSessionModel]]],
    week_start: date,
) -> tuple[int | None, str | None]:
    """Load the phase template JSON linked to this week (for undo snapshot)."""
    plan_id: int | None = None
    for day, _sessions in old_data.values():
        if day.plan_id:
            plan_id = int(day.plan_id)
            break

    if not plan_id:
        return None, None

    plan = await db.get(TrainingPlanModel, plan_id)
    if not plan:
        return None, None

    plan_start = plan.start_date
    plan_start_monday = plan_start - timedelta(days=plan_start.weekday())
    week_number = ((week_start - plan_start_monday).days // 7) + 1

    result = await db.execute(
        select(TrainingPhaseModel).where(
            TrainingPhaseModel.training_plan_id == plan_id,
            TrainingPhaseModel.start_week <= week_number,
            TrainingPhaseModel.end_week >= week_number,
        )
    )
    phase = result.scalar_one_or_none()
    if not phase:
        return None, None

    return phase.id, phase.weekly_templates_json


def _build_entry_from_db(
    day_of_week: int,
    day: Optional[WeeklyPlanDayModel],
    sessions: list[PlannedSessionModel],
    template_names: dict[int, str],
) -> WeeklyPlanEntry:
    """Build a WeeklyPlanEntry from DB models."""
    if day is None:
        return WeeklyPlanEntry(day_of_week=day_of_week)

    session_list: list[PlannedSession] = []
    for s in sessions:
        run_details = _parse_run_details(str(s.run_details_json) if s.run_details_json else None)
        exercises = _parse_exercises(str(s.exercises_json) if s.exercises_json else None)
        tid = s.template_id if s.template_id else None
        session_list.append(
            PlannedSession(
                id=s.id,
                position=int(s.position),
                training_type=str(s.training_type),
                template_id=tid,
                template_name=template_names.get(tid) if tid else None,
                notes=str(s.notes) if s.notes else None,
                run_details=run_details,
                exercises=exercises,
                status=str(s.status) if s.status else "active",
            )
        )

    return WeeklyPlanEntry(
        day_of_week=day_of_week,
        is_rest_day=bool(day.is_rest_day),
        notes=str(day.notes) if day.notes else None,
        sessions=session_list,
        plan_id=int(day.plan_id) if day.plan_id else None,
        edited=bool(day.edited),
    )


@router.get("", response_model=WeeklyPlanResponse)
async def get_weekly_plan(
    week_start: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
) -> WeeklyPlanResponse:
    """Get the weekly plan for a given week (defaults to current week)."""
    if week_start is None:
        week_start = _monday_of_week(date.today())
    else:
        week_start = _monday_of_week(week_start)

    days_data = await _load_days_with_sessions(db, week_start)

    # Collect template IDs for name lookup
    template_ids: list[int] = []
    for _day, sessions in days_data.values():
        for s in sessions:
            if s.template_id is not None:
                template_ids.append(s.template_id)
    template_names = await _get_template_names(db, template_ids)

    # Build full 7-day response
    entries: list[WeeklyPlanEntry] = []
    for dow in range(7):
        if dow in days_data:
            day, sessions = days_data[dow]
            entries.append(_build_entry_from_db(dow, day, sessions, template_names))
        else:
            entries.append(WeeklyPlanEntry(day_of_week=dow))

    # Wetter-Forecast für die Woche anhängen (Background, non-blocking)
    try:
        from app.services.weather_forecast_service import weather_forecast_service

        forecasts = await weather_forecast_service.get_week_forecast(week_start, db)
        for entry in entries:
            if entry.day_of_week in forecasts:
                entry.weather = forecasts[entry.day_of_week]
    except Exception:
        pass  # Graceful degradation — Wochenplan funktioniert ohne Wetter

    return WeeklyPlanResponse(week_start=week_start, entries=entries)


def _sessions_changed(  # noqa: PLR0911  # TODO: E16 Refactoring
    old_sessions: list[PlannedSessionModel],
    new_sessions: list[PlannedSession],
) -> bool:
    """Compare old DB sessions with new request sessions to detect edits."""
    if len(old_sessions) != len(new_sessions):
        return True
    for old_s, new_s in zip(
        sorted(old_sessions, key=lambda s: int(s.position)),
        sorted(new_sessions, key=lambda s: s.position),
    ):
        if str(old_s.training_type) != new_s.training_type:
            return True
        if (old_s.template_id or None) != (new_s.template_id or None):
            return True
        if str(old_s.notes or "") != str(new_s.notes or ""):
            return True
        old_status = str(old_s.status) if old_s.status else "active"
        if old_status != new_s.status:
            return True
        # Compare run_details
        old_rd = str(old_s.run_details_json) if old_s.run_details_json else None
        new_rd = json.dumps(new_s.run_details.model_dump()) if new_s.run_details else None
        if (old_rd or None) != (new_rd or None):
            return True
    return False


def _has_content_changed(
    old_day: WeeklyPlanDayModel,
    old_sessions: list[PlannedSessionModel],
    new_entry: WeeklyPlanEntry,
) -> bool:
    """Compare old DB state with new request entry to detect edits."""
    if bool(old_day.is_rest_day) != new_entry.is_rest_day:
        return True
    if str(old_day.notes or "") != str(new_entry.notes or ""):
        return True
    return _sessions_changed(old_sessions, new_entry.sessions)


_FIELD_LABELS_DAY: dict[str, str] = {
    "is_rest_day": "Ruhetag",
    "notes": "Notizen (Tag)",
    "session_count": "Anzahl Sessions",
    "training_type": "Trainingstyp",
    "template_id": "Vorlage",
    "session_notes": "Notizen (Session)",
    "run_type": "Lauftyp",
    "target_duration_minutes": "Dauer (Ziel)",
    "target_pace_min": "Ziel-Pace (schnell)",
    "target_pace_max": "Ziel-Pace (langsam)",
    "target_hr_min": "Herzfrequenz (min)",
    "target_hr_max": "Herzfrequenz (max)",
}


def _diff_day_entry(
    old_day: WeeklyPlanDayModel,
    old_sessions: list[PlannedSessionModel],
    new_entry: WeeklyPlanEntry,
) -> list[dict[str, object]]:
    """Return field-level diff between old DB state and new request entry."""
    changes: list[dict[str, object]] = []

    def _add(field: str, from_val: object, to_val: object) -> None:
        if from_val != to_val:
            changes.append(
                {
                    "field": field,
                    "from": from_val,
                    "to": to_val,
                    "label": _FIELD_LABELS_DAY.get(field, field),
                }
            )

    _add("is_rest_day", bool(old_day.is_rest_day), new_entry.is_rest_day)
    _add("notes", old_day.notes or None, new_entry.notes)
    _add("session_count", len(old_sessions), len(new_entry.sessions))

    # Compare sessions (positional)
    max_len = max(len(old_sessions), len(new_entry.sessions))
    sorted_old = sorted(old_sessions, key=lambda s: int(s.position))
    sorted_new = sorted(new_entry.sessions, key=lambda s: s.position)

    for i in range(max_len):
        prefix = f"session[{i}]."
        old_s = sorted_old[i] if i < len(sorted_old) else None
        new_s = sorted_new[i] if i < len(sorted_new) else None

        old_type = str(old_s.training_type) if old_s else None
        new_type = new_s.training_type if new_s else None
        _add(f"{prefix}training_type", old_type, new_type)

        old_tid = int(old_s.template_id) if old_s and old_s.template_id else None
        new_tid = new_s.template_id if new_s else None
        _add(f"{prefix}template_id", old_tid, new_tid)

        # RunDetails diff
        old_rd_str = str(old_s.run_details_json) if old_s and old_s.run_details_json else None
        new_rd_str = (
            json.dumps(new_s.run_details.model_dump()) if new_s and new_s.run_details else None
        )
        if (old_rd_str or None) != (new_rd_str or None):
            old_rd: dict[str, object] = json.loads(old_rd_str) if old_rd_str else {}
            new_rd: dict[str, object] = json.loads(new_rd_str) if new_rd_str else {}
            for field in (
                "run_type",
                "target_duration_minutes",
                "target_pace_min",
                "target_pace_max",
                "target_hr_min",
                "target_hr_max",
            ):
                _add(f"{prefix}{field}", old_rd.get(field), new_rd.get(field))

    return changes


@router.put("", response_model=WeeklyPlanResponse)
async def save_weekly_plan(  # noqa: C901, PLR0912  # TODO: E16 Refactoring
    data: WeeklyPlanSaveRequest,
    db: AsyncSession = Depends(get_db),
) -> WeeklyPlanResponse:
    """Save/update the weekly plan. Upserts all provided day entries."""
    week_start = _monday_of_week(data.week_start)

    # Validate no duplicate days
    seen_days: set[int] = set()
    for entry in data.entries:
        if entry.day_of_week in seen_days:
            raise HTTPException(
                status_code=422,
                detail=f"Doppelter Tag: {DAY_NAMES[entry.day_of_week]}",
            )
        seen_days.add(entry.day_of_week)

    # Fetch existing days + sessions BEFORE deletion (for plan_id + edited preservation)
    old_data = await _load_days_with_sessions(db, week_start)

    # Capture snapshot for undo (before any deletion)
    undo_phase_id, undo_phase_json = await _load_linked_phase_template(
        db,
        old_data,
        week_start,
    )
    undo_snapshot = (
        _build_week_snapshot(
            week_start,
            old_data,
            undo_phase_id,
            undo_phase_json,
        )
        if old_data
        else None
    )

    # Delete existing sessions then days
    for _day, sessions in old_data.values():
        for s in sessions:
            await db.delete(s)
    for day, _sessions in old_data.values():
        await db.delete(day)
    await db.flush()

    # Insert new days + sessions, preserving plan_id and detecting edits
    for entry in data.entries:
        old = old_data.get(entry.day_of_week)
        old_day = old[0] if old else None
        old_sessions = old[1] if old else []

        plan_id: Optional[int] = None
        edited = False

        if old_day and old_day.plan_id:
            plan_id = old_day.plan_id
            edited = (
                True if _has_content_changed(old_day, old_sessions, entry) else bool(old_day.edited)
            )

        db_day = WeeklyPlanDayModel(
            week_start=week_start,
            day_of_week=entry.day_of_week,
            is_rest_day=entry.is_rest_day,
            notes=entry.notes,
            plan_id=plan_id,
            edited=edited,
        )
        db.add(db_day)
        await db.flush()  # Get db_day.id

        for session in entry.sessions:
            run_details_str: Optional[str] = None
            if session.run_details is not None:
                run_details_str = json.dumps(session.run_details.model_dump())

            exercises_str: Optional[str] = None
            if session.exercises is not None:
                exercises_str = json.dumps([ex.model_dump() for ex in session.exercises])

            db_session = PlannedSessionModel(
                day_id=db_day.id,
                position=session.position,
                training_type=session.training_type,
                template_id=session.template_id,
                run_details_json=run_details_str,
                exercises_json=exercises_str,
                notes=session.notes,
                status=session.status,
            )
            db.add(db_session)

    # Log manual edits to plan-linked entries with day-level diffs
    changed_plan_days: dict[int, list[dict[str, object]]] = {}
    for entry in data.entries:
        old = old_data.get(entry.day_of_week)
        old_day = old[0] if old else None
        old_sessions = old[1] if old else []

        if old_day and old_day.plan_id and _has_content_changed(old_day, old_sessions, entry):
            pid = old_day.plan_id
            day_changes = _diff_day_entry(old_day, old_sessions, entry)
            if day_changes:
                if pid not in changed_plan_days:
                    changed_plan_days[pid] = []
                changed_plan_days[pid].append(
                    {
                        "day_of_week": entry.day_of_week,
                        "day_name": DAY_NAMES[entry.day_of_week],
                        "field_changes": day_changes,
                    }
                )
    for pid, changed_days in changed_plan_days.items():
        count = len(changed_days)
        details: dict = {
            "category": "content",
            "source": "user",
            "week_start": str(week_start),
            "changed_days": changed_days,
        }
        if undo_snapshot:
            details["snapshot_before"] = undo_snapshot
            details["undoable"] = True
        await log_plan_change(
            db,
            pid,
            "manual_edit",
            f"Wochenplan {week_start}: {count} Eintraege bearbeitet",
            details=details,
        )

    await db.commit()

    # Return the saved plan
    return await get_weekly_plan(week_start=week_start, db=db)


@router.delete("")
async def clear_weekly_plan(
    week_start: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, bool]:
    """Clear all entries for a given week."""
    if week_start is None:
        week_start = _monday_of_week(date.today())
    else:
        week_start = _monday_of_week(week_start)

    # Load days to get IDs for session cleanup
    day_result = await db.execute(
        select(WeeklyPlanDayModel).where(WeeklyPlanDayModel.week_start == week_start)
    )
    days = day_result.scalars().all()

    if days:
        day_ids = [d.id for d in days]
        session_result = await db.execute(
            select(PlannedSessionModel).where(PlannedSessionModel.day_id.in_(day_ids))
        )
        for s in session_result.scalars().all():
            await db.delete(s)
        for d in days:
            await db.delete(d)

    await db.commit()
    return {"success": True}


def _effective_training_type(w: WorkoutModel) -> Optional[str]:
    """Get effective training type (override > auto)."""
    if w.training_type_override:
        return str(w.training_type_override)
    if w.training_type_auto:
        return str(w.training_type_auto)
    return None


def _determine_status(  # noqa: PLR0911  # TODO: E16 Refactoring
    planned_types: list[str],
    is_rest_day: bool,
    sessions: list[WorkoutModel],
) -> str:
    """Determine compliance status for a day.

    Multi-session logic (E17-S07):
    - completed: every planned training_type has at least one matching workout
    - partial: at least one planned type matched, but not all
    - off_target: plan exists + sessions exist but no type matches
    - missed: plan exists but no sessions
    """
    has_plan = len(planned_types) > 0 or is_rest_day
    has_sessions = len(sessions) > 0

    if not has_plan and not has_sessions:
        return "empty"

    if not has_plan and has_sessions:
        return "unplanned"

    if is_rest_day:
        return "rest_ok" if not has_sessions else "off_target"

    if has_plan and not has_sessions:
        return "missed"

    # Both plan and sessions exist — check per-type match
    type_map = {"strength": "strength", "running": "running"}
    matched = 0
    for pt in planned_types:
        expected = type_map.get(pt, pt)
        if any(str(s.workout_type) == expected for s in sessions):
            matched += 1

    if matched == len(planned_types):
        return "completed"
    if matched > 0:
        return "partial"
    return "off_target"


@router.get("/compliance", response_model=ComplianceResponse)
async def get_compliance(  # noqa: C901, PLR0912, PLR0915  # TODO: E16 Refactoring
    week_start: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
) -> ComplianceResponse:
    """Get compliance tracking for a given week (plan vs. actual sessions)."""
    if week_start is None:
        week_start = _monday_of_week(date.today())
    else:
        week_start = _monday_of_week(week_start)

    week_end = week_start + timedelta(days=6)

    # Fetch plan days + sessions
    days_data = await _load_days_with_sessions(db, week_start)

    # Fetch all workouts for this week
    session_result = await db.execute(
        select(WorkoutModel)
        .where(
            WorkoutModel.date >= datetime.combine(week_start, datetime.min.time()),
            WorkoutModel.date <= datetime.combine(week_end, datetime.max.time()),
        )
        .order_by(WorkoutModel.date)
    )
    all_workouts = session_result.scalars().all()

    # Group workouts by day_of_week
    workouts_by_day: dict[int, list[WorkoutModel]] = {d: [] for d in range(7)}
    for w in all_workouts:
        workout_dt = w.date
        w_date = workout_dt.date() if isinstance(workout_dt, datetime) else workout_dt
        day_idx = (w_date - week_start).days
        if 0 <= day_idx <= 6:
            workouts_by_day[day_idx].append(w)

    # --- #149: Resolve planned strength template info ---
    # Build map: planned_session_id -> (template_name, template_id)
    planned_session_template_map: dict[int, tuple[str, int | None]] = {}
    strength_template_ids: list[int] = []
    for _dow, (_day, db_sessions) in days_data.items():
        for s in db_sessions:
            if str(s.training_type) == "strength" and s.template_id:
                tid = s.template_id
                strength_template_ids.append(tid)

    template_names = await _get_template_names(db, strength_template_ids)
    template_exercise_counts = await _get_template_exercise_counts(db, strength_template_ids)

    for _dow, (_day, db_sessions) in days_data.items():
        for s in db_sessions:
            if str(s.training_type) == "strength":
                s_tid: Optional[int] = s.template_id if s.template_id else None
                tname = template_names.get(s_tid) if s_tid else None
                planned_session_template_map[s.id] = (tname or "", s_tid)

    # Build compliance entries
    entries: list[ComplianceDayEntry] = []
    completed_count = 0
    planned_count = 0
    # Collect all strength workouts for weekly summary
    all_strength_exercises: list[dict[str, object]] = []
    strength_session_count = 0

    for day in range(7):
        day_date = week_start + timedelta(days=day)
        day_workouts = workouts_by_day[day]

        planned_types: list[str] = []
        planned_run_type: Optional[str] = None
        planned_template_name: Optional[str] = None
        planned_exercise_count: Optional[int] = None
        is_rest = False

        if day in days_data:
            db_day, db_sessions = days_data[day]
            is_rest = bool(db_day.is_rest_day)
            for s in db_sessions:
                if str(s.status) == "skipped":
                    continue
                planned_types.append(str(s.training_type))
                if str(s.training_type) == "running" and planned_run_type is None:
                    rd = _parse_run_details(str(s.run_details_json) if s.run_details_json else None)
                    if rd:
                        planned_run_type = rd.run_type
                # #149: First planned strength session's template info
                if str(s.training_type) == "strength" and planned_template_name is None:
                    p_tid: Optional[int] = s.template_id if s.template_id else None
                    if p_tid:
                        planned_template_name = template_names.get(p_tid)
                        planned_exercise_count = template_exercise_counts.get(p_tid)

        has_plan = len(planned_types) > 0 or is_rest
        if has_plan:
            planned_count += 1

        status = _determine_status(planned_types, is_rest, day_workouts)
        if status in ("completed", "rest_ok"):
            completed_count += 1

        # Build actual sessions with strength details (#149)
        actual: list[ActualSession] = []
        for w in day_workouts:
            tonnage_kg: Optional[float] = None
            ex_count: Optional[int] = None
            set_count: Optional[int] = None
            tpl_name: Optional[str] = None

            if str(w.workout_type) == "strength" and w.exercises_json:
                exercises_raw = json.loads(str(w.exercises_json))
                metrics = calculate_strength_metrics(exercises_raw)
                tonnage_kg = metrics["total_tonnage_kg"]
                ex_count = metrics["total_exercises"]
                set_count = metrics["total_sets"]
                # Collect for weekly summary
                all_strength_exercises.extend(exercises_raw)
                strength_session_count += 1

            # Resolve template name via planned_entry_id
            if w.planned_entry_id:
                entry_id = w.planned_entry_id
                if entry_id in planned_session_template_map:
                    tpl_name = planned_session_template_map[entry_id][0] or None

            actual.append(
                ActualSession(
                    session_id=w.id,
                    workout_type=str(w.workout_type),
                    training_type_effective=_effective_training_type(w),
                    duration_sec=int(w.duration_sec) if w.duration_sec else None,
                    distance_km=float(w.distance_km) if w.distance_km else None,
                    pace=str(w.pace) if w.pace else None,
                    planned_entry_id=w.planned_entry_id if w.planned_entry_id else None,
                    total_tonnage_kg=tonnage_kg,
                    exercise_count=ex_count,
                    set_count=set_count,
                    template_name=tpl_name,
                )
            )

        entries.append(
            ComplianceDayEntry(
                day_of_week=day,
                date=day_date,
                planned_types=planned_types,
                planned_run_type=planned_run_type,
                is_rest_day=is_rest,
                status=status,
                actual_sessions=actual,
                planned_template_name=planned_template_name,
                planned_exercise_count=planned_exercise_count,
            )
        )

    # --- #149: Weekly Strength Summary ---
    strength_summary: Optional[WeeklyStrengthSummary] = None
    if strength_session_count > 0:
        total_metrics = calculate_strength_metrics(all_strength_exercises)
        cat_breakdown = calculate_category_tonnage(all_strength_exercises)

        # Previous week comparison
        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = week_start - timedelta(days=1)
        prev_result = await db.execute(
            select(WorkoutModel).where(
                WorkoutModel.workout_type == "strength",
                WorkoutModel.exercises_json.isnot(None),
                WorkoutModel.date >= datetime.combine(prev_week_start, datetime.min.time()),
                WorkoutModel.date <= datetime.combine(prev_week_end, datetime.max.time()),
            )
        )
        prev_workouts = prev_result.scalars().all()

        prev_tonnage: Optional[float] = None
        delta_kg: Optional[float] = None
        delta_pct: Optional[float] = None
        trend: Optional[str] = None

        if prev_workouts:
            prev_exercises: list[dict[str, object]] = []
            for pw in prev_workouts:
                if pw.exercises_json:
                    prev_exercises.extend(json.loads(str(pw.exercises_json)))
            if prev_exercises:
                prev_metrics = calculate_strength_metrics(prev_exercises)
                prev_tonnage = prev_metrics["total_tonnage_kg"]
                current_tonnage = total_metrics["total_tonnage_kg"]
                delta_kg = round(current_tonnage - prev_tonnage, 1)
                if prev_tonnage > 0:
                    delta_pct = round((delta_kg / prev_tonnage) * 100, 1)
                    if delta_pct > 10:
                        trend = "up"
                    elif delta_pct < -10:
                        trend = "down"
                    else:
                        trend = "stable"

        strength_summary = WeeklyStrengthSummary(
            total_tonnage_kg=total_metrics["total_tonnage_kg"],
            session_count=strength_session_count,
            exercise_count=total_metrics["total_exercises"],
            set_count=total_metrics["total_sets"],
            categories=[CategoryTonnage(**cat) for cat in cat_breakdown],
            prev_week_tonnage_kg=prev_tonnage,
            tonnage_delta_kg=delta_kg,
            tonnage_delta_pct=delta_pct,
            trend=trend,
        )

    return ComplianceResponse(
        week_start=week_start,
        entries=entries,
        completed_count=completed_count,
        planned_count=planned_count,
        strength_summary=strength_summary,
    )


@router.get("/sessions-for-date", response_model=list[PlannedSessionOption])
async def get_sessions_for_date(
    target_date: date = Query(..., alias="date"),
    db: AsyncSession = Depends(get_db),
) -> list[PlannedSessionOption]:
    """Get planned sessions for a specific date (for upload linking)."""
    week_start = _monday_of_week(target_date)
    day_of_week = (target_date - week_start).days

    # Find the day entry
    day_result = await db.execute(
        select(WeeklyPlanDayModel).where(
            WeeklyPlanDayModel.week_start == week_start,
            WeeklyPlanDayModel.day_of_week == day_of_week,
        )
    )
    day = day_result.scalar_one_or_none()
    if not day:
        return []

    # Fetch sessions for this day
    session_result = await db.execute(
        select(PlannedSessionModel)
        .where(
            PlannedSessionModel.day_id == day.id,
            PlannedSessionModel.status == "active",
        )
        .order_by(PlannedSessionModel.position)
    )
    sessions = session_result.scalars().all()

    # Get template names
    template_ids = [s.template_id for s in sessions if s.template_id]
    template_names = await _get_template_names(db, template_ids)

    result: list[PlannedSessionOption] = []
    for s in sessions:
        rd = _parse_run_details(str(s.run_details_json) if s.run_details_json else None)
        tid = s.template_id if s.template_id else None
        result.append(
            PlannedSessionOption(
                id=s.id,
                training_type=str(s.training_type),
                run_type=rd.run_type if rd else None,
                template_name=template_names.get(tid) if tid else None,
                position=int(s.position),
            )
        )
    return result


@router.post("/sync-to-plan", response_model=SyncToPlanResponse)
async def sync_to_plan(  # noqa: C901, PLR0912, PLR0915  # TODO: E16 Refactoring
    data: SyncToPlanRequest,
    db: AsyncSession = Depends(get_db),
) -> SyncToPlanResponse:
    """Sync edited weekly plan entries back to training plan phase template."""
    week_start = _monday_of_week(data.week_start)

    # Load training plan
    plan_result = await db.execute(
        select(TrainingPlanModel).where(TrainingPlanModel.id == data.plan_id)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Trainingsplan nicht gefunden")

    # Load phases ordered by start_week
    phases_result = await db.execute(
        select(TrainingPhaseModel)
        .where(TrainingPhaseModel.training_plan_id == data.plan_id)
        .order_by(TrainingPhaseModel.start_week)
    )
    phases = phases_result.scalars().all()

    # Compute plan-relative week number (1-indexed)
    plan_start = plan.start_date
    plan_start_monday = plan_start - timedelta(days=plan_start.weekday())
    week_number = ((week_start - plan_start_monday).days // 7) + 1

    # Find phase for this week
    phase: TrainingPhaseModel | None = None
    for p in phases:
        if int(p.start_week) <= week_number <= int(p.end_week):
            phase = p
            break

    if not phase:
        raise HTTPException(
            status_code=404,
            detail=f"Keine Phase fuer Woche {week_number} gefunden",
        )

    # Load weekly plan days + sessions
    days_data = await _load_days_with_sessions(db, week_start)

    # Resolve template names for all sessions
    sync_template_ids: list[int] = []
    for _, (_, db_sessions) in days_data.items():
        for s in db_sessions:
            if s.template_id:
                sync_template_ids.append(s.template_id)
    sync_template_names = await _get_template_names(db, sync_template_ids)

    # Build PhaseWeeklyTemplate from weekly plan (multi-session)
    template_days: list[PhaseWeeklyTemplateDayEntry] = []
    synced_days = 0
    for dow in range(7):
        if dow in days_data:
            db_day, db_sessions = days_data[dow]
            if db_sessions or db_day.is_rest_day:
                template_sessions: list[PhaseWeeklyTemplateSessionEntry] = []
                for s in db_sessions:
                    rd = _parse_run_details(str(s.run_details_json) if s.run_details_json else None)
                    ex = _parse_exercises(str(s.exercises_json) if s.exercises_json else None)
                    s_tid = s.template_id if s.template_id else None
                    template_sessions.append(
                        PhaseWeeklyTemplateSessionEntry(
                            position=int(s.position),
                            training_type=str(s.training_type),
                            run_type=rd.run_type if rd else None,
                            template_id=s_tid,
                            template_name=sync_template_names.get(s_tid) if s_tid else None,
                            run_details=rd,
                            exercises=ex,
                        )
                    )

                template_days.append(
                    PhaseWeeklyTemplateDayEntry(
                        day_of_week=dow,
                        sessions=template_sessions,
                        is_rest_day=bool(db_day.is_rest_day),
                        notes=str(db_day.notes) if db_day.notes else None,
                    )
                )
                synced_days += 1
                continue

        template_days.append(
            PhaseWeeklyTemplateDayEntry(
                day_of_week=dow,
                is_rest_day=False,
            )
        )
    template = PhaseWeeklyTemplate(days=template_days)

    # Compute week key within phase (1-indexed)
    week_in_phase = week_number - phase.start_week
    week_key = str(week_in_phase + 1)

    # Update phase template
    template_dict = template.model_dump()
    if data.apply_to_all_weeks:
        phase.weekly_template_json = json.dumps(template_dict)
    else:
        existing_overrides: dict[str, object] = {}
        if phase.weekly_templates_json:
            try:
                parsed = json.loads(str(phase.weekly_templates_json))
                existing_overrides = parsed.get("weeks", {})
            except (json.JSONDecodeError, ValueError):
                pass
        existing_overrides[week_key] = template_dict
        phase.weekly_templates_json = json.dumps({"weeks": existing_overrides})

    # Reset edited flag on synced days
    for _dow, (db_day, _sessions) in days_data.items():
        if db_day.plan_id and int(db_day.plan_id) == data.plan_id:
            db_day.edited = False

    await log_plan_change(
        db,
        data.plan_id,
        "back_sync",
        f"Woche {week_start} in Phase '{phase.name}' synchronisiert",
        details={
            "category": "technical",
            "source": "user",
            "week_start": str(week_start),
            "phase_name": str(phase.name),
            "apply_to_all_weeks": data.apply_to_all_weeks,
            "week_key": week_key,
            "synced_days": synced_days,
        },
    )
    await db.commit()

    return SyncToPlanResponse(
        phase_id=phase.id,
        phase_name=str(phase.name),
        week_key=week_key,
        apply_to_all_weeks=data.apply_to_all_weeks,
        synced_days=synced_days,
    )


# ---------------------------------------------------------------------------
# Undo
# ---------------------------------------------------------------------------

UNDO_WINDOW_HOURS = 24


async def _find_undoable_entry(
    db: AsyncSession,
    week_start: date,
) -> PlanChangeLogModel | None:
    """Find the most recent undoable changelog entry for a week.

    Returns None if an undo was already performed for this week (within the window).
    Only one undo per week is allowed.
    """
    cutoff = datetime.utcnow() - timedelta(hours=UNDO_WINDOW_HOURS)
    week_str = str(week_start)

    result = await db.execute(
        select(PlanChangeLogModel)
        .where(PlanChangeLogModel.created_at >= cutoff)
        .order_by(PlanChangeLogModel.created_at.desc())
    )
    entries = result.scalars().all()

    # If an undo was already performed for this week, block further undos
    for entry in entries:
        if entry.change_type != "undo" or not entry.details_json:
            continue
        try:
            details = json.loads(entry.details_json)
        except json.JSONDecodeError:
            continue
        if details.get("week_start") == week_str:
            return None

    # Find the most recent undoable entry for this week
    for entry in entries:
        if entry.change_type == "undo" or not entry.details_json:
            continue
        try:
            details = json.loads(entry.details_json)
        except json.JSONDecodeError:
            continue
        if details.get("undoable") is True and details.get("week_start") == week_str:
            return entry

    return None


@router.get("/undo-status", response_model=UndoStatusResponse)
async def get_undo_status(
    week_start: date = Query(...),
    db: AsyncSession = Depends(get_db),
) -> UndoStatusResponse:
    """Check if undo is available for a given week."""
    week_start = _monday_of_week(week_start)
    entry = await _find_undoable_entry(db, week_start)

    if not entry:
        return UndoStatusResponse(available=False)

    expires_at = entry.created_at + timedelta(hours=UNDO_WINDOW_HOURS)
    return UndoStatusResponse(
        available=True,
        changelog_id=entry.id,
        summary=entry.summary,
        created_at=entry.created_at.isoformat(),
        expires_at=expires_at.isoformat(),
    )


@router.post("/undo", response_model=UndoResponse)
async def undo_weekly_plan(
    week_start: date = Query(...),
    db: AsyncSession = Depends(get_db),
) -> UndoResponse:
    """Undo the most recent change to a weekly plan (within 24h window)."""
    week_start = _monday_of_week(week_start)
    entry = await _find_undoable_entry(db, week_start)

    if not entry or not entry.details_json:
        raise HTTPException(status_code=404, detail="Kein rückgängig machbarer Eintrag gefunden.")

    details = json.loads(entry.details_json)
    snapshot = details.get("snapshot_before")
    if not snapshot or not isinstance(snapshot.get("days"), list):
        raise HTTPException(status_code=409, detail="Snapshot-Daten fehlen oder sind ungültig.")

    # Capture current state before restoring (for audit trail)
    current_data = await _load_days_with_sessions(db, week_start)
    current_phase_id, current_phase_json = await _load_linked_phase_template(
        db,
        current_data,
        week_start,
    )
    current_snapshot = _build_week_snapshot(
        week_start,
        current_data,
        current_phase_id,
        current_phase_json,
    )

    # Delete current days + sessions
    for _day, sessions in current_data.values():
        for s in sessions:
            await db.delete(s)
    for day, _sessions in current_data.values():
        await db.delete(day)
    await db.flush()

    # Restore days + sessions from snapshot
    restored_count = 0
    for snap_day in snapshot["days"]:
        plan_id = snap_day.get("plan_id")
        db_day = WeeklyPlanDayModel(
            week_start=week_start,
            day_of_week=snap_day["day_of_week"],
            is_rest_day=snap_day.get("is_rest_day", False),
            notes=snap_day.get("notes"),
            plan_id=plan_id,
            edited=snap_day.get("edited", False),
        )
        db.add(db_day)
        await db.flush()

        for snap_session in snap_day.get("sessions", []):
            db_session = PlannedSessionModel(
                day_id=db_day.id,
                position=snap_session.get("position", 0),
                training_type=snap_session["training_type"],
                template_id=snap_session.get("template_id"),
                run_details_json=snap_session.get("run_details_json"),
                exercises_json=snap_session.get("exercises_json"),
                notes=snap_session.get("notes"),
                status=snap_session.get("status", "active"),
            )
            db.add(db_session)

        restored_count += 1

    # Restore phase template if snapshot contains it
    phase_id = snapshot.get("phase_id")
    phase_json = snapshot.get("phase_weekly_templates_json")
    if phase_id and phase_json is not None:
        phase = await db.get(TrainingPhaseModel, phase_id)
        if phase:
            phase.weekly_templates_json = phase_json

    # Log undo as non-undoable changelog entry
    plan_id_for_log = snapshot["days"][0].get("plan_id") if snapshot["days"] else None
    if plan_id_for_log:
        await log_plan_change(
            db,
            plan_id_for_log,
            "undo",
            f"Rückgängig: Wochenplan {week_start} wiederhergestellt",
            details={
                "category": "content",
                "source": "undo",
                "week_start": str(week_start),
                "undoable": False,
                "undone_changelog_id": entry.id,
                "snapshot_before": current_snapshot,
            },
            category="content",
        )

    # Mark original entry as undone (prevent double-undo)
    details["undoable"] = False
    entry.details_json = json.dumps(details)

    await db.commit()

    return UndoResponse(
        success=True,
        week_start=str(week_start),
        changelog_id=entry.id,
        restored_days=restored_count,
    )


@router.post("/apply-recommendations", response_model=ApplyRecommendationsResponse)
async def apply_recommendations(
    data: ApplyRecommendationsRequest,
    db: AsyncSession = Depends(get_db),
) -> ApplyRecommendationsResponse:
    """Konvertiert KI-Review-Empfehlungen in Plan-Sessions für die Folgewoche."""
    from app.services.recommendation_to_plan_service import (
        apply_recommendations as do_apply,
    )

    week_start = _monday_of_week(data.week_start)

    result = await do_apply(
        review_week_start=week_start,
        recommendations=data.recommendations,
        db=db,
    )

    return ApplyRecommendationsResponse(**result)


# --- FIT Export (#352) ---


@router.get("/entry/{entry_id}/export/fit")
async def export_planned_session_fit(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Export eines geplanten Lauftrainings als FIT-Workout-Datei.

    Konvertiert die Segmente eines Wochenplan-Eintrags direkt in eine
    FIT-Datei fuer HealthFit / Apple Watch / Garmin.
    """
    import re

    from app.services.fit_export import export_template_to_fit

    result = await db.execute(select(PlannedSessionModel).where(PlannedSessionModel.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Geplanter Eintrag nicht gefunden.")

    if str(entry.training_type) != "running":
        raise HTTPException(
            status_code=422,
            detail="FIT-Export ist nur fuer Lauftrainings verfuegbar.",
        )

    run_details = None
    if entry.run_details_json:
        run_details = RunDetails.model_validate_json(str(entry.run_details_json))

    if not run_details or not run_details.segments:
        raise HTTPException(
            status_code=422,
            detail="Geplanter Eintrag hat keine Segmente fuer den Export.",
        )

    # Workout-Name: Notizen oder Run-Type
    workout_name = str(entry.notes or "").split("\n")[0][:50] if entry.notes else None
    if not workout_name:
        workout_name = run_details.run_type or "Lauftraining"

    fit_bytes = export_template_to_fit(
        template_name=workout_name,
        segments=run_details.segments,
    )

    safe_name = re.sub(r"[^a-z0-9]+", "-", workout_name.lower()).strip("-")[:50]
    today = date.today().isoformat()
    filename = f"workout-{safe_name}-{today}.fit"

    return Response(
        content=fit_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
