"""API routes for Weekly Plan (Issue #26, #27, #28)."""

import json
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.training_plans import log_plan_change
from app.infrastructure.database.models import (
    SessionTemplateModel,
    TrainingPhaseModel,
    TrainingPlanModel,
    WeeklyPlanEntryModel,
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


@router.get("", response_model=WeeklyPlanResponse)
async def get_weekly_plan(
    week_start: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
) -> WeeklyPlanResponse:
    """Get the weekly plan for a given week (defaults to current week)."""
    if week_start is None:
        week_start = _monday_of_week(date.today())
    else:
        # Normalize to Monday
        week_start = _monday_of_week(week_start)

    result = await db.execute(
        select(WeeklyPlanEntryModel)
        .where(WeeklyPlanEntryModel.week_start == week_start)
        .order_by(WeeklyPlanEntryModel.day_of_week)
    )
    existing = {
        int(e.day_of_week): e
        for e in result.scalars().all()  # type: ignore[arg-type]
    }

    # Collect template IDs for name lookup
    template_ids = [
        int(e.template_id)  # type: ignore[arg-type]
        for e in existing.values()
        if e.template_id is not None
    ]
    template_names = await _get_template_names(db, template_ids)

    # Build full 7-day response (fill gaps with empty entries)
    entries: list[WeeklyPlanEntry] = []
    for day in range(7):
        if day in existing:
            e = existing[day]
            run_details = _parse_run_details(
                str(e.run_details_json) if e.run_details_json else None
            )
            entries.append(
                WeeklyPlanEntry(
                    day_of_week=day,
                    training_type=str(e.training_type) if e.training_type else None,
                    template_id=int(e.template_id) if e.template_id else None,  # type: ignore[arg-type]
                    template_name=template_names.get(int(e.template_id)) if e.template_id else None,  # type: ignore[arg-type]
                    is_rest_day=bool(e.is_rest_day),
                    notes=str(e.notes) if e.notes else None,
                    run_details=run_details,
                    plan_id=int(e.plan_id) if e.plan_id else None,
                    edited=bool(e.edited),
                )
            )
        else:
            entries.append(
                WeeklyPlanEntry(
                    day_of_week=day,
                    training_type=None,
                    is_rest_day=False,
                    notes=None,
                    run_details=None,
                )
            )

    return WeeklyPlanResponse(week_start=week_start, entries=entries)


def _has_content_changed(
    old: WeeklyPlanEntryModel,
    new_entry: WeeklyPlanEntry,
    new_run_details_str: Optional[str],
) -> bool:
    """Compare old DB entry with new request entry to detect edits."""
    if str(old.training_type or "") != str(new_entry.training_type or ""):
        return True
    if bool(old.is_rest_day) != new_entry.is_rest_day:
        return True
    if str(old.notes or "") != str(new_entry.notes or ""):
        return True
    if (old.template_id or None) != (new_entry.template_id or None):
        return True
    old_rd = str(old.run_details_json) if old.run_details_json else None
    return (old_rd or None) != (new_run_details_str or None)


_FIELD_LABELS_DAY: dict[str, str] = {
    "training_type": "Trainingstyp",
    "is_rest_day": "Ruhetag",
    "notes": "Notizen",
    "template_id": "Vorlage",
    "run_type": "Lauftyp",
    "target_duration_minutes": "Dauer (Ziel)",
    "target_pace_min": "Ziel-Pace (schnell)",
    "target_pace_max": "Ziel-Pace (langsam)",
    "target_hr_min": "Herzfrequenz (min)",
    "target_hr_max": "Herzfrequenz (max)",
}


def _diff_day_entry(
    old: WeeklyPlanEntryModel,
    new_entry: WeeklyPlanEntry,
    new_run_details_str: Optional[str],
) -> list[dict[str, object]]:
    """Return field-level diff between old DB entry and new request entry."""
    changes: list[dict[str, object]] = []

    def _add(field: str, from_val: object, to_val: object) -> None:
        if from_val != to_val:
            changes.append({
                "field": field,
                "from": from_val,
                "to": to_val,
                "label": _FIELD_LABELS_DAY.get(field, field),
            })

    _add("training_type", old.training_type or None, new_entry.training_type)
    _add("is_rest_day", bool(old.is_rest_day), new_entry.is_rest_day)
    _add("notes", old.notes or None, new_entry.notes)
    _add("template_id", old.template_id or None, new_entry.template_id)

    # RunDetails field-level diff
    old_rd_str = str(old.run_details_json) if old.run_details_json else None
    if (old_rd_str or None) != (new_run_details_str or None):
        old_rd: dict[str, object] = json.loads(old_rd_str) if old_rd_str else {}
        new_rd: dict[str, object] = json.loads(new_run_details_str) if new_run_details_str else {}
        for field in ("run_type", "target_duration_minutes", "target_pace_min",
                       "target_pace_max", "target_hr_min", "target_hr_max"):
            _add(field, old_rd.get(field), new_rd.get(field))

    return changes


@router.put("", response_model=WeeklyPlanResponse)
async def save_weekly_plan(
    data: WeeklyPlanSaveRequest,
    db: AsyncSession = Depends(get_db),
) -> WeeklyPlanResponse:
    """Save/update the weekly plan. Upserts all provided day entries."""
    week_start = _monday_of_week(data.week_start)

    # Validate days
    seen_days: set[int] = set()
    for entry in data.entries:
        if entry.day_of_week in seen_days:
            raise HTTPException(
                status_code=422,
                detail=f"Doppelter Tag: {DAY_NAMES[entry.day_of_week]}",
            )
        seen_days.add(entry.day_of_week)

    # Fetch existing entries BEFORE deletion (for plan_id + edited preservation)
    result = await db.execute(
        select(WeeklyPlanEntryModel).where(WeeklyPlanEntryModel.week_start == week_start)
    )
    old_entries: dict[int, WeeklyPlanEntryModel] = {
        int(e.day_of_week): e for e in result.scalars().all()
    }

    # Delete existing entries
    for existing in old_entries.values():
        await db.delete(existing)
    await db.flush()

    # Insert new entries, preserving plan_id and detecting edits
    for entry in data.entries:
        run_details_str: Optional[str] = None
        if entry.run_details is not None:
            run_details_str = json.dumps(entry.run_details.model_dump())

        # Carry over plan_id and detect edits
        old = old_entries.get(entry.day_of_week)
        plan_id: Optional[int] = None
        edited = False

        if old and old.plan_id:
            plan_id = int(old.plan_id)
            edited = True if _has_content_changed(old, entry, run_details_str) else bool(old.edited)

        db_entry = WeeklyPlanEntryModel(
            week_start=week_start,
            day_of_week=entry.day_of_week,
            training_type=entry.training_type,
            template_id=entry.template_id,
            is_rest_day=entry.is_rest_day,
            notes=entry.notes,
            run_details_json=run_details_str,
            plan_id=plan_id,
            edited=edited,
        )
        db.add(db_entry)

    # Log manual edits to plan-linked entries with day-level diffs
    changed_plan_days: dict[int, list[dict[str, object]]] = {}
    for entry in data.entries:
        run_details_str_log: Optional[str] = None
        if entry.run_details is not None:
            run_details_str_log = json.dumps(entry.run_details.model_dump())
        old = old_entries.get(entry.day_of_week)
        if old and old.plan_id and _has_content_changed(old, entry, run_details_str_log):
            pid = int(old.plan_id)
            day_changes = _diff_day_entry(old, entry, run_details_str_log)
            if day_changes:
                if pid not in changed_plan_days:
                    changed_plan_days[pid] = []
                changed_plan_days[pid].append({
                    "day_of_week": entry.day_of_week,
                    "day_name": DAY_NAMES[entry.day_of_week],
                    "field_changes": day_changes,
                })
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

    result = await db.execute(
        select(WeeklyPlanEntryModel).where(WeeklyPlanEntryModel.week_start == week_start)
    )
    for existing in result.scalars().all():
        await db.delete(existing)

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
    plan_entry: Optional[WeeklyPlanEntryModel],
    sessions: list[WorkoutModel],
) -> str:
    """Determine compliance status for a day."""
    has_plan = plan_entry is not None and (
        plan_entry.training_type is not None or plan_entry.is_rest_day
    )
    has_sessions = len(sessions) > 0

    if not has_plan and not has_sessions:
        return "empty"

    if not has_plan and has_sessions:
        return "unplanned"

    if has_plan and plan_entry is not None and plan_entry.is_rest_day:
        return "rest_ok" if not has_sessions else "off_target"

    if has_plan and not has_sessions:
        return "missed"

    # Both plan and sessions exist — check type match
    if plan_entry is not None and plan_entry.training_type:
        planned_type = str(plan_entry.training_type)
        # Map plan training_type to workout_type
        type_map = {"strength": "strength", "running": "running"}
        expected_workout_type = type_map.get(planned_type, planned_type)
        matched = any(str(s.workout_type) == expected_workout_type for s in sessions)
        return "completed" if matched else "off_target"

    return "completed"


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

    # Fetch plan entries
    plan_result = await db.execute(
        select(WeeklyPlanEntryModel)
        .where(WeeklyPlanEntryModel.week_start == week_start)
        .order_by(WeeklyPlanEntryModel.day_of_week)
    )
    plan_entries = {
        int(e.day_of_week): e  # type: ignore[arg-type]
        for e in plan_result.scalars().all()
    }

    # Fetch all sessions for this week
    session_result = await db.execute(
        select(WorkoutModel)
        .where(
            WorkoutModel.date >= datetime.combine(week_start, datetime.min.time()),
            WorkoutModel.date <= datetime.combine(week_end, datetime.max.time()),
        )
        .order_by(WorkoutModel.date)
    )
    all_sessions = session_result.scalars().all()

    # Group sessions by day_of_week
    sessions_by_day: dict[int, list[WorkoutModel]] = {d: [] for d in range(7)}
    for s in all_sessions:
        session_date = s.date
        if isinstance(session_date, datetime):
            session_date = session_date.date()
        day_idx = (session_date - week_start).days  # type: ignore[operator]
        if 0 <= day_idx <= 6:
            sessions_by_day[day_idx].append(s)

    # Build compliance entries
    entries: list[ComplianceDayEntry] = []
    completed_count = 0
    planned_count = 0

    for day in range(7):
        day_date = week_start + timedelta(days=day)
        plan_entry = plan_entries.get(day)
        day_sessions = sessions_by_day[day]

        # Determine planned details
        planned_type: Optional[str] = None
        planned_run_type: Optional[str] = None
        is_rest = False
        if plan_entry:
            if plan_entry.training_type:
                planned_type = str(plan_entry.training_type)
            is_rest = bool(plan_entry.is_rest_day)
            if plan_entry.run_details_json:
                run_details = _parse_run_details(str(plan_entry.run_details_json))
                if run_details:
                    planned_run_type = run_details.run_type

        has_plan = planned_type is not None or is_rest
        if has_plan:
            planned_count += 1

        status = _determine_status(plan_entry, day_sessions)
        if status == "completed" or status == "rest_ok":
            completed_count += 1

        actual = [
            ActualSession(
                session_id=int(s.id),  # type: ignore[arg-type]
                workout_type=str(s.workout_type),
                training_type_effective=_effective_training_type(s),
                duration_sec=int(s.duration_sec) if s.duration_sec else None,
                distance_km=float(s.distance_km) if s.distance_km else None,
                pace=str(s.pace) if s.pace else None,
                planned_entry_id=int(s.planned_entry_id) if s.planned_entry_id else None,  # type: ignore[arg-type]
            )
            for s in day_sessions
        ]

        entries.append(
            ComplianceDayEntry(
                day_of_week=day,
                date=day_date,
                planned_type=planned_type,
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

    # Load weekly plan entries for this week
    entries_result = await db.execute(
        select(WeeklyPlanEntryModel).where(WeeklyPlanEntryModel.week_start == week_start)
    )
    db_entries = {int(e.day_of_week): e for e in entries_result.scalars().all()}

    # Build PhaseWeeklyTemplate from weekly plan entries
    days: list[PhaseWeeklyTemplateDayEntry] = []
    synced_days = 0
    for day in range(7):
        entry = db_entries.get(day)
        if entry and (entry.training_type or entry.is_rest_day):
            run_details = _parse_run_details(
                str(entry.run_details_json) if entry.run_details_json else None
            )
            run_type = run_details.run_type if run_details else None
            days.append(
                PhaseWeeklyTemplateDayEntry(
                    day_of_week=day,
                    training_type=str(entry.training_type) if entry.training_type else None,
                    is_rest_day=bool(entry.is_rest_day),
                    run_type=run_type,
                    template_id=int(entry.template_id) if entry.template_id else None,
                    notes=str(entry.notes) if entry.notes else None,
                    run_details=run_details,
                )
            )
            synced_days += 1
        else:
            days.append(
                PhaseWeeklyTemplateDayEntry(
                    day_of_week=day,
                    training_type=None,
                    is_rest_day=False,
                    run_type=None,
                    notes=None,
                )
            )
    template = PhaseWeeklyTemplate(days=days)

    # Compute week key within phase (1-indexed)
    week_in_phase = week_number - int(phase.start_week)  # type: ignore[arg-type]
    week_key = str(week_in_phase + 1)

    # Update phase template
    template_dict = template.model_dump()
    if data.apply_to_all_weeks:
        # Update shared template (all weeks of phase)
        phase.weekly_template_json = json.dumps(template_dict)  # type: ignore[assignment]
    else:
        # Update per-week override (merge with existing)
        existing_overrides: dict[str, object] = {}
        if phase.weekly_templates_json:
            try:
                parsed = json.loads(str(phase.weekly_templates_json))
                existing_overrides = parsed.get("weeks", {})
            except (json.JSONDecodeError, ValueError):
                pass
        existing_overrides[week_key] = template_dict
        phase.weekly_templates_json = json.dumps({"weeks": existing_overrides})  # type: ignore[assignment]

    # Reset edited flag on synced entries
    for entry in db_entries.values():
        if entry.plan_id and int(entry.plan_id) == data.plan_id:
            entry.edited = False  # type: ignore[assignment]

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
