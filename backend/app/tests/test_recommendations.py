"""Tests fuer KI-Trainingsempfehlungen (E06-S02, Issue #33)."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import WorkoutModel
from app.services.recommendation_service import (
    RecommendationContext,
    _build_recommendation_prompt,
    _normalize_recommendation,
    _parse_recommendations_json,
)

MOCK_ANALYSIS = {
    "summary": "Gutes moderates Lauftraining im GA1-Bereich.",
    "intensity_rating": "moderat",
    "intensity_text": "HF und Pace passen zum Easy Run.",
    "hr_zone_assessment": "80% in Zone 2.",
    "plan_comparison": None,
    "fatigue_indicators": None,
    "recommendations": ["Pace beibehalten", "Long Run einplanen"],
    "cached": True,
    "session_id": 1,
    "provider": "Claude (test)",
}

MOCK_RECOMMENDATIONS_RESPONSE = json.dumps(
    [
        {
            "type": "adjust_pace",
            "title": "Long Run Tempo reduzieren",
            "current_value": "5:20 min/km",
            "suggested_value": "5:40 min/km",
            "reasoning": "Die HF war im oberen Zone-2-Bereich. "
            "Fuer den Long Run sollte das Tempo etwas langsamer sein.",
            "priority": "high",
        },
        {
            "type": "add_rest",
            "title": "Ruhetag nach intensiver Woche",
            "current_value": "Tempo-Lauf geplant",
            "suggested_value": "Ruhetag",
            "reasoning": "Die Woche hat bereits 5 Sessions. "
            "Ein Ruhetag hilft bei der Regeneration.",
            "priority": "medium",
        },
        {
            "type": "general",
            "title": "Dehnroutine nach dem Lauf",
            "current_value": None,
            "suggested_value": "10min Dehnen",
            "reasoning": "Regelmaessiges Dehnen verbessert die Beweglichkeit.",
            "priority": "low",
        },
    ]
)


async def _create_test_workout(
    db: AsyncSession,
    *,
    with_analysis: bool = False,
) -> WorkoutModel:
    """Erstellt ein Test-Workout in der DB."""
    workout = WorkoutModel(
        date=datetime(2026, 3, 10, 8, 0),
        workout_type="running",
        duration_sec=3600,
        distance_km=10.5,
        pace="5:43",
        hr_avg=145,
        hr_max=162,
        hr_min=120,
    )
    if with_analysis:
        workout.ai_analysis = json.dumps(MOCK_ANALYSIS)
    db.add(workout)
    await db.commit()
    await db.refresh(workout)
    return workout


class TestRecommendationsAPI:
    """Integration-Tests fuer POST/GET /sessions/{id}/recommendations."""

    @patch("app.services.recommendation_service.ai_service")
    @patch("app.services.session_analysis_service.ai_service")
    async def test_generate_returns_structured_recommendations(
        self,
        mock_analysis_ai: AsyncMock,
        mock_rec_ai: AsyncMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """POST liefert strukturierte Empfehlungen."""
        workout = await _create_test_workout(db_session, with_analysis=True)
        mock_rec_ai.chat = AsyncMock(return_value=MOCK_RECOMMENDATIONS_RESPONSE)
        mock_rec_ai.get_active_provider.return_value = "Claude (test)"

        response = await client.post(f"/api/v1/sessions/{workout.id}/recommendations")
        assert response.status_code == 200

        data = response.json()
        assert data["session_id"] == workout.id
        assert data["cached"] is False
        assert len(data["recommendations"]) == 3

        # Erste Empfehlung (high priority)
        rec = data["recommendations"][0]
        assert rec["type"] == "adjust_pace"
        assert rec["priority"] == "high"
        assert rec["status"] == "pending"
        assert rec["current_value"] == "5:20 min/km"
        assert rec["suggested_value"] == "5:40 min/km"
        assert rec["id"] > 0

    @patch("app.services.recommendation_service.ai_service")
    @patch("app.services.session_analysis_service.ai_service")
    async def test_cached_recommendations_no_ai_call(
        self,
        mock_analysis_ai: AsyncMock,
        mock_rec_ai: AsyncMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Zweiter Aufruf liefert gecachte Empfehlungen ohne AI-Call."""
        workout = await _create_test_workout(db_session, with_analysis=True)
        mock_rec_ai.chat = AsyncMock(return_value=MOCK_RECOMMENDATIONS_RESPONSE)
        mock_rec_ai.get_active_provider.return_value = "Claude (test)"

        # Erster Aufruf — AI wird gerufen
        await client.post(f"/api/v1/sessions/{workout.id}/recommendations")
        assert mock_rec_ai.chat.call_count == 1

        # Zweiter Aufruf — Cache
        response = await client.post(f"/api/v1/sessions/{workout.id}/recommendations")
        assert response.status_code == 200
        assert response.json()["cached"] is True
        assert mock_rec_ai.chat.call_count == 1  # Kein erneuter Aufruf

    @patch("app.services.recommendation_service.ai_service")
    @patch("app.services.session_analysis_service.ai_service")
    async def test_force_refresh_regenerates(
        self,
        mock_analysis_ai: AsyncMock,
        mock_rec_ai: AsyncMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """force_refresh=True generiert neue Empfehlungen."""
        workout = await _create_test_workout(db_session, with_analysis=True)
        mock_rec_ai.chat = AsyncMock(return_value=MOCK_RECOMMENDATIONS_RESPONSE)
        mock_rec_ai.get_active_provider.return_value = "Claude (test)"

        await client.post(f"/api/v1/sessions/{workout.id}/recommendations")

        response = await client.post(
            f"/api/v1/sessions/{workout.id}/recommendations",
            json={"force_refresh": True},
        )
        assert response.status_code == 200
        assert response.json()["cached"] is False
        assert mock_rec_ai.chat.call_count == 2

    async def test_recommendations_not_found(self, client: AsyncClient) -> None:
        """404 bei ungueltiger Session-ID."""
        response = await client.post("/api/v1/sessions/99999/recommendations")
        assert response.status_code == 404

    @patch("app.services.recommendation_service.ai_service")
    @patch("app.services.session_analysis_service.ai_service")
    async def test_get_recommendations(
        self,
        mock_analysis_ai: AsyncMock,
        mock_rec_ai: AsyncMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """GET liefert gespeicherte Empfehlungen."""
        workout = await _create_test_workout(db_session, with_analysis=True)
        mock_rec_ai.chat = AsyncMock(return_value=MOCK_RECOMMENDATIONS_RESPONSE)
        mock_rec_ai.get_active_provider.return_value = "Claude (test)"

        # Erst generieren
        await client.post(f"/api/v1/sessions/{workout.id}/recommendations")

        # Dann abrufen
        response = await client.get(f"/api/v1/sessions/{workout.id}/recommendations")
        assert response.status_code == 200
        data = response.json()
        assert len(data["recommendations"]) == 3
        assert data["cached"] is True


class TestRecommendationStatusUpdate:
    """Tests fuer PATCH /recommendations/{id}/status."""

    @patch("app.services.recommendation_service.ai_service")
    @patch("app.services.session_analysis_service.ai_service")
    async def test_dismiss_recommendation(
        self,
        mock_analysis_ai: AsyncMock,
        mock_rec_ai: AsyncMock,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Empfehlung kann als 'dismissed' markiert werden."""
        workout = await _create_test_workout(db_session, with_analysis=True)
        mock_rec_ai.chat = AsyncMock(return_value=MOCK_RECOMMENDATIONS_RESPONSE)
        mock_rec_ai.get_active_provider.return_value = "Claude (test)"

        gen_resp = await client.post(f"/api/v1/sessions/{workout.id}/recommendations")
        rec_id = gen_resp.json()["recommendations"][0]["id"]

        response = await client.patch(
            f"/api/v1/sessions/recommendations/{rec_id}/status",
            json={"status": "dismissed"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "dismissed"

    async def test_update_not_found(self, client: AsyncClient) -> None:
        """404 bei ungueltiger Empfehlungs-ID."""
        response = await client.patch(
            "/api/v1/sessions/recommendations/99999/status",
            json={"status": "dismissed"},
        )
        assert response.status_code == 404


class TestRecommendationPromptBuilding:
    """Unit-Tests fuer Prompt-Aufbau."""

    def test_prompt_includes_analysis_context(self) -> None:
        """Prompt enthaelt Session-Analyse."""
        ctx = RecommendationContext(
            analysis_summary="Gutes Training",
            intensity_rating="moderat",
            fatigue_indicators=None,
            plan_comparison=None,
            analysis_recommendations=["Pace beibehalten"],
            race_goal=None,
            current_phase=None,
            upcoming_sessions=[],
            weekly_volume={
                "total_km": 30.0,
                "total_hours": 4.5,
                "session_count": 4,
                "run_count": 3,
                "strength_count": 1,
            },
            recent_recommendations=[],
        )
        prompt = _build_recommendation_prompt(ctx)

        assert "Gutes Training" in prompt
        assert "moderat" in prompt
        assert "Pace beibehalten" in prompt

    def test_prompt_includes_weekly_volume(self) -> None:
        """Prompt enthaelt Wochenvolumen."""
        ctx = RecommendationContext(
            analysis_summary="OK",
            intensity_rating="moderat",
            fatigue_indicators=None,
            plan_comparison=None,
            analysis_recommendations=[],
            race_goal=None,
            current_phase=None,
            upcoming_sessions=[],
            weekly_volume={
                "total_km": 42.0,
                "total_hours": 5.0,
                "session_count": 5,
                "run_count": 4,
                "strength_count": 1,
            },
            recent_recommendations=[],
        )
        prompt = _build_recommendation_prompt(ctx)

        assert "42.0 km" in prompt
        assert "5.0 Stunden" in prompt

    def test_prompt_includes_upcoming_sessions(self) -> None:
        """Prompt enthaelt geplante Sessions."""
        ctx = RecommendationContext(
            analysis_summary="OK",
            intensity_rating="moderat",
            fatigue_indicators=None,
            plan_comparison=None,
            analysis_recommendations=[],
            race_goal=None,
            current_phase=None,
            upcoming_sessions=[
                {
                    "date": "2026-03-12",
                    "type": "running",
                    "run_type": "long_run",
                    "target_duration_min": 90,
                },
            ],
            weekly_volume={
                "total_km": 0,
                "total_hours": 0,
                "session_count": 0,
                "run_count": 0,
                "strength_count": 0,
            },
            recent_recommendations=[],
        )
        prompt = _build_recommendation_prompt(ctx)

        assert "long_run" in prompt
        assert "90min" in prompt


class TestRecommendationJsonParsing:
    """Unit-Tests fuer JSON-Parsing."""

    def test_valid_json_array(self) -> None:
        """Gueltiges JSON-Array wird korrekt geparst."""
        result = _parse_recommendations_json(MOCK_RECOMMENDATIONS_RESPONSE)
        assert len(result) == 3
        assert result[0]["type"] == "adjust_pace"
        assert result[0]["priority"] == "high"

    def test_json_with_markdown_codeblock(self) -> None:
        """JSON in Markdown-Codeblock wird geparst."""
        raw = f"```json\n{MOCK_RECOMMENDATIONS_RESPONSE}\n```"
        result = _parse_recommendations_json(raw)
        assert len(result) == 3

    def test_invalid_json_fallback(self) -> None:
        """Ungueltiges JSON ergibt Fallback-Empfehlung."""
        result = _parse_recommendations_json("Das ist kein JSON.")
        assert len(result) == 1
        assert result[0]["type"] == "general"

    def test_invalid_type_normalized_to_general(self) -> None:
        """Unbekannter Typ wird zu 'general' normalisiert."""
        rec = _normalize_recommendation({"type": "unknown_type", "title": "Test"})
        assert rec["type"] == "general"

    def test_invalid_priority_normalized_to_medium(self) -> None:
        """Ungueltige Prioritaet wird zu 'medium' normalisiert."""
        rec = _normalize_recommendation({"priority": "critical", "title": "Test"})
        assert rec["priority"] == "medium"

    def test_single_object_wrapped_in_list(self) -> None:
        """Einzelnes JSON-Objekt (statt Array) wird gewrapped."""
        raw = json.dumps(
            {
                "type": "add_rest",
                "title": "Ruhetag einlegen",
                "reasoning": "Erholung noetig",
                "priority": "high",
            }
        )
        result = _parse_recommendations_json(raw)
        assert len(result) == 1
        assert result[0]["type"] == "add_rest"
