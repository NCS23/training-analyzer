"""Tests fuer Pacing-Strategie Persistenz (#528)."""

from datetime import datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import RaceGoalModel

PACING_BASE = "/api/v1/pacing"


async def _create_goal(db: AsyncSession) -> RaceGoalModel:
    """Erstellt ein Test-Goal in der DB."""
    goal = RaceGoalModel(
        title="Hamburg HM",
        race_date=datetime(2026, 4, 26),
        distance_km=21.0975,
        target_time_seconds=6600,  # 1:50:00
        is_active=True,
    )
    db.add(goal)
    await db.commit()
    await db.refresh(goal)
    return goal


@pytest.mark.asyncio
class TestPacingAutoSave:
    """Auto-Save: /generate speichert Strategie wenn goal_id vorhanden."""

    async def test_generate_with_goal_saves_strategy(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        goal = await _create_goal(db_session)
        resp = await client.post(
            f"{PACING_BASE}/generate",
            json={
                "target_time_seconds": 6600,
                "distance_km": 21.0975,
                "strategy": "even",
                "goal_id": goal.id,
            },
        )
        assert resp.status_code == 200

        # Pruefen ob Strategie gespeichert wurde
        list_resp = await client.get(f"{PACING_BASE}/goals/{goal.id}/strategies")
        assert list_resp.status_code == 200
        data = list_resp.json()
        assert len(data["strategies"]) == 1
        saved = data["strategies"][0]
        assert saved["strategy"] == "even"
        assert saved["goal_id"] == goal.id
        assert saved["distance_km"] == pytest.approx(21.0975)
        assert len(saved["splits"]) > 0

    async def test_generate_without_goal_does_not_save(self, client: AsyncClient) -> None:
        resp = await client.post(
            f"{PACING_BASE}/generate",
            json={
                "target_time_seconds": 6600,
                "distance_km": 21.0975,
                "strategy": "even",
            },
        )
        assert resp.status_code == 200
        # Keine goal_id → nichts gespeichert (kein Crash)

    async def test_multiple_generates_save_multiple(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        goal = await _create_goal(db_session)
        for strategy in ["even", "negative", "effort_based"]:
            resp = await client.post(
                f"{PACING_BASE}/generate",
                json={
                    "target_time_seconds": 6600,
                    "distance_km": 21.0975,
                    "strategy": strategy,
                    "goal_id": goal.id,
                },
            )
            assert resp.status_code == 200

        list_resp = await client.get(f"{PACING_BASE}/goals/{goal.id}/strategies")
        assert list_resp.status_code == 200
        assert len(list_resp.json()["strategies"]) == 3


@pytest.mark.asyncio
class TestPacingStrategyCRUD:
    """CRUD-Endpoints fuer gespeicherte Strategien."""

    async def test_list_empty(self, client: AsyncClient, db_session: AsyncSession) -> None:
        goal = await _create_goal(db_session)
        resp = await client.get(f"{PACING_BASE}/goals/{goal.id}/strategies")
        assert resp.status_code == 200
        assert resp.json()["strategies"] == []

    async def test_get_single(self, client: AsyncClient, db_session: AsyncSession) -> None:
        goal = await _create_goal(db_session)
        # Generieren (auto-save)
        await client.post(
            f"{PACING_BASE}/generate",
            json={
                "target_time_seconds": 6600,
                "distance_km": 21.0975,
                "strategy": "negative",
                "goal_id": goal.id,
            },
        )
        # Liste holen
        list_resp = await client.get(f"{PACING_BASE}/goals/{goal.id}/strategies")
        strategy_id = list_resp.json()["strategies"][0]["id"]

        # Einzeln abrufen
        resp = await client.get(f"{PACING_BASE}/goals/{goal.id}/strategies/{strategy_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["strategy"] == "negative"
        assert data["id"] == strategy_id

    async def test_get_nonexistent_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        goal = await _create_goal(db_session)
        resp = await client.get(f"{PACING_BASE}/goals/{goal.id}/strategies/9999")
        assert resp.status_code == 404

    async def test_delete(self, client: AsyncClient, db_session: AsyncSession) -> None:
        goal = await _create_goal(db_session)
        await client.post(
            f"{PACING_BASE}/generate",
            json={
                "target_time_seconds": 6600,
                "distance_km": 21.0975,
                "strategy": "even",
                "goal_id": goal.id,
            },
        )
        list_resp = await client.get(f"{PACING_BASE}/goals/{goal.id}/strategies")
        strategy_id = list_resp.json()["strategies"][0]["id"]

        # Loeschen
        del_resp = await client.delete(f"{PACING_BASE}/goals/{goal.id}/strategies/{strategy_id}")
        assert del_resp.status_code == 204

        # Danach leer
        list_resp2 = await client.get(f"{PACING_BASE}/goals/{goal.id}/strategies")
        assert len(list_resp2.json()["strategies"]) == 0

    async def test_delete_nonexistent_returns_404(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        goal = await _create_goal(db_session)
        resp = await client.delete(f"{PACING_BASE}/goals/{goal.id}/strategies/9999")
        assert resp.status_code == 404

    async def test_list_ordered_by_newest_first(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        goal = await _create_goal(db_session)
        for strategy in ["even", "negative"]:
            await client.post(
                f"{PACING_BASE}/generate",
                json={
                    "target_time_seconds": 6600,
                    "distance_km": 21.0975,
                    "strategy": strategy,
                    "goal_id": goal.id,
                },
            )

        list_resp = await client.get(f"{PACING_BASE}/goals/{goal.id}/strategies")
        strategies = list_resp.json()["strategies"]
        assert len(strategies) == 2
        # Neueste zuerst
        assert strategies[0]["strategy"] == "negative"
        assert strategies[1]["strategy"] == "even"

    async def test_weather_data_persisted(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        goal = await _create_goal(db_session)
        resp = await client.post(
            f"{PACING_BASE}/generate",
            json={
                "target_time_seconds": 6600,
                "distance_km": 21.0975,
                "strategy": "even",
                "goal_id": goal.id,
                "temperature_celsius": 28.0,
            },
        )
        assert resp.status_code == 200

        list_resp = await client.get(f"{PACING_BASE}/goals/{goal.id}/strategies")
        saved = list_resp.json()["strategies"][0]
        assert saved["weather_adjustment"] is not None
        assert saved["weather_adjustment"]["temperature_celsius"] == 28.0
