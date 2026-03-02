"""Tests for Training Plans & Phases (S07, S08, S09)."""

from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import RaceGoalModel

PLAN_DATA = {
    "name": "HM Sub-2h Vorbereitung",
    "description": "12-Wochen Plan fuer Halbmarathon",
    "start_date": "2026-04-01",
    "end_date": "2026-06-30",
    "target_event_date": "2026-07-05",
    "status": "draft",
}

PHASE_DATA = {
    "name": "Grundlagenaufbau",
    "phase_type": "base",
    "start_week": 1,
    "end_week": 4,
    "focus": {"primary": ["endurance"], "secondary": ["strength"]},
    "notes": "Langsam aufbauen, Umfang steigern",
}


# --- Plan CRUD ---


@pytest.mark.anyio
async def test_create_plan(client: AsyncClient) -> None:
    response = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "HM Sub-2h Vorbereitung"
    assert body["status"] == "draft"
    assert body["start_date"] == "2026-04-01"
    assert body["end_date"] == "2026-06-30"
    assert body["target_event_date"] == "2026-07-05"
    assert body["phases"] == []
    assert body["goal_summary"] is None


@pytest.mark.anyio
async def test_create_plan_with_phases(client: AsyncClient) -> None:
    data = {
        **PLAN_DATA,
        "phases": [PHASE_DATA],
    }
    response = await client.post("/api/v1/training-plans", json=data)
    assert response.status_code == 201
    body = response.json()
    assert len(body["phases"]) == 1
    assert body["phases"][0]["name"] == "Grundlagenaufbau"
    assert body["phases"][0]["phase_type"] == "base"
    assert body["phases"][0]["start_week"] == 1
    assert body["phases"][0]["end_week"] == 4


@pytest.mark.anyio
async def test_create_plan_invalid_dates(client: AsyncClient) -> None:
    data = {**PLAN_DATA, "end_date": "2026-03-01"}  # before start
    response = await client.post("/api/v1/training-plans", json=data)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_plan_validation_no_name(client: AsyncClient) -> None:
    data = {**PLAN_DATA, "name": ""}
    response = await client.post("/api/v1/training-plans", json=data)
    assert response.status_code == 422


@pytest.mark.anyio
async def test_list_plans(client: AsyncClient) -> None:
    await client.post("/api/v1/training-plans", json=PLAN_DATA)
    await client.post(
        "/api/v1/training-plans",
        json={**PLAN_DATA, "name": "5k Speed Plan", "status": "active"},
    )

    response = await client.get("/api/v1/training-plans")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert len(body["plans"]) == 2


@pytest.mark.anyio
async def test_list_plans_filter_by_status(client: AsyncClient) -> None:
    await client.post("/api/v1/training-plans", json=PLAN_DATA)
    await client.post(
        "/api/v1/training-plans",
        json={**PLAN_DATA, "name": "Active Plan", "status": "active"},
    )

    response = await client.get(
        "/api/v1/training-plans",
        params={"status": "active"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["plans"][0]["name"] == "Active Plan"


@pytest.mark.anyio
async def test_get_plan(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/training-plans/{plan_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "HM Sub-2h Vorbereitung"


@pytest.mark.anyio
async def test_get_plan_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/training-plans/9999")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_update_plan(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/training-plans/{plan_id}",
        json={"name": "Updated Plan", "status": "active"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Plan"
    assert response.json()["status"] == "active"


@pytest.mark.anyio
async def test_update_plan_not_found(client: AsyncClient) -> None:
    response = await client.patch(
        "/api/v1/training-plans/9999",
        json={"name": "Nope"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_plan(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/training-plans/{plan_id}")
    assert response.status_code == 204

    response = await client.get(f"/api/v1/training-plans/{plan_id}")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_plan_not_found(client: AsyncClient) -> None:
    response = await client.delete("/api/v1/training-plans/9999")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_plan_cascades_phases(client: AsyncClient) -> None:
    data = {**PLAN_DATA, "phases": [PHASE_DATA]}
    create_resp = await client.post("/api/v1/training-plans", json=data)
    plan_id = create_resp.json()["id"]

    await client.delete(f"/api/v1/training-plans/{plan_id}")

    # Plan is gone
    response = await client.get(f"/api/v1/training-plans/{plan_id}")
    assert response.status_code == 404


# --- Phase CRUD ---


@pytest.mark.anyio
async def test_list_phases(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/training-plans",
        json={**PLAN_DATA, "phases": [PHASE_DATA]},
    )
    plan_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/training-plans/{plan_id}/phases")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["phase_type"] == "base"


@pytest.mark.anyio
async def test_list_phases_plan_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/training-plans/9999/phases")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_create_phase(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/v1/training-plans/{plan_id}/phases",
        json=PHASE_DATA,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Grundlagenaufbau"
    assert body["training_plan_id"] == plan_id
    assert body["focus"]["primary"] == ["endurance"]


@pytest.mark.anyio
async def test_create_phase_invalid_weeks(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/v1/training-plans/{plan_id}/phases",
        json={**PHASE_DATA, "start_week": 5, "end_week": 2},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_create_phase_invalid_type(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/v1/training-plans/{plan_id}/phases",
        json={**PHASE_DATA, "phase_type": "invalid"},
    )
    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_phase(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/training-plans",
        json={**PLAN_DATA, "phases": [PHASE_DATA]},
    )
    plan_id = create_resp.json()["id"]
    phase_id = create_resp.json()["phases"][0]["id"]

    response = await client.patch(
        f"/api/v1/training-plans/{plan_id}/phases/{phase_id}",
        json={"name": "Updated Phase", "phase_type": "build"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Phase"
    assert response.json()["phase_type"] == "build"


@pytest.mark.anyio
async def test_update_phase_not_found(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/training-plans/{plan_id}/phases/9999",
        json={"name": "Nope"},
    )
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_phase(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/training-plans",
        json={**PLAN_DATA, "phases": [PHASE_DATA]},
    )
    plan_id = create_resp.json()["id"]
    phase_id = create_resp.json()["phases"][0]["id"]

    response = await client.delete(
        f"/api/v1/training-plans/{plan_id}/phases/{phase_id}",
    )
    assert response.status_code == 204

    phases = await client.get(f"/api/v1/training-plans/{plan_id}/phases")
    assert len(phases.json()) == 0


@pytest.mark.anyio
async def test_delete_phase_not_found(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    plan_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/training-plans/{plan_id}/phases/9999",
    )
    assert response.status_code == 404


# --- Goal <-> Plan Link (S09) ---


@pytest.mark.anyio
async def test_create_plan_with_goal(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    # Create a goal first
    goal = RaceGoalModel(
        title="Hamburg HM",
        race_date=datetime(2026, 7, 5),
        distance_km=21.1,
        target_time_seconds=7200,
    )
    db_session.add(goal)
    await db_session.commit()
    await db_session.refresh(goal)

    # Create plan with goal_id
    data = {**PLAN_DATA, "goal_id": goal.id}
    response = await client.post("/api/v1/training-plans", json=data)
    assert response.status_code == 201
    body = response.json()
    assert body["goal_id"] == goal.id
    assert body["goal_summary"]["title"] == "Hamburg HM"

    # Verify bidirectional link: goal now has training_plan_id
    goal_resp = await client.get(f"/api/v1/goals/{goal.id}")
    assert goal_resp.status_code == 200
    assert goal_resp.json()["training_plan_id"] == body["id"]
    assert goal_resp.json()["training_plan_summary"]["name"] == "HM Sub-2h Vorbereitung"


@pytest.mark.anyio
async def test_delete_plan_clears_goal_link(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    goal = RaceGoalModel(
        title="Hamburg HM",
        race_date=datetime(2026, 7, 5),
        distance_km=21.1,
        target_time_seconds=7200,
    )
    db_session.add(goal)
    await db_session.commit()
    await db_session.refresh(goal)

    create_resp = await client.post(
        "/api/v1/training-plans",
        json={**PLAN_DATA, "goal_id": goal.id},
    )
    plan_id = create_resp.json()["id"]

    await client.delete(f"/api/v1/training-plans/{plan_id}")

    # Goal link should be cleared
    goal_resp = await client.get(f"/api/v1/goals/{goal.id}")
    assert goal_resp.json()["training_plan_id"] is None


@pytest.mark.anyio
async def test_plan_summary_in_list(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/training-plans",
        json={**PLAN_DATA, "phases": [PHASE_DATA]},
    )
    assert create_resp.status_code == 201

    response = await client.get("/api/v1/training-plans")
    body = response.json()
    assert body["plans"][0]["phase_count"] == 1
    assert body["plans"][0]["status"] == "draft"


# --- YAML Import ---

VALID_YAML = b"""
name: HM Sub-2h Vorbereitung
description: 16-Wochen Plan
start_date: 2026-04-06
end_date: 2026-07-26
target_event_date: 2026-07-26
status: draft

phases:
  - name: Grundlagenaufbau
    type: base
    start_week: 1
    end_week: 6
    notes: Langsamer Aufbau
  - name: Aufbau
    type: build
    start_week: 7
    end_week: 12
"""


@pytest.mark.anyio
async def test_import_yaml_plan(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/training-plans/import",
        files={"yaml_file": ("plan.yaml", VALID_YAML, "application/x-yaml")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "HM Sub-2h Vorbereitung"
    assert body["status"] == "draft"
    assert body["start_date"] == "2026-04-06"
    assert len(body["phases"]) == 2
    assert body["phases"][0]["phase_type"] == "base"
    assert body["phases"][1]["phase_type"] == "build"


@pytest.mark.anyio
async def test_import_yaml_with_goal_title(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    goal = RaceGoalModel(
        title="Hamburg Halbmarathon",
        race_date=datetime(2026, 7, 26),
        distance_km=21.1,
        target_time_seconds=7200,
    )
    db_session.add(goal)
    await db_session.commit()
    await db_session.refresh(goal)

    yaml_with_goal = b"""
name: HM Plan mit Ziel
start_date: 2026-04-06
end_date: 2026-07-26
status: draft
goal_title: Hamburg Halbmarathon
"""
    response = await client.post(
        "/api/v1/training-plans/import",
        files={"yaml_file": ("plan.yaml", yaml_with_goal, "application/x-yaml")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["goal_id"] == goal.id
    assert body["goal_summary"]["title"] == "Hamburg Halbmarathon"


@pytest.mark.anyio
async def test_import_yaml_goal_title_not_found(client: AsyncClient) -> None:
    yaml_content = b"""
name: Plan ohne passendes Ziel
start_date: 2026-04-06
end_date: 2026-07-26
status: draft
goal_title: Nicht existierendes Ziel
"""
    response = await client.post(
        "/api/v1/training-plans/import",
        files={"yaml_file": ("plan.yaml", yaml_content, "application/x-yaml")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["goal_id"] is None


@pytest.mark.anyio
async def test_import_yaml_invalid_file_extension(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/training-plans/import",
        files={"yaml_file": ("plan.txt", b"name: test", "text/plain")},
    )
    assert response.status_code == 400
    assert "YAML" in response.json()["detail"]


@pytest.mark.anyio
async def test_import_yaml_empty_file(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/training-plans/import",
        files={"yaml_file": ("plan.yaml", b"", "application/x-yaml")},
    )
    assert response.status_code == 400
    assert "leer" in response.json()["detail"]


@pytest.mark.anyio
async def test_import_yaml_malformed(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/training-plans/import",
        files={"yaml_file": ("plan.yaml", b"{{invalid yaml", "application/x-yaml")},
    )
    assert response.status_code == 400
    assert "Parsing" in response.json()["detail"]


@pytest.mark.anyio
async def test_import_yaml_validation_error(client: AsyncClient) -> None:
    yaml_missing = b"""
description: Plan ohne Name und Datum
status: draft
"""
    response = await client.post(
        "/api/v1/training-plans/import",
        files={"yaml_file": ("plan.yaml", yaml_missing, "application/x-yaml")},
    )
    assert response.status_code == 422
    assert "Validierung" in response.json()["detail"]


# --- YAML Import with RunDetails ---


YAML_WITH_RUN_DETAILS = b"""
name: Plan mit RunDetails
start_date: 2026-04-06
end_date: 2026-07-26
status: draft

phases:
  - name: Base
    type: base
    start_week: 1
    end_week: 4
    weekly_template:
      - day: 0
        type: running
        run_type: easy
        run_details:
          run_type: easy
          target_duration_minutes: 45
          target_pace_min: "5:40"
          target_pace_max: "6:10"
      - { day: 1, type: strength }
      - { day: 2, type: running, run_type: easy }
      - { day: 3, rest: true }
      - day: 4
        type: running
        run_type: intervals
        run_details:
          run_type: intervals
          target_duration_minutes: 60
          intervals:
            - { type: warmup, duration_minutes: 10, repeats: 1 }
            - { type: work, duration_minutes: 3, target_pace_min: "4:20", repeats: 5 }
            - { type: recovery_jog, duration_minutes: 2, repeats: 5 }
            - { type: cooldown, duration_minutes: 10, repeats: 1 }
      - { day: 5, type: running, run_type: long_run }
      - { day: 6, rest: true }
"""


@pytest.mark.anyio
async def test_import_yaml_with_run_details(client: AsyncClient) -> None:
    """YAML import correctly parses run_details including intervals."""
    response = await client.post(
        "/api/v1/training-plans/import",
        files={"yaml_file": ("plan.yaml", YAML_WITH_RUN_DETAILS, "application/x-yaml")},
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body["phases"]) == 1

    phase = body["phases"][0]
    wt = phase["weekly_template"]
    assert wt is not None

    # Day 0: easy with explicit run_details
    day0 = wt["days"][0]
    assert day0["run_type"] == "easy"
    assert day0["run_details"] is not None
    assert day0["run_details"]["target_duration_minutes"] == 45
    assert day0["run_details"]["target_pace_min"] == "5:40"
    assert day0["run_details"]["target_pace_max"] == "6:10"

    # Day 4: intervals with intervals list
    day4 = wt["days"][4]
    assert day4["run_type"] == "intervals"
    assert day4["run_details"] is not None
    assert day4["run_details"]["run_type"] == "intervals"
    assert len(day4["run_details"]["intervals"]) == 4
    assert day4["run_details"]["intervals"][1]["type"] == "work"
    assert day4["run_details"]["intervals"][1]["repeats"] == 5

    # Day 2: no run_details → should be None
    day2 = wt["days"][2]
    assert day2["run_type"] == "easy"
    assert day2["run_details"] is None

    # Day 5: long_run without run_details
    day5 = wt["days"][5]
    assert day5["run_type"] == "long_run"
    assert day5["run_details"] is None


@pytest.mark.anyio
async def test_import_yaml_without_run_details_backward_compat(client: AsyncClient) -> None:
    """Existing YAML format without run_details still works."""
    response = await client.post(
        "/api/v1/training-plans/import",
        files={"yaml_file": ("plan.yaml", VALID_YAML, "application/x-yaml")},
    )
    assert response.status_code == 201
    body = response.json()
    assert len(body["phases"]) == 2
    # Phases without weekly_template → no run_details to check
    assert body["phases"][0]["weekly_template"] is None


# --- Goal Auto-Create (API) ---


@pytest.mark.anyio
async def test_create_plan_auto_creates_goal(client: AsyncClient) -> None:
    """Goal block in create → auto-creates a new goal."""
    data = {
        **PLAN_DATA,
        "goal": {
            "title": "Hamburg Halbmarathon",
            "distance_km": 21.1,
            "target_time_seconds": 7140,
        },
    }
    response = await client.post("/api/v1/training-plans", json=data)
    assert response.status_code == 201
    body = response.json()
    assert body["goal_id"] is not None
    assert body["goal_summary"]["title"] == "Hamburg Halbmarathon"

    # Verify the goal was actually created
    goal_resp = await client.get(f"/api/v1/goals/{body['goal_id']}")
    assert goal_resp.status_code == 200
    goal = goal_resp.json()
    assert goal["distance_km"] == 21.1
    assert goal["target_time_seconds"] == 7140
    # race_date defaults to target_event_date
    assert goal["race_date"].startswith("2026-07-05")


# --- Generation Preview & Strategy (E16-S03) ---


async def _create_plan_with_generated_entries(
    client: AsyncClient,
    plan_name: str = "Strategy-Test-Plan",
    start_date: str = "2026-09-07",
    end_date: str = "2026-09-20",
) -> int:
    """Helper: create plan with 2-week phase and generate entries."""
    plan_resp = await client.post(
        "/api/v1/training-plans",
        json={
            "name": plan_name,
            "start_date": start_date,
            "end_date": end_date,
            "phases": [
                {
                    "name": "Base",
                    "phase_type": "base",
                    "start_week": 1,
                    "end_week": 2,
                    "weekly_template": {
                        "days": [
                            {
                                "day_of_week": i,
                                "training_type": "running" if i < 3 else None,
                                "is_rest_day": i >= 3,
                            }
                            for i in range(7)
                        ],
                    },
                },
            ],
        },
    )
    assert plan_resp.status_code == 201
    plan_id: int = plan_resp.json()["id"]

    gen_resp = await client.post(f"/api/v1/training-plans/{plan_id}/generate")
    assert gen_resp.status_code == 200
    assert gen_resp.json()["weeks_generated"] == 2
    return plan_id


async def _edit_week(client: AsyncClient, week_start: str) -> None:
    """Helper: edit a generated week to mark entries as edited."""
    save_data = {
        "week_start": week_start,
        "entries": [
            {
                "day_of_week": 0,
                "training_type": "running",
                "is_rest_day": False,
                "notes": "Manuell bearbeitet",
            },
        ],
    }
    resp = await client.put("/api/v1/weekly-plan", json=save_data)
    assert resp.status_code == 200


@pytest.mark.anyio
async def test_generation_preview_no_edits(client: AsyncClient) -> None:
    """Preview should show 0 edited weeks when nothing was changed."""
    plan_id = await _create_plan_with_generated_entries(
        client, "Preview-No-Edit", "2026-09-07", "2026-09-20"
    )
    resp = await client.get(f"/api/v1/training-plans/{plan_id}/generation-preview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_generated_weeks"] == 2
    assert body["edited_week_count"] == 0
    assert body["edited_week_starts"] == []
    assert body["unedited_week_count"] == 2


@pytest.mark.anyio
async def test_generation_preview_with_edits(client: AsyncClient) -> None:
    """Preview should count edited weeks after manual changes."""
    plan_id = await _create_plan_with_generated_entries(
        client, "Preview-With-Edit", "2026-09-21", "2026-10-04"
    )
    # Edit the first week
    await _edit_week(client, "2026-09-21")

    resp = await client.get(f"/api/v1/training-plans/{plan_id}/generation-preview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_generated_weeks"] == 2
    assert body["edited_week_count"] == 1
    assert "2026-09-21" in body["edited_week_starts"]
    assert body["unedited_week_count"] == 1


@pytest.mark.anyio
async def test_generate_strategy_all_replaces_edited(client: AsyncClient) -> None:
    """strategy=all should replace even edited weeks."""
    plan_id = await _create_plan_with_generated_entries(
        client, "Strategy-All", "2026-10-05", "2026-10-18"
    )
    await _edit_week(client, "2026-10-05")

    # Verify edited
    preview = await client.get(f"/api/v1/training-plans/{plan_id}/generation-preview")
    assert preview.json()["edited_week_count"] == 1

    # Re-generate with strategy=all
    gen_resp = await client.post(f"/api/v1/training-plans/{plan_id}/generate?strategy=all")
    assert gen_resp.status_code == 200
    assert gen_resp.json()["weeks_generated"] == 2

    # Edited should be gone
    preview2 = await client.get(f"/api/v1/training-plans/{plan_id}/generation-preview")
    assert preview2.json()["edited_week_count"] == 0


@pytest.mark.anyio
async def test_generate_strategy_unedited_only_preserves_edited(
    client: AsyncClient,
) -> None:
    """strategy=unedited_only should skip edited weeks."""
    plan_id = await _create_plan_with_generated_entries(
        client, "Strategy-Unedited", "2026-10-19", "2026-11-01"
    )
    await _edit_week(client, "2026-10-19")

    # Re-generate with strategy=unedited_only
    gen_resp = await client.post(
        f"/api/v1/training-plans/{plan_id}/generate?strategy=unedited_only"
    )
    assert gen_resp.status_code == 200
    # Only 1 week regenerated (the unedited one)
    assert gen_resp.json()["weeks_generated"] == 1

    # Edited week should still have the edits
    get_resp = await client.get("/api/v1/weekly-plan", params={"week_start": "2026-10-19"})
    entries = get_resp.json()["entries"]
    monday = entries[0]
    assert monday["edited"] is True
    assert monday["notes"] == "Manuell bearbeitet"


@pytest.mark.anyio
async def test_generate_invalid_strategy_422(client: AsyncClient) -> None:
    """Invalid strategy value should return 422."""
    plan_id = await _create_plan_with_generated_entries(
        client, "Strategy-Invalid", "2026-11-02", "2026-11-15"
    )
    resp = await client.post(f"/api/v1/training-plans/{plan_id}/generate?strategy=invalid")
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_create_plan_auto_create_uses_existing_goal(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Goal block with matching title → reuses existing goal."""
    goal = RaceGoalModel(
        title="Hamburg Halbmarathon",
        race_date=datetime(2026, 7, 5),
        distance_km=21.1,
        target_time_seconds=7200,
    )
    db_session.add(goal)
    await db_session.commit()
    await db_session.refresh(goal)

    data = {
        **PLAN_DATA,
        "goal": {
            "title": "hamburg halbmarathon",  # case-insensitive match
            "distance_km": 21.1,
            "target_time_seconds": 7140,
        },
    }
    response = await client.post("/api/v1/training-plans", json=data)
    assert response.status_code == 201
    body = response.json()
    assert body["goal_id"] == goal.id  # reuses existing goal


@pytest.mark.anyio
async def test_create_plan_auto_create_race_date_fallback(
    client: AsyncClient,
) -> None:
    """Goal without race_date falls back to end_date when no target_event_date."""
    data = {
        "name": "Plan ohne Event-Datum",
        "start_date": "2026-04-01",
        "end_date": "2026-06-30",
        "status": "draft",
        "goal": {
            "title": "Fallback Goal",
            "distance_km": 10.0,
            "target_time_seconds": 3000,
        },
    }
    response = await client.post("/api/v1/training-plans", json=data)
    assert response.status_code == 201
    body = response.json()
    assert body["goal_id"] is not None

    goal_resp = await client.get(f"/api/v1/goals/{body['goal_id']}")
    assert goal_resp.json()["race_date"].startswith("2026-06-30")


@pytest.mark.anyio
async def test_create_plan_goal_id_takes_precedence(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Explicit goal_id takes precedence over goal block."""
    goal = RaceGoalModel(
        title="Existing Goal",
        race_date=datetime(2026, 7, 5),
        distance_km=21.1,
        target_time_seconds=7200,
    )
    db_session.add(goal)
    await db_session.commit()
    await db_session.refresh(goal)

    data = {
        **PLAN_DATA,
        "goal_id": goal.id,
        "goal": {
            "title": "Should Be Ignored",
            "distance_km": 5.0,
            "target_time_seconds": 1500,
        },
    }
    response = await client.post("/api/v1/training-plans", json=data)
    assert response.status_code == 201
    body = response.json()
    assert body["goal_id"] == goal.id
    assert body["goal_summary"]["title"] == "Existing Goal"


# --- Goal Auto-Create (YAML Import) ---


@pytest.mark.anyio
async def test_import_yaml_auto_creates_goal(client: AsyncClient) -> None:
    """YAML with goal: block auto-creates a new goal."""
    yaml_content = b"""
name: Plan mit neuem Ziel
start_date: 2026-04-06
end_date: 2026-07-26
target_event_date: 2026-07-26
status: draft
goal:
  title: Hamburg Halbmarathon 2026
  distance_km: 21.1
  target_time: "1:59:00"
"""
    response = await client.post(
        "/api/v1/training-plans/import",
        files={"yaml_file": ("plan.yaml", yaml_content, "application/x-yaml")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["goal_id"] is not None
    assert body["goal_summary"]["title"] == "Hamburg Halbmarathon 2026"

    # Verify goal details
    goal_resp = await client.get(f"/api/v1/goals/{body['goal_id']}")
    goal = goal_resp.json()
    assert goal["distance_km"] == 21.1
    assert goal["target_time_seconds"] == 7140  # 1:59:00 = 7140s


@pytest.mark.anyio
async def test_import_yaml_goal_uses_existing(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """YAML with goal: block reuses existing goal if title matches."""
    goal = RaceGoalModel(
        title="Hamburg Halbmarathon 2026",
        race_date=datetime(2026, 7, 26),
        distance_km=21.1,
        target_time_seconds=7200,
    )
    db_session.add(goal)
    await db_session.commit()
    await db_session.refresh(goal)

    yaml_content = b"""
name: Plan mit bestehendem Ziel
start_date: 2026-04-06
end_date: 2026-07-26
status: draft
goal:
  title: hamburg halbmarathon 2026
  distance_km: 21.1
  target_time: "1:59:00"
"""
    response = await client.post(
        "/api/v1/training-plans/import",
        files={"yaml_file": ("plan.yaml", yaml_content, "application/x-yaml")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["goal_id"] == goal.id


@pytest.mark.anyio
async def test_import_yaml_goal_target_time_seconds(client: AsyncClient) -> None:
    """YAML goal with target_time_seconds instead of target_time."""
    yaml_content = b"""
name: Plan mit Sekunden-Zielzeit
start_date: 2026-04-06
end_date: 2026-07-26
status: draft
goal:
  title: 10k Rekord
  distance_km: 10.0
  target_time_seconds: 2700
"""
    response = await client.post(
        "/api/v1/training-plans/import",
        files={"yaml_file": ("plan.yaml", yaml_content, "application/x-yaml")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["goal_id"] is not None

    goal_resp = await client.get(f"/api/v1/goals/{body['goal_id']}")
    assert goal_resp.json()["target_time_seconds"] == 2700


@pytest.mark.anyio
async def test_import_yaml_invalid_phase_type(client: AsyncClient) -> None:
    yaml_bad = b"""
name: Plan mit falschem Phasentyp
start_date: 2026-04-06
end_date: 2026-07-26
status: draft
phases:
  - name: Bad Phase
    type: invalid_type
    start_week: 1
    end_week: 4
"""
    response = await client.post(
        "/api/v1/training-plans/import",
        files={"yaml_file": ("plan.yaml", yaml_bad, "application/x-yaml")},
    )
    assert response.status_code == 422
