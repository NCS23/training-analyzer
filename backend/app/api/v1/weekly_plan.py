"""API routes for Weekly Plan (Issue #26)."""

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import TrainingPlanModel, WeeklyPlanEntryModel
from app.infrastructure.database.session import get_db
from app.models.weekly_plan import (
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
            entries.append(
                WeeklyPlanEntry(
                    day_of_week=day,
                    training_type=str(e.training_type) if e.training_type else None,
                    plan_id=int(e.plan_id) if e.plan_id else None,  # type: ignore[arg-type]
                    plan_name=plan_names.get(int(e.plan_id)) if e.plan_id else None,  # type: ignore[arg-type]
                    is_rest_day=bool(e.is_rest_day),
                    notes=str(e.notes) if e.notes else None,
                )
            )
        else:
            entries.append(
                WeeklyPlanEntry(
                    day_of_week=day,
                    training_type=None,
                    is_rest_day=False,
                    notes=None,
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
        db_entry = WeeklyPlanEntryModel(
            week_start=week_start,
            day_of_week=entry.day_of_week,
            training_type=entry.training_type,
            plan_id=entry.plan_id,
            is_rest_day=entry.is_rest_day,
            notes=entry.notes,
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
