"""Tests for Weekly Plan (Issue #26, #28)."""

from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import WorkoutModel

PLAN_DATA = {
    "name": "Test Plan",
    "description": "Für Wochenplan-Tests",
    "session_type": "strength",
    "exercises": [
        {
            "name": "Kniebeugen",
            "category": "legs",
            "sets": 4,
            "reps": 8,
            "weight_kg": 80,
            "exercise_type": "kraft",
        },
    ],
}


@pytest.mark.anyio
async def test_get_empty_week(client: AsyncClient) -> None:
    """An empty week should return 7 entries, all with no training."""
    response = await client.get(
        "/api/v1/weekly-plan", params={"week_start": "2026-03-02"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["week_start"] == "2026-03-02"
    assert len(body["entries"]) == 7
    # All days should be empty
    for i, entry in enumerate(body["entries"]):
        assert entry["day_of_week"] == i
        assert entry["training_type"] is None
        assert entry["is_rest_day"] is False


@pytest.mark.anyio
async def test_get_empty_week_normalizes_to_monday(client: AsyncClient) -> None:
    """Passing a Wednesday should still return the Monday."""
    response = await client.get(
        "/api/v1/weekly-plan", params={"week_start": "2026-03-04"}  # Wednesday
    )
    assert response.status_code == 200
    assert response.json()["week_start"] == "2026-03-02"  # Monday


@pytest.mark.anyio
async def test_save_and_get_weekly_plan(client: AsyncClient) -> None:
    """Save a plan for a week and retrieve it."""
    data = {
        "week_start": "2026-03-02",
        "entries": [
            {"day_of_week": 0, "training_type": "strength", "is_rest_day": False},
            {"day_of_week": 1, "training_type": "running", "is_rest_day": False},
            {"day_of_week": 2, "is_rest_day": True},
            {"day_of_week": 3, "training_type": "strength", "is_rest_day": False, "notes": "Beintraining"},
            {"day_of_week": 4, "training_type": "running", "is_rest_day": False},
            {"day_of_week": 5, "is_rest_day": True},
            {"day_of_week": 6, "training_type": "running", "is_rest_day": False, "notes": "Langer Lauf"},
        ],
    }

    response = await client.put("/api/v1/weekly-plan", json=data)
    assert response.status_code == 200
    body = response.json()
    assert len(body["entries"]) == 7
    assert body["entries"][0]["training_type"] == "strength"
    assert body["entries"][1]["training_type"] == "running"
    assert body["entries"][2]["is_rest_day"] is True
    assert body["entries"][2]["training_type"] is None
    assert body["entries"][3]["notes"] == "Beintraining"
    assert body["entries"][6]["notes"] == "Langer Lauf"

    # Verify with GET
    get_response = await client.get(
        "/api/v1/weekly-plan", params={"week_start": "2026-03-02"}
    )
    assert get_response.status_code == 200
    get_body = get_response.json()
    assert get_body["entries"][0]["training_type"] == "strength"


@pytest.mark.anyio
async def test_save_weekly_plan_with_template_id(client: AsyncClient) -> None:
    """Save a plan entry referencing a session template."""
    # Create a session template first
    template_response = await client.post("/api/v1/session-templates", json=PLAN_DATA)
    assert template_response.status_code == 201
    template_id = template_response.json()["id"]

    data = {
        "week_start": "2026-03-09",
        "entries": [
            {
                "day_of_week": 0,
                "training_type": "strength",
                "template_id": template_id,
                "is_rest_day": False,
            },
        ],
    }

    response = await client.put("/api/v1/weekly-plan", json=data)
    assert response.status_code == 200
    body = response.json()
    # Monday should have the template
    assert body["entries"][0]["template_id"] == template_id
    assert body["entries"][0]["template_name"] == "Test Plan"


@pytest.mark.anyio
async def test_save_replaces_existing(client: AsyncClient) -> None:
    """Saving a new plan replaces the old one."""
    first_data = {
        "week_start": "2026-03-16",
        "entries": [
            {"day_of_week": 0, "training_type": "strength", "is_rest_day": False},
            {"day_of_week": 1, "training_type": "running", "is_rest_day": False},
        ],
    }
    await client.put("/api/v1/weekly-plan", json=first_data)

    # Now save a different plan for the same week
    second_data = {
        "week_start": "2026-03-16",
        "entries": [
            {"day_of_week": 0, "is_rest_day": True},
            {"day_of_week": 2, "training_type": "running", "is_rest_day": False},
        ],
    }
    response = await client.put("/api/v1/weekly-plan", json=second_data)
    assert response.status_code == 200
    body = response.json()
    assert body["entries"][0]["is_rest_day"] is True
    assert body["entries"][0]["training_type"] is None
    assert body["entries"][2]["training_type"] == "running"
    # Tuesday (1) should now be empty
    assert body["entries"][1]["training_type"] is None
    assert body["entries"][1]["is_rest_day"] is False


@pytest.mark.anyio
async def test_duplicate_day_rejected(client: AsyncClient) -> None:
    """Duplicate day_of_week in request should be rejected."""
    data = {
        "week_start": "2026-03-02",
        "entries": [
            {"day_of_week": 0, "training_type": "strength", "is_rest_day": False},
            {"day_of_week": 0, "training_type": "running", "is_rest_day": False},
        ],
    }
    response = await client.put("/api/v1/weekly-plan", json=data)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_clear_weekly_plan(client: AsyncClient) -> None:
    """Clearing a week should remove all entries."""
    # First save
    data = {
        "week_start": "2026-03-23",
        "entries": [
            {"day_of_week": 0, "training_type": "strength", "is_rest_day": False},
        ],
    }
    await client.put("/api/v1/weekly-plan", json=data)

    # Clear
    response = await client.delete(
        "/api/v1/weekly-plan", params={"week_start": "2026-03-23"}
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify empty
    get_response = await client.get(
        "/api/v1/weekly-plan", params={"week_start": "2026-03-23"}
    )
    assert get_response.status_code == 200
    for entry in get_response.json()["entries"]:
        assert entry["training_type"] is None
        assert entry["is_rest_day"] is False


@pytest.mark.anyio
async def test_partial_week_save(client: AsyncClient) -> None:
    """Saving only 3 days should still return 7 entries (others empty)."""
    data = {
        "week_start": "2026-03-30",
        "entries": [
            {"day_of_week": 0, "training_type": "strength", "is_rest_day": False},
            {"day_of_week": 3, "training_type": "running", "is_rest_day": False},
            {"day_of_week": 6, "is_rest_day": True},
        ],
    }
    response = await client.put("/api/v1/weekly-plan", json=data)
    assert response.status_code == 200
    body = response.json()
    assert len(body["entries"]) == 7
    assert body["entries"][0]["training_type"] == "strength"
    assert body["entries"][1]["training_type"] is None  # empty day
    assert body["entries"][3]["training_type"] == "running"
    assert body["entries"][6]["is_rest_day"] is True


@pytest.mark.anyio
async def test_save_with_run_details(client: AsyncClient) -> None:
    """Save a running day with detailed run planning info."""
    data = {
        "week_start": "2026-04-06",
        "entries": [
            {
                "day_of_week": 0,
                "training_type": "running",
                "is_rest_day": False,
                "run_details": {
                    "run_type": "easy",
                    "target_duration_minutes": 45,
                    "target_pace_min": "5:30",
                    "target_pace_max": "6:00",
                },
            },
        ],
    }

    response = await client.put("/api/v1/weekly-plan", json=data)
    assert response.status_code == 200
    body = response.json()
    entry = body["entries"][0]
    assert entry["training_type"] == "running"
    assert entry["run_details"] is not None
    assert entry["run_details"]["run_type"] == "easy"
    assert entry["run_details"]["target_duration_minutes"] == 45
    assert entry["run_details"]["target_pace_min"] == "5:30"
    assert entry["run_details"]["target_pace_max"] == "6:00"


@pytest.mark.anyio
async def test_save_with_intervals(client: AsyncClient) -> None:
    """Save an interval session with structured workout."""
    data = {
        "week_start": "2026-04-06",
        "entries": [
            {
                "day_of_week": 2,
                "training_type": "running",
                "is_rest_day": False,
                "run_details": {
                    "run_type": "intervals",
                    "target_duration_minutes": 60,
                    "intervals": [
                        {
                            "type": "warmup",
                            "duration_minutes": 10,
                            "target_pace_min": "6:00",
                            "target_pace_max": "6:30",
                            "repeats": 1,
                        },
                        {
                            "type": "work",
                            "duration_minutes": 3,
                            "target_pace_min": "4:30",
                            "target_pace_max": "4:50",
                            "repeats": 5,
                        },
                        {
                            "type": "rest",
                            "duration_minutes": 2,
                            "target_pace_min": "6:00",
                            "target_pace_max": "7:00",
                            "repeats": 5,
                        },
                        {
                            "type": "cooldown",
                            "duration_minutes": 10,
                            "target_pace_min": "6:00",
                            "target_pace_max": "6:30",
                            "repeats": 1,
                        },
                    ],
                },
            },
        ],
    }

    response = await client.put("/api/v1/weekly-plan", json=data)
    assert response.status_code == 200
    body = response.json()
    entry = body["entries"][2]
    assert entry["run_details"]["run_type"] == "intervals"
    assert len(entry["run_details"]["intervals"]) == 4
    work = entry["run_details"]["intervals"][1]
    assert work["type"] == "work"
    assert work["duration_minutes"] == 3
    assert work["repeats"] == 5


@pytest.mark.anyio
async def test_run_details_with_hr_targets(client: AsyncClient) -> None:
    """Save a running day with heart rate targets."""
    data = {
        "week_start": "2026-04-13",
        "entries": [
            {
                "day_of_week": 0,
                "training_type": "running",
                "is_rest_day": False,
                "run_details": {
                    "run_type": "tempo",
                    "target_duration_minutes": 40,
                    "target_hr_min": 155,
                    "target_hr_max": 170,
                },
            },
        ],
    }

    response = await client.put("/api/v1/weekly-plan", json=data)
    assert response.status_code == 200
    entry = response.json()["entries"][0]
    assert entry["run_details"]["run_type"] == "tempo"
    assert entry["run_details"]["target_hr_min"] == 155
    assert entry["run_details"]["target_hr_max"] == 170


@pytest.mark.anyio
async def test_empty_entries_have_no_run_details(client: AsyncClient) -> None:
    """Empty and non-running entries should not have run_details."""
    response = await client.get(
        "/api/v1/weekly-plan", params={"week_start": "2026-05-01"}
    )
    assert response.status_code == 200
    for entry in response.json()["entries"]:
        assert entry["run_details"] is None


# --- Compliance Tracking Tests (Issue #28) ---


async def _create_workout(
    db: AsyncSession,
    date_str: str,
    workout_type: str = "running",
    training_type_auto: str = "easy",
) -> int:
    """Helper to create a workout directly in DB."""
    workout = WorkoutModel(
        date=datetime.fromisoformat(date_str),
        workout_type=workout_type,
        training_type_auto=training_type_auto,
        duration_sec=2700,
        distance_km=5.0 if workout_type == "running" else None,
        pace="5:30" if workout_type == "running" else None,
    )
    db.add(workout)
    await db.commit()
    await db.refresh(workout)
    return int(workout.id)  # type: ignore[arg-type]


@pytest.mark.anyio
async def test_compliance_empty_week(client: AsyncClient) -> None:
    """Empty week with no plan and no sessions → all 'empty'."""
    response = await client.get(
        "/api/v1/weekly-plan/compliance", params={"week_start": "2026-06-01"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["week_start"] == "2026-06-01"
    assert len(body["entries"]) == 7
    assert body["completed_count"] == 0
    assert body["planned_count"] == 0
    for entry in body["entries"]:
        assert entry["status"] == "empty"
        assert entry["actual_sessions"] == []


@pytest.mark.anyio
async def test_compliance_completed(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Plan running on Monday, actual running on Monday → 'completed'."""
    # Week of 2026-06-08 (Monday)
    plan_data = {
        "week_start": "2026-06-08",
        "entries": [
            {"day_of_week": 0, "training_type": "running", "is_rest_day": False},
        ],
    }
    await client.put("/api/v1/weekly-plan", json=plan_data)

    # Create actual running session on Monday
    await _create_workout(db_session, "2026-06-08T08:00:00", "running", "easy")

    response = await client.get(
        "/api/v1/weekly-plan/compliance", params={"week_start": "2026-06-08"}
    )
    assert response.status_code == 200
    body = response.json()
    monday = body["entries"][0]
    assert monday["status"] == "completed"
    assert monday["planned_type"] == "running"
    assert len(monday["actual_sessions"]) == 1
    assert monday["actual_sessions"][0]["workout_type"] == "running"
    assert body["completed_count"] == 1
    assert body["planned_count"] == 1


@pytest.mark.anyio
async def test_compliance_missed(client: AsyncClient) -> None:
    """Plan running on Tuesday, no session → 'missed'."""
    plan_data = {
        "week_start": "2026-06-15",
        "entries": [
            {"day_of_week": 1, "training_type": "running", "is_rest_day": False},
        ],
    }
    await client.put("/api/v1/weekly-plan", json=plan_data)

    response = await client.get(
        "/api/v1/weekly-plan/compliance", params={"week_start": "2026-06-15"}
    )
    body = response.json()
    tuesday = body["entries"][1]
    assert tuesday["status"] == "missed"
    assert tuesday["planned_type"] == "running"
    assert body["completed_count"] == 0
    assert body["planned_count"] == 1


@pytest.mark.anyio
async def test_compliance_off_target(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Plan strength on Wednesday, actual running → 'off_target'."""
    plan_data = {
        "week_start": "2026-06-22",
        "entries": [
            {"day_of_week": 2, "training_type": "strength", "is_rest_day": False},
        ],
    }
    await client.put("/api/v1/weekly-plan", json=plan_data)

    # Create running session on Wednesday (instead of strength)
    await _create_workout(db_session, "2026-06-24T09:00:00", "running", "easy")

    response = await client.get(
        "/api/v1/weekly-plan/compliance", params={"week_start": "2026-06-22"}
    )
    body = response.json()
    wednesday = body["entries"][2]
    assert wednesday["status"] == "off_target"
    assert wednesday["planned_type"] == "strength"
    assert len(wednesday["actual_sessions"]) == 1
    assert wednesday["actual_sessions"][0]["workout_type"] == "running"


@pytest.mark.anyio
async def test_compliance_rest_ok(client: AsyncClient) -> None:
    """Rest day planned, no session → 'rest_ok'."""
    plan_data = {
        "week_start": "2026-06-29",
        "entries": [
            {"day_of_week": 4, "is_rest_day": True},
        ],
    }
    await client.put("/api/v1/weekly-plan", json=plan_data)

    response = await client.get(
        "/api/v1/weekly-plan/compliance", params={"week_start": "2026-06-29"}
    )
    body = response.json()
    friday = body["entries"][4]
    assert friday["status"] == "rest_ok"
    assert friday["is_rest_day"] is True
    assert body["completed_count"] == 1
    assert body["planned_count"] == 1


@pytest.mark.anyio
async def test_compliance_unplanned(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """No plan, but session exists → 'unplanned'."""
    # Create a session on Thursday 2026-07-09 (week of 2026-07-06)
    await _create_workout(db_session, "2026-07-09T07:00:00", "strength")

    response = await client.get(
        "/api/v1/weekly-plan/compliance", params={"week_start": "2026-07-06"}
    )
    body = response.json()
    thursday = body["entries"][3]
    assert thursday["status"] == "unplanned"
    assert len(thursday["actual_sessions"]) == 1
    assert body["planned_count"] == 0


@pytest.mark.anyio
async def test_compliance_run_type_in_response(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """Run details should expose planned_run_type in compliance response."""
    plan_data = {
        "week_start": "2026-07-13",
        "entries": [
            {
                "day_of_week": 0,
                "training_type": "running",
                "is_rest_day": False,
                "run_details": {"run_type": "tempo", "target_duration_minutes": 40},
            },
        ],
    }
    await client.put("/api/v1/weekly-plan", json=plan_data)

    await _create_workout(db_session, "2026-07-13T08:00:00", "running", "tempo")

    response = await client.get(
        "/api/v1/weekly-plan/compliance", params={"week_start": "2026-07-13"}
    )
    body = response.json()
    monday = body["entries"][0]
    assert monday["status"] == "completed"
    assert monday["planned_run_type"] == "tempo"
    assert monday["actual_sessions"][0]["training_type_effective"] == "tempo"
