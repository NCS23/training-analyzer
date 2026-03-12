"""Streak Tracking API (Issue #58)."""

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import WorkoutModel
from app.infrastructure.database.session import get_db
from app.models.streak import StreakResponse

router = APIRouter(prefix="/streak", tags=["analytics"])


@router.get("", response_model=StreakResponse)
async def get_streak(
    db: AsyncSession = Depends(get_db),
) -> StreakResponse:
    """Get training streak statistics with 90-day calendar heatmap."""
    today = date.today()

    # Fetch all training dates (distinct days)
    result = await db.execute(
        select(
            func.date(WorkoutModel.date).label("training_date"),
            func.count().label("session_count"),
        )
        .group_by(func.date(WorkoutModel.date))
        .order_by(func.date(WorkoutModel.date).desc())
    )
    rows = result.all()

    # Build set of training dates
    training_dates: dict[date, int] = {}
    for row in rows:
        d = row.training_date
        if isinstance(d, str):
            d = date.fromisoformat(d)
        elif isinstance(d, datetime):
            d = d.date()
        training_dates[d] = int(row.session_count)

    # Compute current streak (counting back from today/yesterday)
    current_streak = 0
    check_date = today
    # Allow today to not have a session yet (streak continues from yesterday)
    if check_date not in training_dates:
        check_date = today - timedelta(days=1)

    while check_date in training_dates:
        current_streak += 1
        check_date -= timedelta(days=1)

    # Compute longest streak ever
    longest_streak = 0
    last_date: str | None = None
    if training_dates:
        sorted_dates = sorted(training_dates.keys())
        streak = 1
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i - 1]).days == 1:
                streak += 1
            else:
                longest_streak = max(longest_streak, streak)
                streak = 1
        longest_streak = max(longest_streak, streak)
        last_date = sorted_dates[-1].isoformat()

    # Streak at risk: had training yesterday but not today
    streak_at_risk = (
        current_streak > 0
        and today not in training_dates
        and (today - timedelta(days=1)) in training_dates
    )

    # 90-day calendar heatmap
    calendar: dict[str, int] = {}
    for i in range(90):
        d = today - timedelta(days=89 - i)
        if d in training_dates:
            calendar[d.isoformat()] = training_dates[d]

    return StreakResponse(
        current_streak=current_streak,
        longest_streak=longest_streak,
        last_training_date=last_date,
        streak_at_risk=streak_at_risk,
        calendar=calendar,
    )
