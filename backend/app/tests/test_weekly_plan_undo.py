"""Tests for Weekly Plan Undo (Issue #340)."""

from datetime import date, datetime, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import PlanChangeLogModel

WEEK = "2026-08-03"  # A Monday (matches _generate_plan_entries pattern)


async def _setup_plan_linked_week(
    client: AsyncClient,
    db_session: AsyncSession,
) -> int:
    """Create a training plan with a phase+template and generate weekly entries.

    Returns the plan_id. After this, weekly plan entries for WEEK have plan_id set.
    """
    end_date = (date.fromisoformat(WEEK) + timedelta(days=6)).isoformat()
    plan_resp = await client.post(
        "/api/v1/training-plans",
        json={
            "name": "Undo Test Plan",
            "start_date": WEEK,
            "end_date": end_date,
            "phases": [
                {
                    "name": "Base",
                    "phase_type": "base",
                    "start_week": 1,
                    "end_week": 1,
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
    return plan_id


def _plan_v1() -> dict:
    """Modified plan: strength Mon, running Tue, rest Wed."""
    return {
        "week_start": WEEK,
        "entries": [
            {
                "day_of_week": 0,
                "sessions": [{"training_type": "strength", "position": 0}],
            },
            {
                "day_of_week": 1,
                "sessions": [{"training_type": "running", "position": 0}],
            },
            {"day_of_week": 2, "is_rest_day": True},
        ],
    }


def _plan_v2() -> dict:
    """Another modification: running Mon, rest Tue, strength Wed."""
    return {
        "week_start": WEEK,
        "entries": [
            {
                "day_of_week": 0,
                "sessions": [{"training_type": "running", "position": 0}],
            },
            {"day_of_week": 1, "is_rest_day": True},
            {
                "day_of_week": 2,
                "sessions": [{"training_type": "strength", "position": 0}],
            },
        ],
    }


@pytest.mark.anyio
async def test_undo_status_no_changes(client: AsyncClient) -> None:
    """Undo should not be available when no changes exist."""
    response = await client.get("/api/v1/weekly-plan/undo-status", params={"week_start": WEEK})
    assert response.status_code == 200
    body = response.json()
    assert body["available"] is False
    assert body["changelog_id"] is None


@pytest.mark.anyio
async def test_undo_not_found(client: AsyncClient) -> None:
    """Undo should return 404 when no undoable entry exists."""
    response = await client.post("/api/v1/weekly-plan/undo", params={"week_start": WEEK})
    assert response.status_code == 404


@pytest.mark.anyio
async def test_undo_restores_weekly_plan(client: AsyncClient, db_session: AsyncSession) -> None:
    """Save v1, save v2, undo → plan should be back to v1."""
    await _setup_plan_linked_week(client, db_session)

    # Save v1 (this changes the generated plan → changelog with snapshot)
    resp1 = await client.put("/api/v1/weekly-plan", json=_plan_v1())
    assert resp1.status_code == 200

    # Verify v1
    get1 = await client.get("/api/v1/weekly-plan", params={"week_start": WEEK})
    assert get1.json()["entries"][0]["sessions"][0]["training_type"] == "strength"

    # Save v2 (triggers another changelog with snapshot of v1)
    resp2 = await client.put("/api/v1/weekly-plan", json=_plan_v2())
    assert resp2.status_code == 200

    # Verify v2
    get2 = await client.get("/api/v1/weekly-plan", params={"week_start": WEEK})
    assert get2.json()["entries"][0]["sessions"][0]["training_type"] == "running"

    # Check undo is available
    status_resp = await client.get("/api/v1/weekly-plan/undo-status", params={"week_start": WEEK})
    status = status_resp.json()
    assert status["available"] is True
    assert status["changelog_id"] is not None

    # Execute undo
    undo_resp = await client.post("/api/v1/weekly-plan/undo", params={"week_start": WEEK})
    assert undo_resp.status_code == 200
    undo_body = undo_resp.json()
    assert undo_body["success"] is True
    assert undo_body["restored_days"] > 0

    # Verify plan is back to v1 state
    get3 = await client.get("/api/v1/weekly-plan", params={"week_start": WEEK})
    entries = get3.json()["entries"]
    mon = next(e for e in entries if e["day_of_week"] == 0)
    assert mon["sessions"][0]["training_type"] == "strength"


@pytest.mark.anyio
async def test_undo_creates_changelog_entry(client: AsyncClient, db_session: AsyncSession) -> None:
    """Undo should create a changelog entry with change_type='undo'."""
    await _setup_plan_linked_week(client, db_session)
    await client.put("/api/v1/weekly-plan", json=_plan_v1())
    await client.put("/api/v1/weekly-plan", json=_plan_v2())

    # Undo
    await client.post("/api/v1/weekly-plan/undo", params={"week_start": WEEK})

    # Check changelog
    result = await db_session.execute(
        select(PlanChangeLogModel)
        .where(PlanChangeLogModel.change_type == "undo")
        .order_by(PlanChangeLogModel.created_at.desc())
    )
    undo_entry = result.scalars().first()
    assert undo_entry is not None
    assert "Rückgängig" in str(undo_entry.summary)


@pytest.mark.anyio
async def test_undo_not_undoable_itself(client: AsyncClient, db_session: AsyncSession) -> None:
    """After undo, the undo entry itself should NOT be undoable."""
    await _setup_plan_linked_week(client, db_session)
    await client.put("/api/v1/weekly-plan", json=_plan_v1())
    await client.put("/api/v1/weekly-plan", json=_plan_v2())

    # Undo once
    undo1 = await client.post("/api/v1/weekly-plan/undo", params={"week_start": WEEK})
    assert undo1.status_code == 200

    # Second undo should fail (no more undoable entries)
    undo2 = await client.post("/api/v1/weekly-plan/undo", params={"week_start": WEEK})
    assert undo2.status_code == 404


@pytest.mark.anyio
async def test_undo_status_expired(client: AsyncClient, db_session: AsyncSession) -> None:
    """Undo should not be available after 24h."""
    await _setup_plan_linked_week(client, db_session)
    await client.put("/api/v1/weekly-plan", json=_plan_v1())
    await client.put("/api/v1/weekly-plan", json=_plan_v2())

    # Verify undo is available
    status1 = await client.get("/api/v1/weekly-plan/undo-status", params={"week_start": WEEK})
    assert status1.json()["available"] is True

    # Backdate changelog entries to 25h ago
    old_time = datetime.utcnow() - timedelta(hours=25)
    await db_session.execute(update(PlanChangeLogModel).values(created_at=old_time))
    await db_session.commit()

    # Undo should no longer be available
    status2 = await client.get("/api/v1/weekly-plan/undo-status", params={"week_start": WEEK})
    assert status2.json()["available"] is False
