"""Tests for KI-Chat plan-change endpoint with segment-level run_details (#759)."""

import json
from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    PlanChangeLogModel,
    PlannedSessionModel,
    TrainingPlanModel,
    WeeklyPlanDayModel,
)
from app.services.chat_tool_handlers import handle_propose_plan_change, handle_propose_week_rewrite


@pytest.fixture
async def active_plan(db_session: AsyncSession) -> TrainingPlanModel:
    """Inject an active training plan covering today for changelog tests."""
    today = date.today()
    plan = TrainingPlanModel(
        name="Test Plan",
        start_date=today.replace(day=1),
        end_date=today.replace(month=12, day=31),
        status="active",
    )
    db_session.add(plan)
    await db_session.commit()
    await db_session.refresh(plan)
    return plan


@pytest.mark.anyio
async def test_apply_plan_change_replace_with_run_details_persists_intervals(
    client: AsyncClient,
) -> None:
    """Replace-Aktion mit run_details schreibt run_details_json inkl. Intervallen."""
    payload = {
        "action": "replace",
        "date": "2026-05-04",
        "description": "Intervalltraining 5×800m",
        "reason": "Tempo-Training fuer VO2max",
        "training_type": "running",
        "run_details": {
            "run_type": "intervals",
            "intervals": [
                {"type": "warmup", "duration_minutes": 10, "repeats": 1},
                {
                    "type": "work",
                    "duration_minutes": 3,
                    "target_pace_min": "4:25",
                    "target_pace_max": "4:35",
                    "repeats": 5,
                },
                {"type": "recovery_jog", "duration_minutes": 2, "repeats": 4},
                {"type": "cooldown", "duration_minutes": 8, "repeats": 1},
            ],
        },
    }
    resp = await client.post("/api/v1/ai/apply-plan-change", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True

    # Inspect persisted session
    from app.tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        sessions = (await session.execute(select(PlannedSessionModel))).scalars().all()
        assert len(sessions) == 1
        s = sessions[0]
        assert s.training_type == "running"
        assert s.run_details_json is not None
        rd = json.loads(s.run_details_json)
        assert rd["run_type"] == "intervals"
        # 4 input intervals expand to >= 4 segments after model_validator
        assert len(rd["intervals"]) >= 4


@pytest.mark.anyio
async def test_apply_plan_change_replace_without_run_details_falls_back(
    client: AsyncClient,
) -> None:
    """Backwards-compat: ohne run_details bleibt Verhalten wie vorher (nur notes)."""
    payload = {
        "action": "replace",
        "date": "2026-05-04",
        "description": "Lockerer Lauf",
        "reason": "Regeneration",
        "to": "Easy 45 min",
    }
    resp = await client.post("/api/v1/ai/apply-plan-change", json=payload)
    assert resp.status_code == 200, resp.text

    from app.tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        sessions = (await session.execute(select(PlannedSessionModel))).scalars().all()
        assert len(sessions) == 1
        assert sessions[0].run_details_json is None
        assert sessions[0].training_type == "running"


@pytest.mark.anyio
async def test_apply_plan_change_invalid_run_details_returns_422(
    client: AsyncClient,
) -> None:
    """Strikte Validierung: ungueltiger run_type wird abgelehnt."""
    payload = {
        "action": "add",
        "date": "2026-05-04",
        "description": "Falsches Schema",
        "reason": "Test",
        "training_type": "running",
        "run_details": {
            "run_type": "completely_invalid_type",
            "intervals": [{"type": "steady", "duration_minutes": 30}],
        },
    }
    resp = await client.post("/api/v1/ai/apply-plan-change", json=payload)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_apply_plan_change_changelog_includes_run_details(
    client: AsyncClient,
    active_plan: TrainingPlanModel,  # noqa: ARG001
) -> None:
    """Changelog-Eintrag enthaelt run_details fuer Audit/Undo."""
    payload = {
        "action": "add",
        "date": str(date.today()),
        "description": "Tempo-Lauf",
        "reason": "Schwellentempo",
        "training_type": "running",
        "run_details": {
            "run_type": "tempo",
            "intervals": [
                {
                    "type": "steady",
                    "duration_minutes": 25,
                    "target_pace_min": "5:00",
                    "target_pace_max": "5:10",
                }
            ],
        },
    }
    resp = await client.post("/api/v1/ai/apply-plan-change", json=payload)
    assert resp.status_code == 200, resp.text

    from app.tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        log_entries = (await session.execute(select(PlanChangeLogModel))).scalars().all()
        # last entry is the chat-applied one
        chat_entry = next(e for e in log_entries if e.details_json and "ki_chat" in e.details_json)
        assert chat_entry.details_json is not None
        details = json.loads(chat_entry.details_json)
        assert details["source"] == "ki_chat"
        assert details["training_type"] == "running"
        assert details["run_details"]["run_type"] == "tempo"


@pytest.mark.anyio
async def test_handle_propose_plan_change_block_includes_run_details(
    db_session: AsyncSession,
) -> None:
    """Tool-Handler haengt run_details an den plan-change Block."""
    args = {
        "action": "replace",
        "day": "Mittwoch",
        "date": "2026-05-06",
        "description": "Intervalle",
        "reason": "Tempotraining",
        "training_type": "running",
        "run_details": {
            "run_type": "intervals",
            "intervals": [{"type": "work", "duration_minutes": 3, "repeats": 5}],
        },
    }
    result = await handle_propose_plan_change(args, db_session)
    assert result["rendered"] is True
    block = result["block"]
    assert "```plan-change" in block
    # Strip code fences
    json_str = block.split("\n", 1)[1].rsplit("\n```", 1)[0]
    parsed = json.loads(json_str)
    assert parsed["training_type"] == "running"
    assert parsed["run_details"]["run_type"] == "intervals"


@pytest.mark.anyio
async def test_handle_propose_week_rewrite_block_format(db_session: AsyncSession) -> None:
    """Wochen-Rewrite-Tool erzeugt week-rewrite Block mit Folgewoche."""
    args = {
        "review_week_start": "2026-04-20",  # Monday
        "summary": "Volumen reduzieren",
        "reason": "Hohe Belastung in der Vorwoche",
        "recommendations": [
            "Long Run um 20% kuerzen",
            "Tempo-Lauf durch Easy Run ersetzen",
        ],
    }
    result = await handle_propose_week_rewrite(args, db_session)
    assert result["rendered"] is True
    block = result["block"]
    assert "```week-rewrite" in block
    json_str = block.split("\n", 1)[1].rsplit("\n```", 1)[0]
    parsed = json.loads(json_str)
    assert parsed["target_week_start"] == "2026-04-27"
    assert len(parsed["recommendations"]) == 2


@pytest.mark.anyio
async def test_apply_plan_change_creates_day_when_missing(client: AsyncClient) -> None:
    """Ohne bestehenden WeeklyPlanDay wird einer angelegt."""
    payload = {
        "action": "add",
        "date": "2026-05-08",
        "description": "Cross-Training",
        "reason": "Test",
        "training_type": "strength",
        "to": "Krafttraining",
    }
    resp = await client.post("/api/v1/ai/apply-plan-change", json=payload)
    assert resp.status_code == 200, resp.text

    from app.tests.conftest import TestSessionLocal

    async with TestSessionLocal() as session:
        days = (await session.execute(select(WeeklyPlanDayModel))).scalars().all()
        assert len(days) == 1
        assert days[0].is_rest_day is False
        assert days[0].edited is True
