"""Tests fuer den vollstaendigen minsaga-Export (#823/#825, Format-Version 3)."""

import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import WorkoutModel

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

    assert export["version"] == 3
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

    assert export["version"] == 3
    assert export["goals"] == []
    assert export["plans"] == []
    assert export["weekly_plans"] == []
    assert export["sessions"] == []


@pytest.mark.anyio
async def test_export_enthaelt_trainings_historie(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """#825: Die Garmin-Historie liegt nur hier — sie MUSS in den Export."""
    from datetime import datetime

    db_session.add(
        WorkoutModel(
            user_id=1,
            date=datetime(2024, 3, 15, 7, 30),
            workout_type="running",
            subtype="intervals",
            duration_sec=3_600,
            distance_km=10.5,
            hr_avg=155,
            hr_max=178,
            cadence_avg=172,
            rpe=7,
            laps_json=json.dumps(
                [
                    {
                        "lap_number": 1,
                        "duration_seconds": 600,
                        "distance_km": 1.6,
                        "avg_pace_min_per_km": 6.25,
                        "avg_hr_bpm": 132,
                        "suggested_type": "warmup",
                        "user_override": None,
                    },
                    {
                        "lap_number": 2,
                        "duration_seconds": 300,
                        "distance_km": 1.0,
                        "avg_pace_min_per_km": 5.0,
                        "avg_hr_bpm": 168,
                        "suggested_type": "steady",
                        "user_override": "work",
                    },
                ]
            ),
        )
    )
    await db_session.commit()

    export = (await client.get("/api/v1/export/minsaga")).json()

    assert len(export["sessions"]) == 1
    session = export["sessions"][0]
    assert session["workout_type"] == "running"
    assert session["subtype"] == "intervals"
    assert session["duration_sec"] == 3_600
    assert session["distance_km"] == 10.5
    assert session["hr_avg"] == 155
    assert session["cadence_avg"] == 172
    assert session["rpe"] == 7
    assert len(session["laps"]) == 2
    # Nutzer-Korrektur schlaegt die Klassifikation.
    assert session["laps"][1]["type"] == "work"
    assert session["laps"][0]["type"] == "warmup"
    # Zeitreihen und GPS bleiben bewusst draussen.
    assert "gps_track_json" not in session
    assert "csv_data" not in session
