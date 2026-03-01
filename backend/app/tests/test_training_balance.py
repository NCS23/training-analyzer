"""Tests for Training Balance Analysis (Issue #48)."""

import json
from datetime import datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import WorkoutModel


async def _add_running(
    db: AsyncSession,
    days_ago: int,
    training_type: str = "easy",
    distance_km: float = 5.0,
    duration_sec: int = 2700,
) -> None:
    """Helper to add a running session."""
    workout = WorkoutModel(
        date=datetime.utcnow() - timedelta(days=days_ago),
        workout_type="running",
        training_type_auto=training_type,
        distance_km=distance_km,
        duration_sec=duration_sec,
        pace="5:30",
    )
    db.add(workout)
    await db.commit()


async def _add_strength(
    db: AsyncSession,
    days_ago: int,
    exercises: list[dict[str, object]],
) -> None:
    """Helper to add a strength session."""
    workout = WorkoutModel(
        date=datetime.utcnow() - timedelta(days=days_ago),
        workout_type="strength",
        duration_sec=3600,
        exercises_json=json.dumps(exercises),
    )
    db.add(workout)
    await db.commit()


@pytest.mark.anyio
async def test_balance_empty(client: AsyncClient) -> None:
    """Empty period returns zeros."""
    response = await client.get(
        "/api/v1/training-balance", params={"days": 28}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["period_days"] == 28
    assert body["intensity"]["total_sessions"] == 0
    assert body["volume_weeks"] == []
    assert body["muscle_groups"] == []
    assert body["sport_mix"]["total_sessions"] == 0


@pytest.mark.anyio
async def test_intensity_distribution(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Running sessions classified by intensity."""
    # 4 easy, 1 tempo → 80/20 polarized
    await _add_running(db_session, 1, "easy")
    await _add_running(db_session, 3, "easy")
    await _add_running(db_session, 5, "easy")
    await _add_running(db_session, 7, "recovery")
    await _add_running(db_session, 9, "tempo")

    response = await client.get(
        "/api/v1/training-balance", params={"days": 28}
    )
    body = response.json()
    intensity = body["intensity"]
    assert intensity["total_sessions"] == 5
    assert intensity["easy_sessions"] == 4  # easy + recovery
    assert intensity["moderate_sessions"] == 1  # tempo
    assert intensity["hard_sessions"] == 0
    assert intensity["is_polarized"] is True


@pytest.mark.anyio
async def test_volume_weeks(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Volume grouped by week with change percent."""
    # Week 1: 10km, Week 2: 15km → 50% increase
    await _add_running(db_session, 14, "easy", 10.0, 3600)
    await _add_running(db_session, 7, "easy", 15.0, 5400)

    response = await client.get(
        "/api/v1/training-balance", params={"days": 28}
    )
    body = response.json()
    weeks = body["volume_weeks"]
    assert len(weeks) >= 2
    # Later week should have volume_change_percent
    last_week = weeks[-1]
    assert last_week["volume_change_percent"] is not None
    assert last_week["volume_change_percent"] == 50.0


@pytest.mark.anyio
async def test_muscle_groups(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Muscle groups from strength exercises."""
    exercises = [
        {"name": "Bankdrücken", "category": "push", "sets": [
            {"reps": 8, "weight_kg": 80},
            {"reps": 8, "weight_kg": 80},
            {"reps": 8, "weight_kg": 80},
        ]},
        {"name": "Kniebeugen", "category": "legs", "sets": [
            {"reps": 10, "weight_kg": 60},
            {"reps": 10, "weight_kg": 60},
        ]},
    ]
    await _add_strength(db_session, 3, exercises)

    response = await client.get(
        "/api/v1/training-balance", params={"days": 28}
    )
    body = response.json()
    groups = body["muscle_groups"]
    assert len(groups) == 2
    # Push (3 sets) should be first
    assert groups[0]["group"] == "Brust/Schulter/Trizeps"
    assert groups[0]["total_sets"] == 3
    assert groups[1]["group"] == "Beine"
    assert groups[1]["total_sets"] == 2


@pytest.mark.anyio
async def test_sport_mix(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Sport mix distribution."""
    await _add_running(db_session, 1, "easy")
    await _add_running(db_session, 3, "easy")
    await _add_running(db_session, 5, "tempo")
    await _add_strength(db_session, 2, [
        {"name": "Planks", "category": "core", "sets": [{"reps": 30}]},
    ])

    response = await client.get(
        "/api/v1/training-balance", params={"days": 28}
    )
    body = response.json()
    mix = body["sport_mix"]
    assert mix["total_sessions"] == 4
    assert mix["running_sessions"] == 3
    assert mix["strength_sessions"] == 1
    assert mix["running_percent"] == 75.0
    assert mix["strength_percent"] == 25.0


@pytest.mark.anyio
async def test_insights_no_strength_warning(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Warning when only running, no strength."""
    for i in range(5):
        await _add_running(db_session, i * 2, "easy")

    response = await client.get(
        "/api/v1/training-balance", params={"days": 28}
    )
    body = response.json()
    categories = [ins["category"] for ins in body["insights"]]
    assert "sport_mix" in categories
    sport_insight = next(
        ins for ins in body["insights"] if ins["category"] == "sport_mix"
    )
    assert sport_insight["type"] == "warning"
    assert "Krafttraining" in sport_insight["message"]


@pytest.mark.anyio
async def test_insights_volume_spike(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Warning when volume increases more than 10%."""
    # Week 1: 10km, Week 2: 20km → 100% increase
    await _add_running(db_session, 14, "easy", 10.0, 3600)
    await _add_running(db_session, 7, "easy", 20.0, 7200)

    response = await client.get(
        "/api/v1/training-balance", params={"days": 28}
    )
    body = response.json()
    volume_insights = [
        ins for ins in body["insights"] if ins["category"] == "volume"
    ]
    assert len(volume_insights) >= 1
    assert volume_insights[0]["type"] == "warning"
    assert "10%" in volume_insights[0]["message"]
