"""API routes for Weekly Plan (Issue #26, #27, #28)."""

import json
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    TrainingPlanModel,
    WeeklyPlanEntryModel,
    WorkoutModel,
)
from app.infrastructure.database.session import get_db
from app.models.weekly_plan import (
    ActualSession,
    ComplianceDayEntry,
    ComplianceResponse,
    RunDetails,
    WeeklyPlanEntry,
    WeeklyPlanResponse,
    WeeklyPlanSaveRequest,
)

router = APIRouter(prefix="/weekly-plan")

DAY_NAMES = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def _monday_of_week(d: date) -> date:
    """Return the Monday of the week containing `d`."""
    return d - timedelta(days=d.weekday())


async def _get_plan_names(
    db: AsyncSession, plan_ids: list[int],
) -> dict[int, str]:
    """Fetch plan names for a list of plan IDs."""
    if not plan_ids:
        return {}
    result = await db.execute(
        select(TrainingPlanModel.id, TrainingPlanModel.name).where(
            TrainingPlanModel.id.in_(plan_ids)
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
        int(e.day_of_week): e for e in result.scalars().all()  # type: ignore[arg-type]
    }

    # Collect plan IDs for name lookup
    plan_ids = [
        int(e.plan_id)  # type: ignore[arg-type]
        for e in existing.values()
        if e.plan_id is not None
    ]
    plan_names = await _get_plan_names(db, plan_ids)

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
                    plan_id=int(e.plan_id) if e.plan_id else None,  # type: ignore[arg-type]
                    plan_name=plan_names.get(int(e.plan_id)) if e.plan_id else None,  # type: ignore[arg-type]
                    is_rest_day=bool(e.is_rest_day),
                    notes=str(e.notes) if e.notes else None,
                    run_details=run_details,
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

    # Delete existing entries for this week
    result = await db.execute(
        select(WeeklyPlanEntryModel).where(
            WeeklyPlanEntryModel.week_start == week_start
        )
    )
    for existing in result.scalars().all():
        await db.delete(existing)
    await db.flush()  # Ensure deletes are applied before inserts

    # Insert new entries
    for entry in data.entries:
        run_details_str: Optional[str] = None
        if entry.run_details is not None:
            run_details_str = json.dumps(entry.run_details.model_dump())

        db_entry = WeeklyPlanEntryModel(
            week_start=week_start,
            day_of_week=entry.day_of_week,
            training_type=entry.training_type,
            plan_id=entry.plan_id,
            is_rest_day=entry.is_rest_day,
            notes=entry.notes,
            run_details_json=run_details_str,
        )
        db.add(db_entry)

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
        select(WeeklyPlanEntryModel).where(
            WeeklyPlanEntryModel.week_start == week_start
        )
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
        matched = any(
            str(s.workout_type) == expected_workout_type for s in sessions
        )
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
