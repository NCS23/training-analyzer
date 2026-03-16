"""Tests fuer Krafttraining (Issue #15, #151, #285)."""

import json

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.models.strength import SetInput, SetType
from app.services.progression_tracker import calculate_weekly_category_tonnage
from app.services.tonnage_calculator import (
    calculate_category_tonnage,
    calculate_srpe,
    calculate_strength_metrics,
)

# --- Unit Tests: SetType Validation (#285 S01) ---


class TestSetTypeValidation:
    """Validierung aller 8 Set-Typen und Backward Compatibility."""

    def test_weight_reps_valid(self) -> None:
        s = SetInput(type=SetType.WEIGHT_REPS, reps=8, weight_kg=100)
        assert s.type == SetType.WEIGHT_REPS
        assert s.reps == 8
        assert s.weight_kg == 100

    def test_weight_reps_missing_weight(self) -> None:
        with pytest.raises(ValidationError, match="weight_kg"):
            SetInput(type=SetType.WEIGHT_REPS, reps=8)

    def test_weight_reps_missing_reps(self) -> None:
        with pytest.raises(ValidationError, match="reps"):
            SetInput(type=SetType.WEIGHT_REPS, weight_kg=100)

    def test_bodyweight_reps_valid(self) -> None:
        s = SetInput(type=SetType.BODYWEIGHT_REPS, reps=15)
        assert s.type == SetType.BODYWEIGHT_REPS
        assert s.reps == 15
        assert s.weight_kg is None

    def test_bodyweight_reps_missing_reps(self) -> None:
        with pytest.raises(ValidationError, match="reps"):
            SetInput(type=SetType.BODYWEIGHT_REPS)

    def test_weighted_bodyweight_valid(self) -> None:
        s = SetInput(type=SetType.WEIGHTED_BODYWEIGHT, reps=8, weight_kg=10)
        assert s.type == SetType.WEIGHTED_BODYWEIGHT
        assert s.reps == 8
        assert s.weight_kg == 10  # Zusatzgewicht

    def test_assisted_bodyweight_valid(self) -> None:
        s = SetInput(type=SetType.ASSISTED_BODYWEIGHT, reps=8, weight_kg=20)
        assert s.type == SetType.ASSISTED_BODYWEIGHT
        assert s.weight_kg == 20  # Hilfsgewicht

    def test_duration_valid(self) -> None:
        s = SetInput(type=SetType.DURATION, duration_sec=60)
        assert s.type == SetType.DURATION
        assert s.duration_sec == 60
        assert s.reps is None

    def test_duration_missing_duration(self) -> None:
        with pytest.raises(ValidationError, match="duration_sec"):
            SetInput(type=SetType.DURATION)

    def test_weight_duration_valid(self) -> None:
        s = SetInput(type=SetType.WEIGHT_DURATION, weight_kg=20, duration_sec=45)
        assert s.type == SetType.WEIGHT_DURATION

    def test_weight_duration_missing_weight(self) -> None:
        with pytest.raises(ValidationError, match="weight_kg"):
            SetInput(type=SetType.WEIGHT_DURATION, duration_sec=45)

    def test_distance_duration_valid(self) -> None:
        s = SetInput(type=SetType.DISTANCE_DURATION, distance_m=30, duration_sec=15)
        assert s.type == SetType.DISTANCE_DURATION
        assert s.distance_m == 30
        assert s.duration_sec == 15

    def test_distance_duration_without_time(self) -> None:
        """duration_sec ist optional bei distance_duration."""
        s = SetInput(type=SetType.DISTANCE_DURATION, distance_m=30)
        assert s.distance_m == 30
        assert s.duration_sec is None

    def test_distance_duration_missing_distance(self) -> None:
        with pytest.raises(ValidationError, match="distance_m"):
            SetInput(type=SetType.DISTANCE_DURATION, duration_sec=15)

    def test_weight_distance_valid(self) -> None:
        s = SetInput(type=SetType.WEIGHT_DISTANCE, weight_kg=24, distance_m=50)
        assert s.type == SetType.WEIGHT_DISTANCE
        assert s.weight_kg == 24
        assert s.distance_m == 50

    def test_weight_distance_missing_distance(self) -> None:
        with pytest.raises(ValidationError, match="distance_m"):
            SetInput(type=SetType.WEIGHT_DISTANCE, weight_kg=24)

    def test_backward_compat_no_type(self) -> None:
        """Alte Sets ohne type-Feld werden als weight_reps behandelt."""
        s = SetInput.model_validate({"reps": 8, "weight_kg": 100, "status": "completed"})
        assert s.type == SetType.WEIGHT_REPS
        assert s.reps == 8
        assert s.weight_kg == 100

    def test_backward_compat_zero_weight(self) -> None:
        """Alte Bodyweight-Sets (weight_kg=0) bleiben als weight_reps."""
        s = SetInput.model_validate({"reps": 12, "weight_kg": 0, "status": "completed"})
        assert s.type == SetType.WEIGHT_REPS
        assert s.weight_kg == 0

    def test_all_set_types_in_enum(self) -> None:
        """Alle 8 Typen existieren."""
        assert len(SetType) == 8


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


# --- Unit Tests: Typ-differenzierte Metriken (#285 S03) ---


class TestTypDifferenzierteMetriken:
    """Tests für typ-differenzierte Volumen-Berechnung."""

    def test_bodyweight_reps_counted(self) -> None:
        exercises = [
            {
                "name": "Liegestuetze",
                "category": "push",
                "sets": [
                    {"type": "bodyweight_reps", "reps": 20, "status": "completed"},
                    {"type": "bodyweight_reps", "reps": 15, "status": "completed"},
                ],
            }
        ]
        result = calculate_strength_metrics(exercises)
        assert result["total_reps"] == 35
        assert result["total_tonnage_kg"] == 0.0

    def test_duration_sets_counted(self) -> None:
        exercises = [
            {
                "name": "Plank",
                "category": "core",
                "sets": [
                    {"type": "duration", "duration_sec": 60, "status": "completed"},
                    {"type": "duration", "duration_sec": 45, "status": "completed"},
                ],
            }
        ]
        result = calculate_strength_metrics(exercises)
        assert result["total_duration_sec"] == 105
        assert result["total_tonnage_kg"] == 0.0
        assert result["total_reps"] == 0

    def test_distance_sets_counted(self) -> None:
        exercises = [
            {
                "name": "A-Skip",
                "category": "drills",
                "sets": [
                    {"type": "distance_duration", "distance_m": 30, "status": "completed"},
                    {"type": "distance_duration", "distance_m": 30, "status": "completed"},
                ],
            }
        ]
        result = calculate_strength_metrics(exercises)
        assert result["total_distance_m"] == 60.0
        assert result["total_tonnage_kg"] == 0.0

    def test_mixed_session(self) -> None:
        """Gemischte Session: alle Metrik-Typen gleichzeitig."""
        exercises = [
            {
                "name": "Kniebeugen",
                "category": "legs",
                "sets": [
                    {"type": "weight_reps", "reps": 5, "weight_kg": 100, "status": "completed"},
                ],
            },
            {
                "name": "Klimmzuege",
                "category": "pull",
                "sets": [
                    {"type": "bodyweight_reps", "reps": 10, "status": "completed"},
                ],
            },
            {
                "name": "Plank",
                "category": "core",
                "sets": [
                    {"type": "duration", "duration_sec": 60, "status": "completed"},
                ],
            },
            {
                "name": "Farmers Walk",
                "category": "core",
                "sets": [
                    {
                        "type": "weight_distance",
                        "weight_kg": 24,
                        "distance_m": 50,
                        "status": "completed",
                    },
                ],
            },
        ]
        result = calculate_strength_metrics(exercises)
        assert result["total_tonnage_kg"] == 500.0
        assert result["total_reps"] == 10
        assert result["total_duration_sec"] == 60
        assert result["total_distance_m"] == 50.0
        assert result["total_exercises"] == 4
        assert result["completed_sets"] == 4

    def test_skipped_duration_not_counted(self) -> None:
        exercises = [
            {
                "name": "Plank",
                "category": "core",
                "sets": [
                    {"type": "duration", "duration_sec": 60, "status": "completed"},
                    {"type": "duration", "duration_sec": 60, "status": "skipped"},
                ],
            }
        ]
        result = calculate_strength_metrics(exercises)
        assert result["total_duration_sec"] == 60
        assert result["completed_sets"] == 1


class TestSrpe:
    """Tests für sRPE-Berechnung."""

    def test_basic_srpe(self) -> None:
        assert calculate_srpe(7, 60) == 420

    def test_srpe_no_rpe(self) -> None:
        assert calculate_srpe(None, 60) is None

    def test_srpe_no_duration(self) -> None:
        assert calculate_srpe(7, None) is None

    def test_srpe_both_none(self) -> None:
        assert calculate_srpe(None, None) is None

    def test_srpe_high_intensity(self) -> None:
        assert calculate_srpe(10, 90) == 900

    def test_srpe_easy_session(self) -> None:
        assert calculate_srpe(3, 30) == 90


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


# --- Unit Tests: Weekly Category Tonnage (#151) ---


class TestWeeklyCategoryTonnage:
    def test_single_week_single_category(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-03-02",
                "exercises": [
                    {
                        "name": "Bankdruecken",
                        "category": "push",
                        "sets": [{"reps": 10, "weight_kg": 60, "status": "completed"}],
                    },
                ],
            },
        ]
        result = calculate_weekly_category_tonnage(sessions)
        assert len(result["weeks"]) == 1
        assert result["weeks"][0]["week"] == "2026-W10"
        cats = result["weeks"][0]["categories"]
        assert len(cats) == 1
        assert cats[0]["category"] == "push"
        assert cats[0]["tonnage_kg"] == 600.0
        assert result["total_tonnage_kg"] == 600.0

    def test_multiple_weeks_multiple_categories(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-03-02",  # W10
                "exercises": [
                    {
                        "name": "Bankdruecken",
                        "category": "push",
                        "sets": [{"reps": 10, "weight_kg": 60, "status": "completed"}],
                    },
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [{"reps": 5, "weight_kg": 100, "status": "completed"}],
                    },
                ],
            },
            {
                "id": 2,
                "date": "2026-03-09",  # W11
                "exercises": [
                    {
                        "name": "Bankdruecken",
                        "category": "push",
                        "sets": [{"reps": 10, "weight_kg": 65, "status": "completed"}],
                    },
                ],
            },
        ]
        result = calculate_weekly_category_tonnage(sessions)
        assert len(result["weeks"]) == 2

        # Week 10: push 600 + legs 500
        w10 = result["weeks"][0]
        assert w10["total_tonnage_kg"] == 1100.0
        cats_w10 = {c["category"]: c["tonnage_kg"] for c in w10["categories"]}
        assert cats_w10["push"] == 600.0
        assert cats_w10["legs"] == 500.0

        # Week 11: push 650
        w11 = result["weeks"][1]
        assert w11["total_tonnage_kg"] == 650.0

        # Aggregated: push 1250, legs 500
        agg = {c["category"]: c["tonnage_kg"] for c in result["aggregated"]}
        assert agg["push"] == 1250.0
        assert agg["legs"] == 500.0
        assert result["total_tonnage_kg"] == 1750.0

    def test_empty_sessions(self) -> None:
        result = calculate_weekly_category_tonnage([])
        assert result["weeks"] == []
        assert result["aggregated"] == []
        assert result["total_tonnage_kg"] == 0.0

    def test_skipped_sets_excluded(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-03-02",
                "exercises": [
                    {
                        "name": "Bankdruecken",
                        "category": "push",
                        "sets": [
                            {"reps": 10, "weight_kg": 60, "status": "completed"},
                            {"reps": 0, "weight_kg": 60, "status": "skipped"},
                        ],
                    },
                ],
            },
        ]
        result = calculate_weekly_category_tonnage(sessions)
        cats = result["weeks"][0]["categories"]
        assert cats[0]["tonnage_kg"] == 600.0

    def test_aggregated_sorted_by_tonnage_desc(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-03-02",
                "exercises": [
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
                    {
                        "name": "Bankdruecken",
                        "category": "push",
                        "sets": [{"reps": 10, "weight_kg": 60, "status": "completed"}],
                    },
                ],
            },
        ]
        result = calculate_weekly_category_tonnage(sessions)
        cats = [c["category"] for c in result["aggregated"]]
        # push=600, legs=500, pull=160
        assert cats == ["push", "legs", "pull"]


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


# --- Integration Tests: Category Tonnage Trend (#151) ---


@pytest.mark.anyio
async def test_category_tonnage_trend_endpoint(client: AsyncClient) -> None:
    """Neuer Endpoint liefert Kategorie-Tonnage nach Wochen."""
    await client.post("/api/v1/sessions/strength", data=VALID_FORM_DATA)

    response = await client.get(
        "/api/v1/sessions/strength/category-tonnage-trend",
        params={"days": 90},
    )
    assert response.status_code == 200
    body = response.json()
    assert "weeks" in body
    assert "aggregated" in body
    assert "total_tonnage_kg" in body
    assert body["period_days"] == 90
    assert body["total_tonnage_kg"] > 0

    # Aggregated should have legs + push from test data
    cats = {c["category"] for c in body["aggregated"]}
    assert "legs" in cats
    assert "push" in cats


@pytest.mark.anyio
async def test_create_mixed_set_types(client: AsyncClient) -> None:
    """Session mit verschiedenen Set-Typen (weighted + bodyweight + duration)."""
    exercises = [
        {
            "name": "Kniebeugen",
            "category": "legs",
            "sets": [
                {"type": "weight_reps", "reps": 8, "weight_kg": 100, "status": "completed"},
            ],
        },
        {
            "name": "Liegestuetze",
            "category": "push",
            "sets": [
                {"type": "bodyweight_reps", "reps": 20, "status": "completed"},
            ],
        },
        {
            "name": "Plank",
            "category": "core",
            "sets": [
                {"type": "duration", "duration_sec": 60, "status": "completed"},
            ],
        },
        {
            "name": "A-Skip",
            "category": "drills",
            "sets": [
                {
                    "type": "distance_duration",
                    "distance_m": 30,
                    "duration_sec": 12,
                    "status": "completed",
                },
            ],
        },
    ]
    response = await client.post(
        "/api/v1/sessions/strength",
        data={
            "exercises_json": json.dumps(exercises),
            "training_date": "2026-03-16",
            "duration_minutes": "45",
            "rpe": "6",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["metrics"]["total_exercises"] == 4
    assert body["metrics"]["total_sets"] == 4
    # Tonnage nur von weighted set: 8 * 100 = 800
    assert body["metrics"]["total_tonnage_kg"] == 800.0


@pytest.mark.anyio
async def test_create_session_backward_compat(client: AsyncClient) -> None:
    """Alte Clients ohne type-Feld funktionieren weiterhin."""
    exercises = [
        {
            "name": "Bankdruecken",
            "category": "push",
            "sets": [
                {"reps": 10, "weight_kg": 60, "status": "completed"},
            ],
        },
    ]
    response = await client.post(
        "/api/v1/sessions/strength",
        data={
            "exercises_json": json.dumps(exercises),
            "training_date": "2026-03-16",
            "duration_minutes": "30",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["metrics"]["total_tonnage_kg"] == 600.0


@pytest.mark.anyio
async def test_category_tonnage_trend_empty(client: AsyncClient) -> None:
    """Leerer Zeitraum liefert leere Listen."""
    response = await client.get(
        "/api/v1/sessions/strength/category-tonnage-trend",
        params={"days": 7},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["weeks"] == []
    assert body["aggregated"] == []
    assert body["total_tonnage_kg"] == 0.0
