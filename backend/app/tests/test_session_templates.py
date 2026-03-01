"""Tests for Session Templates (Issue #14, #29)."""

import json
from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import WorkoutModel

TEMPLATE_DATA = {
    "name": "Studio Tag 1 - Kniedominant",
    "description": "Fokus auf Kniebeugen und Beinpresse",
    "session_type": "strength",
    "exercises": [
        {
            "name": "Kniebeugen",
            "category": "legs",
            "sets": 4,
            "reps": 8,
            "weight_kg": 80,
            "exercise_type": "kraft",
            "notes": "Tiefe Kniebeugen, Knie nicht ueber Zehenspitzen",
        },
        {
            "name": "Beinpresse",
            "category": "legs",
            "sets": 3,
            "reps": 12,
            "weight_kg": 120,
            "exercise_type": "kraft",
        },
        {
            "name": "Hueftmobilisation",
            "category": "legs",
            "sets": 2,
            "reps": 10,
            "exercise_type": "mobilitaet",
            "notes": "Zum Aufwaermen",
        },
    ],
}

RUNNING_TEMPLATE_DATA = {
    "name": "Easy Run Template",
    "session_type": "running",
    "run_details": {
        "run_type": "easy",
        "target_duration_minutes": 45,
        "target_pace_min": "5:30",
        "target_pace_max": "6:00",
    },
}


@pytest.mark.anyio
async def test_create_template(client: AsyncClient) -> None:
    response = await client.post("/api/v1/session-templates", json=TEMPLATE_DATA)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Studio Tag 1 - Kniedominant"
    assert body["session_type"] == "strength"
    assert len(body["exercises"]) == 3
    assert body["exercises"][0]["name"] == "Kniebeugen"
    assert body["exercises"][0]["sets"] == 4
    assert body["exercises"][0]["reps"] == 8
    assert body["exercises"][0]["weight_kg"] == 80
    assert body["exercises"][2]["exercise_type"] == "mobilitaet"
    assert body["is_template"] is True


@pytest.mark.anyio
async def test_create_template_validation_empty_exercises(client: AsyncClient) -> None:
    data = {**TEMPLATE_DATA, "exercises": []}
    response = await client.post("/api/v1/session-templates", json=data)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_template_validation_no_name(client: AsyncClient) -> None:
    data = {**TEMPLATE_DATA, "name": ""}
    response = await client.post("/api/v1/session-templates", json=data)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_templates(client: AsyncClient) -> None:
    # Create two templates
    await client.post("/api/v1/session-templates", json=TEMPLATE_DATA)
    await client.post(
        "/api/v1/session-templates",
        json={
            **TEMPLATE_DATA,
            "name": "Studio Tag 2 - Hueftdominant",
        },
    )

    response = await client.get("/api/v1/session-templates")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["templates"]) == 2
    # Should have exercise_count and total_sets
    assert body["templates"][0]["exercise_count"] == 3
    assert body["templates"][0]["total_sets"] == 9  # 4+3+2


@pytest.mark.anyio
async def test_list_templates_filter_by_type(client: AsyncClient) -> None:
    await client.post("/api/v1/session-templates", json=TEMPLATE_DATA)

    response = await client.get("/api/v1/session-templates", params={"session_type": "running"})
    assert response.status_code == 200
    assert response.json()["total"] == 0

    response = await client.get("/api/v1/session-templates", params={"session_type": "strength"})
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.anyio
async def test_get_template(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/session-templates", json=TEMPLATE_DATA)
    template_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/session-templates/{template_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == template_id
    assert body["name"] == "Studio Tag 1 - Kniedominant"
    assert len(body["exercises"]) == 3


@pytest.mark.anyio
async def test_get_template_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/session-templates/9999")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_template(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/session-templates", json=TEMPLATE_DATA)
    template_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/session-templates/{template_id}",
        json={"name": "Studio Tag 1 - Updated"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Studio Tag 1 - Updated"
    # Exercises should remain unchanged
    assert len(response.json()["exercises"]) == 3


@pytest.mark.anyio
async def test_update_template_exercises(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/session-templates", json=TEMPLATE_DATA)
    template_id = create_resp.json()["id"]

    new_exercises = [
        {
            "name": "Bankdruecken",
            "category": "push",
            "sets": 5,
            "reps": 5,
            "weight_kg": 70,
            "exercise_type": "kraft",
        },
    ]
    response = await client.patch(
        f"/api/v1/session-templates/{template_id}",
        json={"exercises": new_exercises},
    )
    assert response.status_code == 200
    assert len(response.json()["exercises"]) == 1
    assert response.json()["exercises"][0]["name"] == "Bankdruecken"


@pytest.mark.anyio
async def test_update_template_not_found(client: AsyncClient) -> None:
    response = await client.patch(
        "/api/v1/session-templates/9999",
        json={"name": "Nope"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_template(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/session-templates", json=TEMPLATE_DATA)
    template_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/session-templates/{template_id}")
    assert response.status_code == 204

    # Verify deleted
    response = await client.get(f"/api/v1/session-templates/{template_id}")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_template_not_found(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/session-templates/9999")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_duplicate_template(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/session-templates", json=TEMPLATE_DATA)
    template_id = create_resp.json()["id"]

    response = await client.post(f"/api/v1/session-templates/{template_id}/duplicate")
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Studio Tag 1 - Kniedominant (Kopie)"
    assert len(body["exercises"]) == 3
    assert body["id"] != template_id


@pytest.mark.anyio
async def test_duplicate_template_not_found(client: AsyncClient) -> None:
    response = await client.post("/api/v1/session-templates/9999/duplicate")
    assert response.status_code == 404


# --- Running Template Tests ---


@pytest.mark.anyio
async def test_create_running_template(client: AsyncClient) -> None:
    response = await client.post("/api/v1/session-templates", json=RUNNING_TEMPLATE_DATA)
    assert response.status_code == 201
    body = response.json()
    assert body["session_type"] == "running"
    assert body["run_details"] is not None
    assert body["run_details"]["run_type"] == "easy"
    assert body["run_details"]["target_duration_minutes"] == 45
    assert body["run_details"]["target_pace_min"] == "5:30"
    assert body["exercises"] == []


@pytest.mark.anyio
async def test_create_running_template_no_details_fails(client: AsyncClient) -> None:
    data = {"name": "Bad Running Template", "session_type": "running"}
    response = await client.post("/api/v1/session-templates", json=data)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_strength_template_no_exercises_fails(client: AsyncClient) -> None:
    data = {"name": "Bad Strength Template", "session_type": "strength"}
    response = await client.post("/api/v1/session-templates", json=data)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_running_templates(client: AsyncClient) -> None:
    await client.post("/api/v1/session-templates", json=TEMPLATE_DATA)
    await client.post("/api/v1/session-templates", json=RUNNING_TEMPLATE_DATA)

    response = await client.get("/api/v1/session-templates", params={"session_type": "running"})
    body = response.json()
    assert body["total"] == 1
    assert body["templates"][0]["run_type"] == "easy"

    response = await client.get("/api/v1/session-templates", params={"session_type": "strength"})
    assert response.json()["total"] == 1


@pytest.mark.anyio
async def test_duplicate_running_template(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/session-templates", json=RUNNING_TEMPLATE_DATA)
    template_id = create_resp.json()["id"]

    response = await client.post(f"/api/v1/session-templates/{template_id}/duplicate")
    assert response.status_code == 201
    body = response.json()
    assert body["run_details"]["run_type"] == "easy"
    assert body["id"] != template_id


# --- From-Session Tests ---


@pytest.mark.anyio
async def test_from_session_strength(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    exercises = [
        {
            "name": "Bankdruecken",
            "category": "push",
            "sets": [
                {"reps": 8, "weight_kg": 70},
                {"reps": 8, "weight_kg": 70},
                {"reps": 6, "weight_kg": 75},
            ],
            "exercise_type": "kraft",
        },
    ]
    workout = WorkoutModel(
        date=datetime(2026, 3, 1),
        workout_type="strength",
        duration_sec=3600,
        exercises_json=json.dumps(exercises),
    )
    db_session.add(workout)
    await db_session.commit()
    await db_session.refresh(workout)

    response = await client.post(f"/api/v1/session-templates/from-session/{workout.id}")
    assert response.status_code == 201
    body = response.json()
    assert body["session_type"] == "strength"
    assert len(body["exercises"]) == 1
    assert body["exercises"][0]["name"] == "Bankdruecken"
    assert body["exercises"][0]["sets"] == 3  # 3 sets from the array
    assert body["exercises"][0]["reps"] == 8  # first set's reps
    assert body["exercises"][0]["weight_kg"] == 70


@pytest.mark.anyio
async def test_from_session_running(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    workout = WorkoutModel(
        date=datetime(2026, 3, 1),
        workout_type="running",
        duration_sec=2700,
        distance_km=8.5,
        pace="5:18",
        training_type_auto="easy",
    )
    db_session.add(workout)
    await db_session.commit()
    await db_session.refresh(workout)

    response = await client.post(f"/api/v1/session-templates/from-session/{workout.id}")
    assert response.status_code == 201
    body = response.json()
    assert body["session_type"] == "running"
    assert body["run_details"]["run_type"] == "easy"
    assert body["run_details"]["target_duration_minutes"] == 45
    assert body["run_details"]["target_pace_min"] == "5:18"


@pytest.mark.anyio
async def test_from_session_long_run(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    workout = WorkoutModel(
        date=datetime(2026, 3, 1),
        workout_type="running",
        duration_sec=5400,
        distance_km=18.0,
        pace="5:00",
    )
    db_session.add(workout)
    await db_session.commit()
    await db_session.refresh(workout)

    response = await client.post(f"/api/v1/session-templates/from-session/{workout.id}")
    assert response.status_code == 201
    body = response.json()
    assert body["run_details"]["run_type"] == "long_run"


@pytest.mark.anyio
async def test_from_session_not_found(client: AsyncClient) -> None:
    response = await client.post("/api/v1/session-templates/from-session/9999")
    assert response.status_code == 404
