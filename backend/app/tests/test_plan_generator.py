"""Tests for plan generator service and generate endpoint."""

import json
from datetime import date, datetime
from typing import Optional

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    RaceGoalModel,
    TrainingPhaseModel,
    TrainingPlanModel,
)
from app.models.training_plan import PhaseWeeklyTemplate, PhaseWeeklyTemplateDayEntry
from app.models.weekly_plan import RunDetails, RunInterval
from app.services.plan_generator import (
    _build_run_details,
    _compute_race_pace,
    _distribute_days,
    _has_explicit_run_details,
    _seconds_to_pace,
    _template_to_entries,
    generate_weekly_plans,
)

# --- Helpers ---


def _first_run_details(entry):  # type: ignore[no-untyped-def]
    """Get run_details from the first session of an entry (or None)."""
    if entry.sessions:
        return entry.sessions[0].run_details
    return None


def _first_training_type(entry):  # type: ignore[no-untyped-def]
    """Get training_type from the first session of an entry (or None)."""
    if entry.sessions:
        return entry.sessions[0].training_type
    return None


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
    weekly_template: Optional[dict] = None,
) -> TrainingPhaseModel:
    phase = TrainingPhaseModel(
        training_plan_id=plan_id,
        name=f"{phase_type} phase",
        phase_type=phase_type,
        start_week=start_week,
        end_week=end_week,
        target_metrics_json=json.dumps(metrics) if metrics else None,
        weekly_template_json=json.dumps(weekly_template) if weekly_template else None,
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
            e
            for e in entries
            if _first_training_type(e) == "running" and _first_run_details(e) is not None
        ]
        long_runs = [
            e
            for e in running_entries
            if _first_run_details(e) and _first_run_details(e).run_type == "long_run"
        ]
        assert len(long_runs) == 1
        assert long_runs[0].day_of_week == 5  # Saturday


# --- Template tests ---


def _day(
    day: int,
    training_type: Optional[str] = None,
    run_type: Optional[str] = None,
    is_rest_day: bool = False,
) -> PhaseWeeklyTemplateDayEntry:
    return PhaseWeeklyTemplateDayEntry(
        day_of_week=day,
        training_type=training_type,
        is_rest_day=is_rest_day,
        run_type=run_type,
        template_id=None,
        notes=None,
    )


SAMPLE_TEMPLATE = PhaseWeeklyTemplate(
    days=[
        _day(0, "running", "easy"),
        _day(1, "strength"),
        _day(2, "running", "tempo"),
        _day(3, "running", "easy"),
        _day(4, "running", "intervals"),
        _day(5, "running", "long_run"),
        _day(6, is_rest_day=True),
    ]
)


class TestTemplateToEntries:
    def test_template_produces_7_entries(self) -> None:
        entries = _template_to_entries(SAMPLE_TEMPLATE)
        assert len(entries) == 7

    def test_template_preserves_run_types(self) -> None:
        entries = _template_to_entries(SAMPLE_TEMPLATE)
        run_types = {
            e.day_of_week: _first_run_details(e).run_type
            for e in entries
            if _first_run_details(e) is not None
        }
        assert run_types[0] == "easy"
        assert run_types[2] == "tempo"
        assert run_types[4] == "intervals"
        assert run_types[5] == "long_run"

    def test_template_preserves_strength(self) -> None:
        entries = _template_to_entries(SAMPLE_TEMPLATE)
        assert _first_training_type(entries[1]) == "strength"
        assert _first_run_details(entries[1]) is None

    def test_template_preserves_rest_day(self) -> None:
        entries = _template_to_entries(SAMPLE_TEMPLATE)
        assert entries[6].is_rest_day is True
        assert len(entries[6].sessions) == 0

    def test_template_with_explicit_run_details(self) -> None:
        """Template RunDetails are passed through 1:1."""
        explicit_rd = RunDetails(
            run_type="easy",
            target_duration_minutes=45,
            target_pace_min="5:40",
            target_pace_max="6:10",
            target_hr_min=None,
            target_hr_max=None,
            intervals=None,
        )
        template = PhaseWeeklyTemplate(
            days=[
                PhaseWeeklyTemplateDayEntry(
                    day_of_week=0,
                    training_type="running",
                    run_type="easy",
                    template_id=None,
                    notes=None,
                    run_details=explicit_rd,
                ),
                *[_day(d, is_rest_day=True) for d in range(1, 7)],
            ]
        )
        entries = _template_to_entries(template)
        rd = _first_run_details(entries[0])
        assert rd is not None
        assert rd.target_duration_minutes == 45
        assert rd.target_pace_min == "5:40"
        assert rd.target_pace_max == "6:10"

    def test_template_with_interval_run_details(self) -> None:
        """Template with intervals in RunDetails."""
        intervals = [
            RunInterval(
                type="warmup",
                duration_minutes=10,
                repeats=1,
                target_pace_min=None,
                target_pace_max=None,
                target_hr_min=None,
                target_hr_max=None,
            ),
            RunInterval(
                type="work",
                duration_minutes=3,
                target_pace_min="4:20",
                target_pace_max=None,
                target_hr_min=None,
                target_hr_max=None,
                repeats=5,
            ),
            RunInterval(
                type="recovery_jog",
                duration_minutes=2,
                repeats=5,
                target_pace_min=None,
                target_pace_max=None,
                target_hr_min=None,
                target_hr_max=None,
            ),
            RunInterval(
                type="cooldown",
                duration_minutes=10,
                repeats=1,
                target_pace_min=None,
                target_pace_max=None,
                target_hr_min=None,
                target_hr_max=None,
            ),
        ]
        explicit_rd = RunDetails(
            run_type="intervals",
            target_duration_minutes=60,
            target_pace_min=None,
            target_pace_max=None,
            target_hr_min=None,
            target_hr_max=None,
            intervals=intervals,
        )
        template = PhaseWeeklyTemplate(
            days=[
                PhaseWeeklyTemplateDayEntry(
                    day_of_week=0,
                    training_type="running",
                    run_type="intervals",
                    template_id=None,
                    notes=None,
                    run_details=explicit_rd,
                ),
                *[_day(d, is_rest_day=True) for d in range(1, 7)],
            ]
        )
        entries = _template_to_entries(template)
        rd = _first_run_details(entries[0])
        assert rd is not None
        assert rd.run_type == "intervals"
        assert rd.intervals is not None
        assert len(rd.intervals) == 4
        assert rd.intervals[1].type == "work"
        assert rd.intervals[1].repeats == 5

    def test_template_without_run_details_creates_skeleton(self) -> None:
        """Without run_details on template entry, a skeleton is created."""
        template = PhaseWeeklyTemplate(
            days=[
                _day(0, "running", "easy"),
                *[_day(d, is_rest_day=True) for d in range(1, 7)],
            ]
        )
        entries = _template_to_entries(template)
        rd = _first_run_details(entries[0])
        assert rd is not None
        assert rd.run_type == "easy"
        assert rd.target_duration_minutes is None
        assert rd.target_pace_min is None
        assert rd.intervals is None


class TestHasExplicitRunDetails:
    def test_skeleton_is_not_explicit(self) -> None:
        rd = RunDetails(
            run_type="easy",
            target_duration_minutes=None,
            target_pace_min=None,
            target_pace_max=None,
            target_hr_min=None,
            target_hr_max=None,
            intervals=None,
        )
        assert _has_explicit_run_details(rd) is False

    def test_duration_makes_explicit(self) -> None:
        rd = RunDetails(
            run_type="easy",
            target_duration_minutes=45,
            target_pace_min=None,
            target_pace_max=None,
            target_hr_min=None,
            target_hr_max=None,
            intervals=None,
        )
        assert _has_explicit_run_details(rd) is True

    def test_pace_makes_explicit(self) -> None:
        rd = RunDetails(
            run_type="tempo",
            target_duration_minutes=None,
            target_pace_min="5:00",
            target_pace_max=None,
            target_hr_min=None,
            target_hr_max=None,
            intervals=None,
        )
        assert _has_explicit_run_details(rd) is True

    def test_intervals_make_explicit(self) -> None:
        rd = RunDetails(
            run_type="intervals",
            target_duration_minutes=None,
            target_pace_min=None,
            target_pace_max=None,
            target_hr_min=None,
            target_hr_max=None,
            intervals=[
                RunInterval(
                    type="work",
                    duration_minutes=3,
                    repeats=5,
                    target_pace_min=None,
                    target_pace_max=None,
                    target_hr_min=None,
                    target_hr_max=None,
                )
            ],
        )
        assert _has_explicit_run_details(rd) is True


# --- Integration tests for generate_weekly_plans ---


@pytest.mark.anyio
async def test_generate_basic(db_session: AsyncSession) -> None:
    """Plan with 2 phases → correct number of weeks."""
    plan = _make_plan(db_session, start="2026-04-06", end="2026-06-28")  # ~12 weeks
    await db_session.flush()

    _make_phase(
        db_session,
        int(plan.id),
        "base",
        1,
        6,
        {  # type: ignore[arg-type]
            "weekly_volume_min": 30,
            "weekly_volume_max": 45,
        },
    )
    _make_phase(
        db_session,
        int(plan.id),
        "build",
        7,
        12,
        {  # type: ignore[arg-type]
            "weekly_volume_min": 40,
            "weekly_volume_max": 55,
        },
    )
    await db_session.flush()

    from sqlalchemy import select

    phases = list(
        (
            await db_session.execute(
                select(TrainingPhaseModel)
                .where(TrainingPhaseModel.training_plan_id == plan.id)
                .order_by(TrainingPhaseModel.start_week)
            )
        )
        .scalars()
        .all()
    )

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

    _make_phase(
        db_session,
        int(plan.id),
        "base",
        1,
        4,
        {  # type: ignore[arg-type]
            "weekly_volume_min": 30,
            "weekly_volume_max": 40,
        },
    )
    await db_session.flush()

    from sqlalchemy import select

    phases = list(
        (
            await db_session.execute(
                select(TrainingPhaseModel).where(TrainingPhaseModel.training_plan_id == plan.id)
            )
        )
        .scalars()
        .all()
    )

    result = generate_weekly_plans(plan, phases, [6], goal)
    assert len(result) > 0

    # At least one running session should have pace
    has_pace = False
    for _, entries in result:
        for e in entries:
            rd = _first_run_details(e)
            if rd and rd.target_pace_min:
                has_pace = True
                break
    assert has_pace, "Expected at least one entry with pace range"


@pytest.mark.anyio
async def test_generate_without_goal(db_session: AsyncSession) -> None:
    """No goal → RunDetails without pace, only duration."""
    plan = _make_plan(db_session, start="2026-04-06", end="2026-05-03")
    await db_session.flush()

    _make_phase(
        db_session,
        int(plan.id),
        "base",
        1,
        4,
        {  # type: ignore[arg-type]
            "weekly_volume_min": 30,
            "weekly_volume_max": 40,
        },
    )
    await db_session.flush()

    from sqlalchemy import select

    phases = list(
        (
            await db_session.execute(
                select(TrainingPhaseModel).where(TrainingPhaseModel.training_plan_id == plan.id)
            )
        )
        .scalars()
        .all()
    )

    result = generate_weekly_plans(plan, phases, [6], None)
    assert len(result) > 0

    for _, entries in result:
        for e in entries:
            rd = _first_run_details(e)
            if rd:
                assert rd.target_pace_min is None
                assert rd.target_pace_max is None


@pytest.mark.anyio
async def test_generate_volume_progression(db_session: AsyncSession) -> None:
    """Volume increases within a phase (week 1 < last week)."""
    plan = _make_plan(db_session, start="2026-04-06", end="2026-06-28")
    await db_session.flush()

    _make_phase(
        db_session,
        int(plan.id),
        "base",
        1,
        12,
        {  # type: ignore[arg-type]
            "weekly_volume_min": 20,
            "weekly_volume_max": 50,
        },
    )
    await db_session.flush()

    from sqlalchemy import select

    phases = list(
        (
            await db_session.execute(
                select(TrainingPhaseModel).where(TrainingPhaseModel.training_plan_id == plan.id)
            )
        )
        .scalars()
        .all()
    )

    result = generate_weekly_plans(plan, phases, [6], None)
    assert len(result) >= 2

    # Compute total duration for first and last week
    def week_total_duration(entries: list) -> int:
        total = 0
        for e in entries:
            rd = _first_run_details(e)
            if rd and rd.target_duration_minutes:
                total += rd.target_duration_minutes
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
    _make_phase(
        db_session,
        int(plan.id),
        "peak",
        1,
        4,
        {  # type: ignore[arg-type]
            "weekly_volume_min": 45,
            "weekly_volume_max": 55,
        },
    )
    await db_session.flush()

    from sqlalchemy import select

    phases = list(
        (
            await db_session.execute(
                select(TrainingPhaseModel).where(TrainingPhaseModel.training_plan_id == plan.id)
            )
        )
        .scalars()
        .all()
    )

    result = generate_weekly_plans(plan, phases, [6], None)
    assert len(result) > 0

    # Check first week has interval and tempo sessions
    _, entries = result[0]
    run_types = {
        _first_run_details(e).run_type for e in entries if _first_run_details(e) is not None
    }
    assert "intervals" in run_types, f"Expected intervals in peak phase, got {run_types}"
    assert "tempo" in run_types, f"Expected tempo in peak phase, got {run_types}"


# --- Template integration tests ---


TEMPLATE_JSON = {
    "days": [
        {"day_of_week": 0, "training_type": "running", "run_type": "easy"},
        {"day_of_week": 1, "training_type": "strength"},
        {"day_of_week": 2, "training_type": "running", "run_type": "tempo"},
        {"day_of_week": 3, "training_type": "running", "run_type": "easy"},
        {"day_of_week": 4, "training_type": "running", "run_type": "intervals"},
        {"day_of_week": 5, "training_type": "running", "run_type": "long_run"},
        {"day_of_week": 6, "is_rest_day": True},
    ]
}


@pytest.mark.anyio
async def test_generate_with_template(db_session: AsyncSession) -> None:
    """Phase with weekly_template → entries match template exactly."""
    plan = _make_plan(db_session, start="2026-04-06", end="2026-05-03")
    await db_session.flush()

    _make_phase(
        db_session,
        int(plan.id),
        "build",
        1,
        4,
        {  # type: ignore[arg-type]
            "weekly_volume_min": 30,
            "weekly_volume_max": 40,
        },
        weekly_template=TEMPLATE_JSON,
    )
    await db_session.flush()

    from sqlalchemy import select

    phases = list(
        (
            await db_session.execute(
                select(TrainingPhaseModel).where(TrainingPhaseModel.training_plan_id == plan.id)
            )
        )
        .scalars()
        .all()
    )

    result = generate_weekly_plans(plan, phases, [6], None)
    assert len(result) > 0

    _, entries = result[0]
    assert len(entries) == 7

    # Verify template structure is preserved
    assert _first_training_type(entries[0]) == "running"
    assert _first_run_details(entries[0]) is not None
    assert _first_run_details(entries[0]).run_type == "easy"
    assert _first_training_type(entries[1]) == "strength"
    assert _first_run_details(entries[2]) is not None
    assert _first_run_details(entries[2]).run_type == "tempo"
    assert entries[6].is_rest_day is True


@pytest.mark.anyio
async def test_generate_template_with_volume(db_session: AsyncSession) -> None:
    """Template + volume metrics → RunDetails get duration/pace filled in."""
    goal = _make_goal(db_session)
    await db_session.flush()

    plan = _make_plan(db_session, start="2026-04-06", end="2026-05-03", goal_id=int(goal.id))  # type: ignore[arg-type]
    await db_session.flush()

    _make_phase(
        db_session,
        int(plan.id),
        "build",
        1,
        4,
        {  # type: ignore[arg-type]
            "weekly_volume_min": 35,
            "weekly_volume_max": 45,
        },
        weekly_template=TEMPLATE_JSON,
    )
    await db_session.flush()

    from sqlalchemy import select

    phases = list(
        (
            await db_session.execute(
                select(TrainingPhaseModel).where(TrainingPhaseModel.training_plan_id == plan.id)
            )
        )
        .scalars()
        .all()
    )

    result = generate_weekly_plans(plan, phases, [6], goal)
    assert len(result) > 0

    _, entries = result[0]
    # Running sessions should have duration and pace filled
    running_with_details = [
        e
        for e in entries
        if _first_run_details(e) and _first_run_details(e).target_duration_minutes
    ]
    assert len(running_with_details) > 0
    # At least one should have pace (because goal is set)
    has_pace = any(
        _first_run_details(e).target_pace_min
        for e in running_with_details
        if _first_run_details(e)
    )
    assert has_pace


@pytest.mark.anyio
async def test_generate_mixed_phases(db_session: AsyncSession) -> None:
    """One phase with template, one without → both work correctly."""
    plan = _make_plan(db_session, start="2026-04-06", end="2026-06-28")
    await db_session.flush()

    # Phase 1: with template
    _make_phase(
        db_session,
        int(plan.id),
        "base",
        1,
        6,
        {  # type: ignore[arg-type]
            "weekly_volume_min": 30,
            "weekly_volume_max": 40,
        },
        weekly_template=TEMPLATE_JSON,
    )
    # Phase 2: without template (fallback to PHASE_DEFAULTS)
    _make_phase(
        db_session,
        int(plan.id),
        "build",
        7,
        12,
        {  # type: ignore[arg-type]
            "weekly_volume_min": 40,
            "weekly_volume_max": 55,
        },
    )
    await db_session.flush()

    from sqlalchemy import select

    phases = list(
        (
            await db_session.execute(
                select(TrainingPhaseModel)
                .where(TrainingPhaseModel.training_plan_id == plan.id)
                .order_by(TrainingPhaseModel.start_week)
            )
        )
        .scalars()
        .all()
    )

    result = generate_weekly_plans(plan, phases, [6], None)
    assert len(result) == 12

    # Week 1 (template phase): should match template
    _, week1_entries = result[0]
    assert _first_training_type(week1_entries[1]) == "strength"  # day 1 = strength from template

    # Week 7 (defaults phase): should have entries generated from defaults
    _, week7_entries = result[6]
    assert len(week7_entries) == 7
    # build phase defaults have progression run
    run_types = {
        _first_run_details(e).run_type for e in week7_entries if _first_run_details(e) is not None
    }
    assert "progression" in run_types


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
    assert body["total_weeks"] == body["weeks_generated"]


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
async def test_generate_replaces_previous(client: AsyncClient) -> None:
    """Re-generating always replaces previous entries for the same plan."""
    create_resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = create_resp.json()["id"]

    # First generate
    resp1 = await client.post(f"/api/v1/training-plans/{plan_id}/generate")
    assert resp1.status_code == 200
    first_generated = resp1.json()["weeks_generated"]

    # Second generate — should replace, not skip
    resp2 = await client.post(f"/api/v1/training-plans/{plan_id}/generate")
    assert resp2.status_code == 200
    body = resp2.json()
    assert body["weeks_generated"] == first_generated

    # Verify via weekly plan API: first week should have entries
    week_resp = await client.get("/api/v1/weekly-plan", params={"week_start": "2026-04-06"})
    assert week_resp.status_code == 200
    entries = week_resp.json()["entries"]
    has_content = any(len(e["sessions"]) > 0 or e["is_rest_day"] for e in entries)
    assert has_content


@pytest.mark.anyio
async def test_generate_preserves_template_run_details(db_session: AsyncSession) -> None:
    """Volume distribution must NOT overwrite explicit template RunDetails."""
    plan = _make_plan(db_session, start="2026-04-06", end="2026-04-26", rest_days=[6])
    await db_session.flush()

    explicit_easy = RunDetails(
        run_type="easy",
        target_duration_minutes=45,
        target_pace_min="5:40",
        target_pace_max="6:10",
        target_hr_min=None,
        target_hr_max=None,
        intervals=None,
    ).model_dump()
    template = {
        "days": [
            {
                "day_of_week": 0,
                "training_type": "running",
                "run_type": "easy",
                "is_rest_day": False,
                "run_details": explicit_easy,
            },
            {
                "day_of_week": 1,
                "training_type": "running",
                "run_type": "easy",
                "is_rest_day": False,
            },  # no run_details → skeleton → will be filled
            {
                "day_of_week": 2,
                "training_type": "running",
                "run_type": "tempo",
                "is_rest_day": False,
            },
            {
                "day_of_week": 3,
                "training_type": "running",
                "run_type": "easy",
                "is_rest_day": False,
            },
            {"day_of_week": 4, "training_type": "strength", "is_rest_day": False},
            {
                "day_of_week": 5,
                "training_type": "running",
                "run_type": "long_run",
                "is_rest_day": False,
            },
            {"day_of_week": 6, "is_rest_day": True},
        ]
    }
    _make_phase(
        db_session,
        int(plan.id),
        "base",
        1,
        3,
        metrics={"weekly_volume_min": 30, "weekly_volume_max": 45},
        weekly_template=template,
    )
    goal = _make_goal(db_session)
    await db_session.flush()

    plan.goal_id = goal.id
    # _make_phase added to db_session but plan.phases won't auto-load;
    # we need the actual phase objects
    phases_result = await db_session.execute(
        select(TrainingPhaseModel).where(TrainingPhaseModel.training_plan_id == plan.id)
    )
    phases = list(phases_result.scalars().all())

    result = generate_weekly_plans(plan, phases, [6], goal)
    assert len(result) > 0

    _, entries = result[0]
    # Day 0: had explicit run_details → must be preserved
    day0 = next(e for e in entries if e.day_of_week == 0)
    rd0 = _first_run_details(day0)
    assert rd0 is not None
    assert rd0.target_duration_minutes == 45
    assert rd0.target_pace_min == "5:40"
    assert rd0.target_pace_max == "6:10"

    # Day 1: had skeleton → should be filled by volume distribution
    day1 = next(e for e in entries if e.day_of_week == 1)
    rd1 = _first_run_details(day1)
    assert rd1 is not None
    assert rd1.target_duration_minutes is not None
    assert rd1.target_duration_minutes != 45  # different from template


@pytest.mark.anyio
async def test_generate_fills_skeleton_run_details(db_session: AsyncSession) -> None:
    """Skeleton RunDetails (no explicit values) get filled with volume/pace."""
    plan = _make_plan(db_session, start="2026-04-06", end="2026-04-19", rest_days=[6])
    await db_session.flush()

    # Template without any run_details
    template = {
        "days": [
            {"day_of_week": d, "training_type": "running", "run_type": "easy", "is_rest_day": False}
            if d < 5
            else (
                {
                    "day_of_week": 5,
                    "training_type": "running",
                    "run_type": "long_run",
                    "is_rest_day": False,
                }
                if d == 5
                else {"day_of_week": 6, "is_rest_day": True}
            )
            for d in range(7)
        ]
    }
    _make_phase(
        db_session,
        int(plan.id),
        "base",
        1,
        2,
        metrics={"weekly_volume_min": 30, "weekly_volume_max": 35},
        weekly_template=template,
    )
    goal = _make_goal(db_session)
    await db_session.flush()
    plan.goal_id = goal.id

    phases_result = await db_session.execute(
        select(TrainingPhaseModel).where(TrainingPhaseModel.training_plan_id == plan.id)
    )
    phases = list(phases_result.scalars().all())

    result = generate_weekly_plans(plan, phases, [6], goal)
    assert len(result) > 0
    _, entries = result[0]

    running = [e for e in entries if _first_run_details(e) is not None]
    assert len(running) >= 4
    # All skeleton entries should now have duration and pace filled
    for e in running:
        rd = _first_run_details(e)
        assert rd is not None
        assert rd.target_duration_minutes is not None
        assert rd.target_pace_min is not None


@pytest.mark.anyio
async def test_generate_cleans_legacy_entries(client: AsyncClient) -> None:
    """Generating cleans up legacy entries (plan_id=NULL) for covered weeks."""
    # Create a manual entry first (simulates old data without plan_id)
    manual_resp = await client.put(
        "/api/v1/weekly-plan",
        json={
            "week_start": "2026-04-06",
            "entries": [
                {
                    "day_of_week": 0,
                    "is_rest_day": False,
                    "sessions": [{"training_type": "strength", "position": 0}],
                }
            ],
        },
    )
    assert manual_resp.status_code == 200

    # Now create a plan covering that week and generate
    create_resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = create_resp.json()["id"]

    resp = await client.post(f"/api/v1/training-plans/{plan_id}/generate")
    assert resp.status_code == 200
    assert resp.json()["weeks_generated"] > 0
