"""Tests for Weekly Plan (Issue #26)."""

import pytest
from httpx import AsyncClient

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
async def test_save_weekly_plan_with_plan_id(client: AsyncClient) -> None:
    """Save a plan entry referencing a training plan."""
    # Create a training plan first
    plan_response = await client.post("/api/v1/plans", json=PLAN_DATA)
    assert plan_response.status_code == 201
    plan_id = plan_response.json()["id"]

    data = {
        "week_start": "2026-03-09",
        "entries": [
            {
                "day_of_week": 0,
                "training_type": "strength",
                "plan_id": plan_id,
                "is_rest_day": False,
            },
        ],
    }

    response = await client.put("/api/v1/weekly-plan", json=data)
    assert response.status_code == 200
    body = response.json()
    # Monday should have the plan
    assert body["entries"][0]["plan_id"] == plan_id
    assert body["entries"][0]["plan_name"] == "Test Plan"


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
