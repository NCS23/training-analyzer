"""Tests for plan generator service and generate endpoint."""

import json
from datetime import date, datetime
from typing import Optional

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    RaceGoalModel,
    TrainingPhaseModel,
    TrainingPlanModel,
)
from app.services.plan_generator import (
    _build_run_details,
    _compute_race_pace,
    _distribute_days,
    _seconds_to_pace,
    generate_weekly_plans,
)

# --- Helpers ---


def _make_plan(
    db: AsyncSession,
    start: str = "2026-04-06",
    end: str = "2026-07-26",
    goal_id: Optional[int] = None,
    rest_days: Optional[list[int]] = None,
) -> TrainingPlanModel:
    ws = json.dumps({"rest_days": rest_days}) if rest_days is not None else None
    plan = TrainingPlanModel(
        name="Test Plan",
        start_date=date.fromisoformat(start),
        end_date=date.fromisoformat(end),
        goal_id=goal_id,
        weekly_structure_json=ws,
        status="draft",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(plan)
    return plan


def _make_phase(
    db: AsyncSession,
    plan_id: int,
    phase_type: str = "base",
    start_week: int = 1,
    end_week: int = 4,
    metrics: Optional[dict] = None,
) -> TrainingPhaseModel:
    phase = TrainingPhaseModel(
        training_plan_id=plan_id,
        name=f"{phase_type} phase",
        phase_type=phase_type,
        start_week=start_week,
        end_week=end_week,
        target_metrics_json=json.dumps(metrics) if metrics else None,
        created_at=datetime.utcnow(),
    )
    db.add(phase)
    return phase


def _make_goal(
    db: AsyncSession,
    distance_km: float = 21.1,
    target_time_seconds: int = 7140,
) -> RaceGoalModel:
    goal = RaceGoalModel(
        title="HM Sub-2h",
        race_date=date(2026, 7, 26),
        distance_km=distance_km,
        target_time_seconds=target_time_seconds,
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(goal)
    return goal


# --- Unit tests for helpers ---


class TestHelpers:
    def test_seconds_to_pace(self) -> None:
        assert _seconds_to_pace(360.0) == "6:00"
        assert _seconds_to_pace(338.0) == "5:38"
        assert _seconds_to_pace(420.5) == "7:00"

    def test_compute_race_pace_with_goal(self) -> None:
        goal = RaceGoalModel(
            title="HM",
            race_date=date(2026, 7, 26),
            distance_km=21.1,
            target_time_seconds=7140,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        pace = _compute_race_pace(goal)
        assert pace is not None
        assert abs(pace - 338.4) < 1.0  # ~5:38/km

    def test_compute_race_pace_without_goal(self) -> None:
        assert _compute_race_pace(None) is None

    def test_build_run_details_with_pace(self) -> None:
        race_pace = 338.4  # 5:38/km
        details = _build_run_details("easy", 8.0, race_pace)
        assert details.run_type == "easy"
        assert details.target_pace_min is not None
        assert details.target_pace_max is not None
        assert details.target_duration_minutes is not None
        assert details.target_duration_minutes > 0

    def test_build_run_details_without_pace(self) -> None:
        details = _build_run_details("easy", 8.0, None)
        assert details.run_type == "easy"
        assert details.target_pace_min is None
        assert details.target_pace_max is None
        assert details.target_duration_minutes is not None  # estimated from ~6:30/km

    def test_distribute_days_respects_rest_days(self) -> None:
        entries = _distribute_days(["easy", "easy", "long_run"], 1, [0, 6])
        days = {e.day_of_week: e for e in entries}
        assert days[0].is_rest_day is True
        assert days[6].is_rest_day is True

    def test_distribute_days_places_long_run_weekend(self) -> None:
        entries = _distribute_days(["easy", "easy", "easy", "long_run"], 0, [6])
        running_entries = [
            e for e in entries
            if e.training_type == "running" and e.run_details is not None
        ]
        long_runs = [e for e in running_entries if e.run_details and e.run_details.run_type == "long_run"]
        assert len(long_runs) == 1
        assert long_runs[0].day_of_week == 5  # Saturday


# --- Integration tests for generate_weekly_plans ---


@pytest.mark.anyio
async def test_generate_basic(db_session: AsyncSession) -> None:
    """Plan with 2 phases → correct number of weeks."""
    plan = _make_plan(db_session, start="2026-04-06", end="2026-06-28")  # ~12 weeks
    await db_session.flush()

    _make_phase(db_session, int(plan.id), "base", 1, 6, {  # type: ignore[arg-type]
        "weekly_volume_min": 30, "weekly_volume_max": 45,
    })
    _make_phase(db_session, int(plan.id), "build", 7, 12, {  # type: ignore[arg-type]
        "weekly_volume_min": 40, "weekly_volume_max": 55,
    })
    await db_session.flush()

    from sqlalchemy import select
    phases = list((await db_session.execute(
        select(TrainingPhaseModel)
        .where(TrainingPhaseModel.training_plan_id == plan.id)
        .order_by(TrainingPhaseModel.start_week)
    )).scalars().all())

    result = generate_weekly_plans(plan, phases, [6], None)
    assert len(result) == 12
    # Each week has 7 entries
    for _, entries in result:
        assert len(entries) == 7


@pytest.mark.anyio
async def test_generate_with_goal_pace(db_session: AsyncSession) -> None:
    """Goal present → RunDetails contain pace ranges."""
    goal = _make_goal(db_session)
    await db_session.flush()

    plan = _make_plan(db_session, start="2026-04-06", end="2026-05-03", goal_id=int(goal.id))  # type: ignore[arg-type]
    await db_session.flush()

    _make_phase(db_session, int(plan.id), "base", 1, 4, {  # type: ignore[arg-type]
        "weekly_volume_min": 30, "weekly_volume_max": 40,
    })
    await db_session.flush()

    from sqlalchemy import select
    phases = list((await db_session.execute(
        select(TrainingPhaseModel)
        .where(TrainingPhaseModel.training_plan_id == plan.id)
    )).scalars().all())

    result = generate_weekly_plans(plan, phases, [6], goal)
    assert len(result) > 0

    # At least one running entry should have pace
    has_pace = False
    for _, entries in result:
        for e in entries:
            if e.run_details and e.run_details.target_pace_min:
                has_pace = True
                break
    assert has_pace, "Expected at least one entry with pace range"


@pytest.mark.anyio
async def test_generate_without_goal(db_session: AsyncSession) -> None:
    """No goal → RunDetails without pace, only duration."""
    plan = _make_plan(db_session, start="2026-04-06", end="2026-05-03")
    await db_session.flush()

    _make_phase(db_session, int(plan.id), "base", 1, 4, {  # type: ignore[arg-type]
        "weekly_volume_min": 30, "weekly_volume_max": 40,
    })
    await db_session.flush()

    from sqlalchemy import select
    phases = list((await db_session.execute(
        select(TrainingPhaseModel)
        .where(TrainingPhaseModel.training_plan_id == plan.id)
    )).scalars().all())

    result = generate_weekly_plans(plan, phases, [6], None)
    assert len(result) > 0

    for _, entries in result:
        for e in entries:
            if e.run_details:
                assert e.run_details.target_pace_min is None
                assert e.run_details.target_pace_max is None


@pytest.mark.anyio
async def test_generate_volume_progression(db_session: AsyncSession) -> None:
    """Volume increases within a phase (week 1 < last week)."""
    plan = _make_plan(db_session, start="2026-04-06", end="2026-06-28")
    await db_session.flush()

    _make_phase(db_session, int(plan.id), "base", 1, 12, {  # type: ignore[arg-type]
        "weekly_volume_min": 20, "weekly_volume_max": 50,
    })
    await db_session.flush()

    from sqlalchemy import select
    phases = list((await db_session.execute(
        select(TrainingPhaseModel)
        .where(TrainingPhaseModel.training_plan_id == plan.id)
    )).scalars().all())

    result = generate_weekly_plans(plan, phases, [6], None)
    assert len(result) >= 2

    # Compute total duration for first and last week
    def week_total_duration(entries: list) -> int:
        total = 0
        for e in entries:
            if e.run_details and e.run_details.target_duration_minutes:
                total += e.run_details.target_duration_minutes
        return total

    first_week_dur = week_total_duration(result[0][1])
    last_week_dur = week_total_duration(result[-1][1])
    assert last_week_dur > first_week_dur, (
        f"Expected last week duration ({last_week_dur}) > first ({first_week_dur})"
    )


@pytest.mark.anyio
async def test_generate_phase_type_sessions(db_session: AsyncSession) -> None:
    """Different phase types produce correct session distributions."""
    plan = _make_plan(db_session, start="2026-04-06", end="2026-05-03")
    await db_session.flush()

    # Peak phase should have intervals + tempo
    _make_phase(db_session, int(plan.id), "peak", 1, 4, {  # type: ignore[arg-type]
        "weekly_volume_min": 45, "weekly_volume_max": 55,
    })
    await db_session.flush()

    from sqlalchemy import select
    phases = list((await db_session.execute(
        select(TrainingPhaseModel)
        .where(TrainingPhaseModel.training_plan_id == plan.id)
    )).scalars().all())

    result = generate_weekly_plans(plan, phases, [6], None)
    assert len(result) > 0

    # Check first week has interval and tempo sessions
    _, entries = result[0]
    run_types = {
        e.run_details.run_type
        for e in entries
        if e.run_details is not None
    }
    assert "intervals" in run_types, f"Expected intervals in peak phase, got {run_types}"
    assert "tempo" in run_types, f"Expected tempo in peak phase, got {run_types}"


# --- API endpoint tests ---


PLAN_DATA = {
    "name": "Generate Test Plan",
    "start_date": "2026-04-06",
    "end_date": "2026-06-28",
    "phases": [
        {
            "name": "Grundlage",
            "phase_type": "base",
            "start_week": 1,
            "end_week": 6,
        },
        {
            "name": "Aufbau",
            "phase_type": "build",
            "start_week": 7,
            "end_week": 12,
        },
    ],
}


@pytest.mark.anyio
async def test_generate_endpoint(client: AsyncClient) -> None:
    """POST /{plan_id}/generate creates weekly plan entries."""
    # Create plan with phases
    create_resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    assert create_resp.status_code == 201
    plan_id = create_resp.json()["id"]

    # Generate
    resp = await client.post(f"/api/v1/training-plans/{plan_id}/generate")
    assert resp.status_code == 200
    body = resp.json()
    assert body["weeks_generated"] > 0
    assert body["total_weeks"] == body["weeks_generated"] + body["weeks_skipped"]


@pytest.mark.anyio
async def test_generate_no_phases(client: AsyncClient) -> None:
    """Plan without phases → 400."""
    create_resp = await client.post(
        "/api/v1/training-plans",
        json={"name": "Empty", "start_date": "2026-04-06", "end_date": "2026-06-28"},
    )
    assert create_resp.status_code == 201
    plan_id = create_resp.json()["id"]

    resp = await client.post(f"/api/v1/training-plans/{plan_id}/generate")
    assert resp.status_code == 400


@pytest.mark.anyio
async def test_generate_plan_not_found(client: AsyncClient) -> None:
    """Non-existent plan → 404."""
    resp = await client.post("/api/v1/training-plans/99999/generate")
    assert resp.status_code == 404


@pytest.mark.anyio
async def test_generate_overwrite_false_skips(client: AsyncClient) -> None:
    """overwrite=false skips existing weeks."""
    create_resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = create_resp.json()["id"]

    # First generate
    resp1 = await client.post(f"/api/v1/training-plans/{plan_id}/generate")
    assert resp1.status_code == 200
    first_generated = resp1.json()["weeks_generated"]

    # Second generate without overwrite
    resp2 = await client.post(
        f"/api/v1/training-plans/{plan_id}/generate",
        json={"overwrite": False},
    )
    assert resp2.status_code == 200
    body = resp2.json()
    assert body["weeks_skipped"] == first_generated
    assert body["weeks_generated"] == 0


@pytest.mark.anyio
async def test_generate_overwrite_true_replaces(client: AsyncClient) -> None:
    """overwrite=true replaces existing weeks."""
    create_resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = create_resp.json()["id"]

    # First generate
    resp1 = await client.post(f"/api/v1/training-plans/{plan_id}/generate")
    first_generated = resp1.json()["weeks_generated"]

    # Second generate with overwrite
    resp2 = await client.post(
        f"/api/v1/training-plans/{plan_id}/generate",
        json={"overwrite": True},
    )
    assert resp2.status_code == 200
    body = resp2.json()
    assert body["weeks_generated"] == first_generated
    assert body["weeks_skipped"] == 0
