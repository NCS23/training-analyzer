"""Tests fuer Krafttraining Progression-Tracking (Issue #17)."""

import json

import pytest
from httpx import AsyncClient

from app.services.progression_tracker import (
    calculate_weekly_tonnage,
    detect_personal_records,
    get_all_exercise_names,
    get_exercise_history,
)

# --- Unit Tests: Progression Tracker Service ---


class TestExerciseHistory:
    def test_single_session(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-02-01",
                "exercises": [
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [
                            {"reps": 8, "weight_kg": 80, "status": "completed"},
                            {"reps": 8, "weight_kg": 80, "status": "completed"},
                        ],
                    }
                ],
            }
        ]
        history = get_exercise_history("Kniebeugen", sessions)
        assert len(history) == 1
        assert history[0]["max_weight_kg"] == 80
        assert history[0]["total_reps"] == 16
        assert history[0]["tonnage_kg"] == 1280.0

    def test_progression_over_time(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-02-01",
                "exercises": [
                    {
                        "name": "Bankdruecken",
                        "category": "push",
                        "sets": [{"reps": 8, "weight_kg": 60, "status": "completed"}],
                    }
                ],
            },
            {
                "id": 2,
                "date": "2026-02-08",
                "exercises": [
                    {
                        "name": "Bankdruecken",
                        "category": "push",
                        "sets": [{"reps": 8, "weight_kg": 65, "status": "completed"}],
                    }
                ],
            },
        ]
        history = get_exercise_history("bankdruecken", sessions)  # case insensitive
        assert len(history) == 2
        assert history[0]["max_weight_kg"] == 60
        assert history[1]["max_weight_kg"] == 65

    def test_skipped_sets_excluded(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-02-01",
                "exercises": [
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [
                            {"reps": 8, "weight_kg": 100, "status": "completed"},
                            {"reps": 0, "weight_kg": 100, "status": "skipped"},
                        ],
                    }
                ],
            }
        ]
        history = get_exercise_history("Kniebeugen", sessions)
        assert history[0]["completed_sets"] == 1
        assert history[0]["total_reps"] == 8
        assert history[0]["tonnage_kg"] == 800.0

    def test_exercise_not_found(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-02-01",
                "exercises": [
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [{"reps": 8, "weight_kg": 80, "status": "completed"}],
                    }
                ],
            }
        ]
        history = get_exercise_history("Bankdruecken", sessions)
        assert len(history) == 0

    def test_empty_sessions(self) -> None:
        assert get_exercise_history("Kniebeugen", []) == []

    def test_chronological_order(self) -> None:
        sessions = [
            {
                "id": 2,
                "date": "2026-02-08",
                "exercises": [
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [{"reps": 5, "weight_kg": 100, "status": "completed"}],
                    }
                ],
            },
            {
                "id": 1,
                "date": "2026-02-01",
                "exercises": [
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [{"reps": 5, "weight_kg": 90, "status": "completed"}],
                    }
                ],
            },
        ]
        history = get_exercise_history("Kniebeugen", sessions)
        assert history[0]["date"] == "2026-02-01"
        assert history[1]["date"] == "2026-02-08"


class TestPersonalRecords:
    def test_max_weight_pr(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-02-01",
                "exercises": [
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [{"reps": 5, "weight_kg": 100, "status": "completed"}],
                    }
                ],
            },
            {
                "id": 2,
                "date": "2026-02-08",
                "exercises": [
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [{"reps": 3, "weight_kg": 110, "status": "completed"}],
                    }
                ],
            },
        ]
        prs = detect_personal_records(sessions)
        weight_prs = [p for p in prs if p["record_type"] == "max_weight"]
        kb_pr = [p for p in weight_prs if p["exercise_name"] == "Kniebeugen"]
        assert len(kb_pr) == 1
        assert kb_pr[0]["value"] == 110
        assert kb_pr[0]["session_id"] == 2

    def test_max_volume_set_pr(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-02-01",
                "exercises": [
                    {
                        "name": "Bankdruecken",
                        "category": "push",
                        "sets": [
                            {"reps": 8, "weight_kg": 60, "status": "completed"},
                            {"reps": 10, "weight_kg": 60, "status": "completed"},
                        ],
                    }
                ],
            },
        ]
        prs = detect_personal_records(sessions)
        vol_prs = [
            p
            for p in prs
            if p["record_type"] == "max_volume_set" and p["exercise_name"] == "Bankdruecken"
        ]
        assert len(vol_prs) == 1
        assert vol_prs[0]["value"] == 600.0  # 10 x 60

    def test_max_tonnage_session_pr(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-02-01",
                "exercises": [
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [
                            {"reps": 5, "weight_kg": 100, "status": "completed"},
                            {"reps": 5, "weight_kg": 100, "status": "completed"},
                        ],
                    }
                ],
            },
        ]
        prs = detect_personal_records(sessions)
        ton_prs = [
            p
            for p in prs
            if p["record_type"] == "max_tonnage_session" and p["exercise_name"] == "Kniebeugen"
        ]
        assert len(ton_prs) == 1
        assert ton_prs[0]["value"] == 1000.0

    def test_skipped_excluded_from_prs(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-02-01",
                "exercises": [
                    {
                        "name": "Test",
                        "category": "push",
                        "sets": [{"reps": 0, "weight_kg": 100, "status": "skipped"}],
                    }
                ],
            },
        ]
        prs = detect_personal_records(sessions)
        assert len(prs) == 0

    def test_empty_sessions(self) -> None:
        assert detect_personal_records([]) == []

    def test_multiple_exercises(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-02-01",
                "exercises": [
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [{"reps": 5, "weight_kg": 100, "status": "completed"}],
                    },
                    {
                        "name": "Bankdruecken",
                        "category": "push",
                        "sets": [{"reps": 8, "weight_kg": 60, "status": "completed"}],
                    },
                ],
            },
        ]
        prs = detect_personal_records(sessions)
        exercise_names = {p["exercise_name"] for p in prs}
        assert "Kniebeugen" in exercise_names
        assert "Bankdruecken" in exercise_names


class TestWeeklyTonnage:
    def test_single_week(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-02-23",
                "exercises": [
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [
                            {"reps": 5, "weight_kg": 100, "status": "completed"},
                            {"reps": 5, "weight_kg": 100, "status": "completed"},
                        ],
                    }
                ],
            },
        ]
        weeks = calculate_weekly_tonnage(sessions)
        assert len(weeks) == 1
        assert weeks[0]["total_tonnage_kg"] == 1000.0
        assert weeks[0]["session_count"] == 1

    def test_multiple_weeks(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-02-16",
                "exercises": [
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [{"reps": 5, "weight_kg": 100, "status": "completed"}],
                    }
                ],
            },
            {
                "id": 2,
                "date": "2026-02-23",
                "exercises": [
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [{"reps": 5, "weight_kg": 110, "status": "completed"}],
                    }
                ],
            },
        ]
        weeks = calculate_weekly_tonnage(sessions)
        assert len(weeks) == 2
        assert weeks[0]["total_tonnage_kg"] == 500.0
        assert weeks[1]["total_tonnage_kg"] == 550.0

    def test_skipped_excluded(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-02-23",
                "exercises": [
                    {
                        "name": "Test",
                        "category": "push",
                        "sets": [
                            {"reps": 10, "weight_kg": 50, "status": "completed"},
                            {"reps": 0, "weight_kg": 50, "status": "skipped"},
                        ],
                    }
                ],
            },
        ]
        weeks = calculate_weekly_tonnage(sessions)
        assert weeks[0]["total_tonnage_kg"] == 500.0

    def test_empty(self) -> None:
        assert calculate_weekly_tonnage([]) == []


class TestGetAllExerciseNames:
    def test_basic(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-02-01",
                "exercises": [
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [{"reps": 5, "weight_kg": 100, "status": "completed"}],
                    },
                    {
                        "name": "Bankdruecken",
                        "category": "push",
                        "sets": [{"reps": 8, "weight_kg": 60, "status": "completed"}],
                    },
                ],
            },
        ]
        result = get_all_exercise_names(sessions)
        assert len(result) == 2
        names = [r["name"] for r in result]
        assert "Kniebeugen" in names
        assert "Bankdruecken" in names

    def test_session_count(self) -> None:
        sessions = [
            {
                "id": 1,
                "date": "2026-02-01",
                "exercises": [
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [{"reps": 5, "weight_kg": 80, "status": "completed"}],
                    }
                ],
            },
            {
                "id": 2,
                "date": "2026-02-08",
                "exercises": [
                    {
                        "name": "Kniebeugen",
                        "category": "legs",
                        "sets": [{"reps": 5, "weight_kg": 90, "status": "completed"}],
                    }
                ],
            },
        ]
        result = get_all_exercise_names(sessions)
        assert result[0]["session_count"] == 2
        assert result[0]["last_max_weight_kg"] == 90

    def test_empty(self) -> None:
        assert get_all_exercise_names([]) == []


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


async def _create_strength_session(
    client: AsyncClient,
    exercises: str = EXERCISES_JSON,
    date_str: str = "2026-02-27",
    duration: str = "60",
) -> int:
    response = await client.post(
        "/api/v1/sessions/strength",
        data={
            "exercises_json": exercises,
            "training_date": date_str,
            "duration_minutes": duration,
        },
    )
    assert response.status_code == 201
    return response.json()["session_id"]


@pytest.mark.anyio
async def test_exercises_list(client: AsyncClient) -> None:
    await _create_strength_session(client)

    response = await client.get("/api/v1/sessions/strength/exercises")
    assert response.status_code == 200
    body = response.json()
    assert len(body["exercises"]) == 2
    names = [e["name"] for e in body["exercises"]]
    assert "Kniebeugen" in names
    assert "Bankdruecken" in names


@pytest.mark.anyio
async def test_exercises_list_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/sessions/strength/exercises")
    assert response.status_code == 200
    assert len(response.json()["exercises"]) == 0


@pytest.mark.anyio
async def test_exercise_progression(client: AsyncClient) -> None:
    # Create two sessions with progression
    await _create_strength_session(
        client,
        exercises=json.dumps(
            [
                {
                    "name": "Kniebeugen",
                    "category": "legs",
                    "sets": [{"reps": 5, "weight_kg": 80, "status": "completed"}],
                }
            ]
        ),
        date_str="2026-02-20",
    )
    await _create_strength_session(
        client,
        exercises=json.dumps(
            [
                {
                    "name": "Kniebeugen",
                    "category": "legs",
                    "sets": [{"reps": 5, "weight_kg": 90, "status": "completed"}],
                }
            ]
        ),
        date_str="2026-02-27",
    )

    response = await client.get(
        "/api/v1/sessions/strength/progression",
        params={"exercise_name": "Kniebeugen"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["exercise_name"] == "Kniebeugen"
    assert len(body["data_points"]) == 2
    assert body["current_max_weight"] == 90
    assert body["previous_max_weight"] == 80
    assert body["weight_progression"] == 10.0


@pytest.mark.anyio
async def test_exercise_progression_not_found(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/sessions/strength/progression",
        params={"exercise_name": "NichtVorhanden"},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["data_points"]) == 0


@pytest.mark.anyio
async def test_personal_records(client: AsyncClient) -> None:
    await _create_strength_session(client)

    response = await client.get("/api/v1/sessions/strength/prs")
    assert response.status_code == 200
    body = response.json()
    assert len(body["records"]) > 0
    # Should have PRs for both exercises
    exercise_names = {pr["exercise_name"] for pr in body["records"]}
    assert "Kniebeugen" in exercise_names
    assert "Bankdruecken" in exercise_names


@pytest.mark.anyio
async def test_personal_records_for_session(client: AsyncClient) -> None:
    session_id = await _create_strength_session(client)

    response = await client.get(
        "/api/v1/sessions/strength/prs",
        params={"session_id": session_id},
    )
    assert response.status_code == 200
    body = response.json()
    # First session = all records are new PRs
    assert body["new_prs_session"] is not None
    assert len(body["new_prs_session"]) > 0


@pytest.mark.anyio
async def test_tonnage_trend(client: AsyncClient) -> None:
    await _create_strength_session(client)

    response = await client.get(
        "/api/v1/sessions/strength/tonnage-trend",
        params={"days": 90},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["weeks"]) == 1
    assert body["total_tonnage_kg"] > 0
    assert body["avg_weekly_tonnage_kg"] > 0


@pytest.mark.anyio
async def test_tonnage_trend_empty(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/sessions/strength/tonnage-trend",
        params={"days": 90},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["weeks"]) == 0
    assert body["total_tonnage_kg"] == 0
