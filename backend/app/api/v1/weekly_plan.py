"""API routes for Weekly Plan (Issue #26, #27, #28, E17-S02)."""

import json
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.training_plans import log_plan_change
from app.infrastructure.database.models import (
    PlannedSessionModel,
    SessionTemplateModel,
    TrainingPhaseModel,
    TrainingPlanModel,
    WeeklyPlanDayModel,
    WorkoutModel,
)
from app.infrastructure.database.session import get_db
from app.models.training_plan import (
    PhaseWeeklyTemplate,
    PhaseWeeklyTemplateDayEntry,
)
from app.models.weekly_plan import (
    ActualSession,
    ComplianceDayEntry,
    ComplianceResponse,
    PlannedSession,
    RunDetails,
    SyncToPlanRequest,
    SyncToPlanResponse,
    WeeklyPlanEntry,
    WeeklyPlanResponse,
    WeeklyPlanSaveRequest,
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
    return {row.id: str(row.name) for row in result.all()}  # type: ignore[union-attr]


def _parse_run_details(raw: Optional[str]) -> Optional[RunDetails]:
    """Parse run_details_json string to RunDetails model."""
    if not raw:
        return None
    try:
        data = json.loads(raw)
        return RunDetails(**data)
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

    day_ids = [int(d.id) for d in days.values()]  # type: ignore[arg-type]
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
        day_id = int(day.id)  # type: ignore[arg-type]
        result[dow] = (day, sessions_by_day_id.get(day_id, []))

    return result


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
        run_details = _parse_run_details(
            str(s.run_details_json) if s.run_details_json else None
        )
        tid = int(s.template_id) if s.template_id else None
        session_list.append(
            PlannedSession(
                id=int(s.id),  # type: ignore[arg-type]
                position=int(s.position),
                training_type=str(s.training_type),
                template_id=tid,
                template_name=template_names.get(tid) if tid else None,
                notes=str(s.notes) if s.notes else None,
                run_details=run_details,
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
                template_ids.append(int(s.template_id))
    template_names = await _get_template_names(db, template_ids)

    # Build full 7-day response
    entries: list[WeeklyPlanEntry] = []
    for dow in range(7):
        if dow in days_data:
            day, sessions = days_data[dow]
            entries.append(_build_entry_from_db(dow, day, sessions, template_names))
        else:
            entries.append(WeeklyPlanEntry(day_of_week=dow))

    return WeeklyPlanResponse(week_start=week_start, entries=entries)


def _sessions_changed(
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
        new_rd_str = json.dumps(new_s.run_details.model_dump()) if new_s and new_s.run_details else None
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
async def save_weekly_plan(
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
            plan_id = int(old_day.plan_id)
            edited = (
                True
                if _has_content_changed(old_day, old_sessions, entry)
                else bool(old_day.edited)
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

            db_session = PlannedSessionModel(
                day_id=db_day.id,
                position=session.position,
                training_type=session.training_type,
                template_id=session.template_id,
                run_details_json=run_details_str,
                notes=session.notes,
            )
            db.add(db_session)

    # Log manual edits to plan-linked entries with day-level diffs
    changed_plan_days: dict[int, list[dict[str, object]]] = {}
    for entry in data.entries:
        old = old_data.get(entry.day_of_week)
        old_day = old[0] if old else None
        old_sessions = old[1] if old else []

        if (
            old_day
            and old_day.plan_id
            and _has_content_changed(old_day, old_sessions, entry)
        ):
            pid = int(old_day.plan_id)
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
        await log_plan_change(
            db,
            pid,
            "manual_edit",
            f"Wochenplan {week_start}: {count} Eintraege bearbeitet",
            details={
                "category": "content",
                "source": "user",
                "week_start": str(week_start),
                "changed_days": changed_days,
            },
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
        day_ids = [int(d.id) for d in days]  # type: ignore[arg-type]
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


def _determine_status(
    planned_types: list[str],
    is_rest_day: bool,
    sessions: list[WorkoutModel],
) -> str:
    """Determine compliance status for a day."""
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

    # Both plan and sessions exist — check type match
    type_map = {"strength": "strength", "running": "running"}
    for pt in planned_types:
        expected = type_map.get(pt, pt)
        if any(str(s.workout_type) == expected for s in sessions):
            return "completed"

    return "off_target"


@router.get("/compliance", response_model=ComplianceResponse)
async def get_compliance(
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
        workout_date = w.date
        if isinstance(workout_date, datetime):
            workout_date = workout_date.date()
        day_idx = (workout_date - week_start).days  # type: ignore[operator]
        if 0 <= day_idx <= 6:
            workouts_by_day[day_idx].append(w)

    # Build compliance entries
    entries: list[ComplianceDayEntry] = []
    completed_count = 0
    planned_count = 0

    for day in range(7):
        day_date = week_start + timedelta(days=day)
        day_workouts = workouts_by_day[day]

        planned_types: list[str] = []
        planned_run_type: Optional[str] = None
        is_rest = False

        if day in days_data:
            db_day, db_sessions = days_data[day]
            is_rest = bool(db_day.is_rest_day)
            for s in db_sessions:
                planned_types.append(str(s.training_type))
                if str(s.training_type) == "running" and planned_run_type is None:
                    rd = _parse_run_details(
                        str(s.run_details_json) if s.run_details_json else None
                    )
                    if rd:
                        planned_run_type = rd.run_type

        has_plan = len(planned_types) > 0 or is_rest
        if has_plan:
            planned_count += 1

        status = _determine_status(planned_types, is_rest, day_workouts)
        if status in ("completed", "rest_ok"):
            completed_count += 1

        actual = [
            ActualSession(
                session_id=int(w.id),  # type: ignore[arg-type]
                workout_type=str(w.workout_type),
                training_type_effective=_effective_training_type(w),
                duration_sec=int(w.duration_sec) if w.duration_sec else None,
                distance_km=float(w.distance_km) if w.distance_km else None,
                pace=str(w.pace) if w.pace else None,
                planned_entry_id=int(w.planned_entry_id) if w.planned_entry_id else None,  # type: ignore[arg-type]
            )
            for w in day_workouts
        ]

        entries.append(
            ComplianceDayEntry(
                day_of_week=day,
                date=day_date,
                planned_types=planned_types,
                planned_run_type=planned_run_type,
                is_rest_day=is_rest,
                status=status,
                actual_sessions=actual,
            )
        )

    return ComplianceResponse(
        week_start=week_start,
        entries=entries,
        completed_count=completed_count,
        planned_count=planned_count,
    )


@router.post("/sync-to-plan", response_model=SyncToPlanResponse)
async def sync_to_plan(
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
    plan_start_monday = plan_start - timedelta(days=plan_start.weekday())  # type: ignore[operator]
    week_number = ((week_start - plan_start_monday).days // 7) + 1

    # Find phase for this week
    phase: TrainingPhaseModel | None = None
    for p in phases:
        if int(p.start_week) <= week_number <= int(p.end_week):  # type: ignore[arg-type]
            phase = p
            break

    if not phase:
        raise HTTPException(
            status_code=404,
            detail=f"Keine Phase fuer Woche {week_number} gefunden",
        )

    # Load weekly plan days + sessions
    days_data = await _load_days_with_sessions(db, week_start)

    # Build PhaseWeeklyTemplate from weekly plan
    # Note: PhaseWeeklyTemplateDayEntry is still flat (S03 will update to multi-session)
    # For now, use the first session's data per day
    template_days: list[PhaseWeeklyTemplateDayEntry] = []
    synced_days = 0
    for dow in range(7):
        if dow in days_data:
            db_day, db_sessions = days_data[dow]
            if db_sessions or db_day.is_rest_day:
                first_session = db_sessions[0] if db_sessions else None
                training_type: Optional[str] = None
                run_type: Optional[str] = None
                template_id: Optional[int] = None
                run_details: Optional[RunDetails] = None

                if first_session:
                    training_type = str(first_session.training_type)
                    template_id = (
                        int(first_session.template_id)
                        if first_session.template_id
                        else None
                    )
                    run_details = _parse_run_details(
                        str(first_session.run_details_json)
                        if first_session.run_details_json
                        else None
                    )
                    run_type = run_details.run_type if run_details else None

                template_days.append(
                    PhaseWeeklyTemplateDayEntry(
                        day_of_week=dow,
                        training_type=training_type,
                        is_rest_day=bool(db_day.is_rest_day),
                        run_type=run_type,
                        template_id=template_id,
                        notes=str(db_day.notes) if db_day.notes else None,
                        run_details=run_details,
                    )
                )
                synced_days += 1
                continue

        template_days.append(
            PhaseWeeklyTemplateDayEntry(
                day_of_week=dow,
                training_type=None,
                is_rest_day=False,
                run_type=None,
                notes=None,
            )
        )
    template = PhaseWeeklyTemplate(days=template_days)

    # Compute week key within phase (1-indexed)
    week_in_phase = week_number - int(phase.start_week)  # type: ignore[arg-type]
    week_key = str(week_in_phase + 1)

    # Update phase template
    template_dict = template.model_dump()
    if data.apply_to_all_weeks:
        phase.weekly_template_json = json.dumps(template_dict)  # type: ignore[assignment]
    else:
        existing_overrides: dict[str, object] = {}
        if phase.weekly_templates_json:
            try:
                parsed = json.loads(str(phase.weekly_templates_json))
                existing_overrides = parsed.get("weeks", {})
            except (json.JSONDecodeError, ValueError):
                pass
        existing_overrides[week_key] = template_dict
        phase.weekly_templates_json = json.dumps({"weeks": existing_overrides})  # type: ignore[assignment]

    # Reset edited flag on synced days
    for _dow, (db_day, _sessions) in days_data.items():
        if db_day.plan_id and int(db_day.plan_id) == data.plan_id:
            db_day.edited = False  # type: ignore[assignment]

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
        phase_id=int(phase.id),  # type: ignore[arg-type]
        phase_name=str(phase.name),
        week_key=week_key,
        apply_to_all_weeks=data.apply_to_all_weeks,
        synced_days=synced_days,
    )
