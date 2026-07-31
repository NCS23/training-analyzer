"""Tests fuer den vollstaendigen minsaga-Export (#823, Format-Version 2)."""

import pytest
from httpx import AsyncClient

PLAN_DATA = {
    "name": "HM Sub 2h",
    "description": "Halbmarathon-Vorbereitung",
    "start_date": "2026-08-03",
    "end_date": "2026-11-01",
    "status": "active",
}

WEEK = "2026-08-03"

WEEKLY_PLAN = {
    "week_start": WEEK,
    "entries": [
        {
            "day_of_week": 0,
            "sessions": [
                {
                    "training_type": "running",
                    "position": 0,
                    "notes": "getauscht wegen Termin",
                    "run_details": {
                        "run_type": "easy",
                        "target_duration_minutes": 45,
                        "target_pace_min": "6:00",
                        "target_pace_max": "6:30",
                    },
                }
            ],
        },
        {"day_of_week": 1, "is_rest_day": True},
        {
            "day_of_week": 3,
            "sessions": [
                {
                    "training_type": "running",
                    "position": 0,
                    "status": "skipped",
                    "run_details": {"run_type": "intervals", "target_duration_minutes": 60},
                }
            ],
        },
    ],
}


@pytest.mark.anyio
async def test_export_enthaelt_wochenplan_und_changelog(client: AsyncClient) -> None:
    plan_resp = await client.post("/api/v1/training-plans", json=PLAN_DATA)
    assert plan_resp.status_code == 201

    save_resp = await client.put("/api/v1/weekly-plan", json=WEEKLY_PLAN)
    assert save_resp.status_code == 200

    export_resp = await client.get("/api/v1/export/minsaga")
    assert export_resp.status_code == 200
    export = export_resp.json()

    assert export["version"] == 2
    assert "exported_at" in export

    # Plan mit Changelog (plan_created ist immer da), interne IDs draussen
    assert len(export["plans"]) == 1
    plan = export["plans"][0]
    assert plan["name"] == "HM Sub 2h"
    assert "id" not in plan
    change_types = [entry["change_type"] for entry in plan["changelog"]]
    assert "plan_created" in change_types

    # Wochenplan: Anpassungen inkl. run_details, Status und Notizen
    assert len(export["weekly_plans"]) == 1
    week = export["weekly_plans"][0]
    assert week["week_start"] == WEEK
    montag = next(day for day in week["days"] if day["day_of_week"] == 0)
    session = montag["sessions"][0]
    assert session["run_details"]["run_type"] == "easy"
    assert session["run_details"]["target_pace_min"] == "6:00"
    assert session["notes"] == "getauscht wegen Termin"
    donnerstag = next(day for day in week["days"] if day["day_of_week"] == 3)
    assert donnerstag["sessions"][0]["status"] == "skipped"
    dienstag = next(day for day in week["days"] if day["day_of_week"] == 1)
    assert dienstag["is_rest_day"] is True


@pytest.mark.anyio
async def test_export_athlete_aus_schwellentest(client: AsyncClient) -> None:
    test_resp = await client.post(
        "/api/v1/threshold-tests",
        json={"test_date": "2026-07-15", "lthr": 172, "avg_pace_sec": 310.0},
    )
    assert test_resp.status_code == 201

    export = (await client.get("/api/v1/export/minsaga")).json()

    assert export["athlete"]["lthr"] == 172
    assert export["athlete"]["threshold_pace_sec_per_km"] == 310.0
    assert export["threshold_tests"][0]["test_date"] == "2026-07-15"


@pytest.mark.anyio
async def test_export_leerer_zustand(client: AsyncClient) -> None:
    export = (await client.get("/api/v1/export/minsaga")).json()

    assert export["version"] == 2
    assert export["goals"] == []
    assert export["plans"] == []
    assert export["weekly_plans"] == []
