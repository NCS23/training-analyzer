"""Tests for Streak Tracking (Issue #58)."""

from datetime import date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import WorkoutModel


async def _add_session(db: AsyncSession, days_ago: int) -> None:
    """Add a training session N days ago (uses date.today() for consistency with streak API)."""
    target_date = date.today() - timedelta(days=days_ago)
    workout = WorkoutModel(
        date=datetime(target_date.year, target_date.month, target_date.day, 12, 0),
        workout_type="running",
        duration_sec=2700,
        distance_km=5.0,
    )
    db.add(workout)
    await db.commit()


@pytest.mark.anyio
async def test_streak_empty(client: AsyncClient) -> None:
    """No sessions → zero streak."""
    response = await client.get("/api/v1/streak")
    assert response.status_code == 200
    body = response.json()
    assert body["current_streak"] == 0
    assert body["longest_streak"] == 0
    assert body["last_training_date"] is None
    assert body["streak_at_risk"] is False
    assert body["calendar"] == {}


@pytest.mark.anyio
async def test_streak_consecutive_days(client: AsyncClient, db_session: AsyncSession) -> None:
    """Training 3 days in a row including today → streak 3."""
    await _add_session(db_session, 0)  # today
    await _add_session(db_session, 1)  # yesterday
    await _add_session(db_session, 2)  # 2 days ago

    response = await client.get("/api/v1/streak")
    body = response.json()
    assert body["current_streak"] == 3
    assert body["longest_streak"] == 3


@pytest.mark.anyio
async def test_streak_gap_breaks_current(client: AsyncClient, db_session: AsyncSession) -> None:
    """Gap in training breaks current streak."""
    await _add_session(db_session, 0)  # today
    await _add_session(db_session, 1)  # yesterday
    # gap at 2 days ago
    await _add_session(db_session, 3)  # 3 days ago
    await _add_session(db_session, 4)  # 4 days ago

    response = await client.get("/api/v1/streak")
    body = response.json()
    assert body["current_streak"] == 2  # today + yesterday
    assert body["longest_streak"] == 2  # both streaks are 2 days


@pytest.mark.anyio
async def test_streak_at_risk(client: AsyncClient, db_session: AsyncSession) -> None:
    """Trained yesterday but not today → streak at risk."""
    await _add_session(db_session, 1)  # yesterday
    await _add_session(db_session, 2)  # day before

    response = await client.get("/api/v1/streak")
    body = response.json()
    assert body["current_streak"] == 2
    assert body["streak_at_risk"] is True


@pytest.mark.anyio
async def test_longest_streak_historical(client: AsyncClient, db_session: AsyncSession) -> None:
    """Longest streak can be in the past."""
    # Past streak: 5 days (80-76 days ago)
    for i in range(76, 81):
        await _add_session(db_session, i)

    # Current streak: 2 days
    await _add_session(db_session, 0)
    await _add_session(db_session, 1)

    response = await client.get("/api/v1/streak")
    body = response.json()
    assert body["current_streak"] == 2
    assert body["longest_streak"] == 5


@pytest.mark.anyio
async def test_calendar_heatmap(client: AsyncClient, db_session: AsyncSession) -> None:
    """Calendar returns session counts for last 90 days."""
    await _add_session(db_session, 0)  # today
    await _add_session(db_session, 0)  # second session today
    await _add_session(db_session, 5)  # 5 days ago

    response = await client.get("/api/v1/streak")
    body = response.json()
    calendar = body["calendar"]
    # Should have exactly 2 entries
    assert len(calendar) == 2
    # Today should have count 2
    today_str = date.today().isoformat()
    assert calendar.get(today_str) == 2
