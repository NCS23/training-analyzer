"""Tests fuer Krafttraining (Issue #15)."""

import json

import pytest
from httpx import AsyncClient

from app.services.tonnage_calculator import calculate_category_tonnage, calculate_strength_metrics

# --- Unit Tests: Tonnage Calculator ---


class TestTonnageCalculator:
    def test_basic_tonnage(self) -> None:
        exercises = [
            {
                "name": "Kniebeugen",
                "category": "legs",
                "sets": [
                    {"reps": 8, "weight_kg": 100, "status": "completed"},
                    {"reps": 8, "weight_kg": 100, "status": "completed"},
                    {"reps": 6, "weight_kg": 100, "status": "reduced"},
                ],
            }
        ]
        result = calculate_strength_metrics(exercises)
        assert result["total_exercises"] == 1
        assert result["total_sets"] == 3
        assert result["completed_sets"] == 3  # completed + reduced count
        assert result["total_tonnage_kg"] == 2200.0

    def test_skipped_sets_excluded_from_tonnage(self) -> None:
        exercises = [
            {
                "name": "Bankdruecken",
                "category": "push",
                "sets": [
                    {"reps": 10, "weight_kg": 60, "status": "completed"},
                    {"reps": 0, "weight_kg": 60, "status": "skipped"},
                ],
            }
        ]
        result = calculate_strength_metrics(exercises)
        assert result["total_tonnage_kg"] == 600.0
        assert result["completed_sets"] == 1
        assert result["total_sets"] == 2

    def test_multiple_exercises(self) -> None:
        exercises = [
            {
                "name": "Kniebeugen",
                "category": "legs",
                "sets": [{"reps": 5, "weight_kg": 100, "status": "completed"}],
            },
            {
                "name": "Bankdruecken",
                "category": "push",
                "sets": [{"reps": 5, "weight_kg": 80, "status": "completed"}],
            },
        ]
        result = calculate_strength_metrics(exercises)
        assert result["total_exercises"] == 2
        assert result["total_tonnage_kg"] == 900.0

    def test_empty_exercises(self) -> None:
        result = calculate_strength_metrics([])
        assert result["total_exercises"] == 0
        assert result["total_tonnage_kg"] == 0.0

    def test_bodyweight_exercises(self) -> None:
        exercises = [
            {
                "name": "Klimmzuege",
                "category": "pull",
                "sets": [{"reps": 12, "weight_kg": 0, "status": "completed"}],
            }
        ]
        result = calculate_strength_metrics(exercises)
        assert result["total_tonnage_kg"] == 0.0
        assert result["completed_sets"] == 1


# --- Unit Tests: Category Tonnage (#149) ---


class TestCategoryTonnage:
    def test_single_category(self) -> None:
        exercises = [
            {
                "name": "Bankdruecken",
                "category": "push",
                "sets": [
                    {"reps": 10, "weight_kg": 60, "status": "completed"},
                    {"reps": 8, "weight_kg": 60, "status": "completed"},
                ],
            }
        ]
        result = calculate_category_tonnage(exercises)
        assert len(result) == 1
        assert result[0]["category"] == "push"
        assert result[0]["tonnage_kg"] == 1080.0
        assert result[0]["exercise_count"] == 1
        assert result[0]["set_count"] == 2

    def test_multiple_categories(self) -> None:
        exercises = [
            {
                "name": "Bankdruecken",
                "category": "push",
                "sets": [{"reps": 10, "weight_kg": 60, "status": "completed"}],
            },
            {
                "name": "Klimmzuege",
                "category": "pull",
                "sets": [{"reps": 8, "weight_kg": 20, "status": "completed"}],
            },
            {
                "name": "Kniebeugen",
                "category": "legs",
                "sets": [{"reps": 5, "weight_kg": 100, "status": "completed"}],
            },
        ]
        result = calculate_category_tonnage(exercises)
        assert len(result) == 3
        # Sorted by tonnage desc: push 600, legs 500, pull 160
        assert result[0]["category"] == "push"
        assert result[0]["tonnage_kg"] == 600.0
        assert result[1]["category"] == "legs"
        assert result[1]["tonnage_kg"] == 500.0
        assert result[2]["category"] == "pull"
        assert result[2]["tonnage_kg"] == 160.0

    def test_skipped_sets_excluded(self) -> None:
        exercises = [
            {
                "name": "Bankdruecken",
                "category": "push",
                "sets": [
                    {"reps": 10, "weight_kg": 60, "status": "completed"},
                    {"reps": 0, "weight_kg": 60, "status": "skipped"},
                ],
            }
        ]
        result = calculate_category_tonnage(exercises)
        assert result[0]["tonnage_kg"] == 600.0
        assert result[0]["set_count"] == 2  # Both counted as sets
        assert result[0]["exercise_count"] == 1

    def test_reduced_sets_included(self) -> None:
        exercises = [
            {
                "name": "Bankdruecken",
                "category": "push",
                "sets": [
                    {"reps": 6, "weight_kg": 60, "status": "reduced"},
                ],
            }
        ]
        result = calculate_category_tonnage(exercises)
        assert result[0]["tonnage_kg"] == 360.0

    def test_empty_exercises(self) -> None:
        result = calculate_category_tonnage([])
        assert result == []

    def test_same_category_multiple_exercises(self) -> None:
        exercises = [
            {
                "name": "Bankdruecken",
                "category": "push",
                "sets": [{"reps": 10, "weight_kg": 60, "status": "completed"}],
            },
            {
                "name": "Schulterpressen",
                "category": "push",
                "sets": [{"reps": 8, "weight_kg": 40, "status": "completed"}],
            },
        ]
        result = calculate_category_tonnage(exercises)
        assert len(result) == 1
        assert result[0]["category"] == "push"
        assert result[0]["tonnage_kg"] == 920.0
        assert result[0]["exercise_count"] == 2


# --- Integration Tests: API ---

EXERCISES_JSON = json.dumps(
    [
        {
            "name": "Kniebeugen",
            "category": "legs",
            "sets": [
                {"reps": 8, "weight_kg": 100, "status": "completed"},
                {"reps": 8, "weight_kg": 100, "status": "completed"},
            ],
        },
        {
            "name": "Bankdruecken",
            "category": "push",
            "sets": [
                {"reps": 10, "weight_kg": 60, "status": "completed"},
            ],
        },
    ]
)

VALID_FORM_DATA = {
    "exercises_json": EXERCISES_JSON,
    "training_date": "2026-02-27",
    "duration_minutes": "60",
    "notes": "Gutes Training",
    "rpe": "7",
}


@pytest.mark.anyio
async def test_create_strength_session(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/sessions/strength",
        data=VALID_FORM_DATA,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["session_id"] is not None
    assert body["metrics"]["total_exercises"] == 2
    assert body["metrics"]["total_tonnage_kg"] == 2200.0
    assert body["file_data"]["has_file"] is False


@pytest.mark.anyio
async def test_strength_session_in_detail(client: AsyncClient) -> None:
    create = await client.post(
        "/api/v1/sessions/strength",
        data=VALID_FORM_DATA,
    )
    session_id = create.json()["session_id"]

    response = await client.get(f"/api/v1/sessions/{session_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["workout_type"] == "strength"
    assert body["exercises"] is not None
    assert len(body["exercises"]) == 2
    assert body["exercises"][0]["name"] == "Kniebeugen"


@pytest.mark.anyio
async def test_strength_session_in_list(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/sessions/strength",
        data=VALID_FORM_DATA,
    )

    response = await client.get("/api/v1/sessions")
    body = response.json()
    assert body["total"] >= 1
    strength = [s for s in body["sessions"] if s["workout_type"] == "strength"]
    assert len(strength) >= 1
    assert strength[0]["exercises_count"] == 2
    assert strength[0]["total_tonnage_kg"] == 2200.0


@pytest.mark.anyio
async def test_last_exercises_found(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/sessions/strength",
        data=VALID_FORM_DATA,
    )

    response = await client.get(
        "/api/v1/sessions/strength/last-exercises",
        params={"exercise_name": "Kniebeugen"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["found"] is True
    assert body["exercise"]["exercise_name"] == "Kniebeugen"
    assert len(body["exercise"]["sets"]) == 2


@pytest.mark.anyio
async def test_last_exercises_not_found(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/sessions/strength/last-exercises",
        params={"exercise_name": "NichtVorhanden"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["found"] is False


@pytest.mark.anyio
async def test_create_validation_no_exercises(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/sessions/strength",
        data={
            "exercises_json": "[]",
            "training_date": "2026-02-27",
            "duration_minutes": "60",
        },
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_validation_no_sets(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/sessions/strength",
        data={
            "exercises_json": json.dumps([{"name": "Kniebeugen", "category": "legs", "sets": []}]),
            "training_date": "2026-02-27",
            "duration_minutes": "60",
        },
    )
    assert response.status_code == 422
