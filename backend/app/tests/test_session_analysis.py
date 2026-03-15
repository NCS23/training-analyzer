"""Tests für KI Session-Analyse (Issue #32)."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import WorkoutModel
from app.models.ai_analysis import SessionAnalysisResponse
from app.services.session_analysis_service import (
    _build_analysis_prompt,
    _parse_analysis_json,
)

MOCK_AI_RESPONSE = json.dumps(
    {
        "summary": "Gutes moderates Lauftraining im GA1-Bereich.",
        "intensity_rating": "moderat",
        "intensity_text": "HF und Pace passen zum Easy Run.",
        "hr_zone_assessment": "80% in Zone 2 — ideal für Grundlagenausdauer.",
        "plan_comparison": None,
        "fatigue_indicators": None,
        "recommendations": [
            "Pace beibehalten",
            "Nächste Woche Long Run einplanen",
        ],
    }
)


async def _create_test_workout(db: AsyncSession) -> WorkoutModel:
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
        cadence_avg=178,
        laps_json=json.dumps(
            [
                {
                    "lap_number": 1,
                    "duration_seconds": 600,
                    "duration_formatted": "10:00",
                    "distance_km": 1.7,
                    "pace_formatted": "5:53",
                    "avg_hr_bpm": 140,
                    "suggested_type": "warmup",
                },
                {
                    "lap_number": 2,
                    "duration_seconds": 2400,
                    "duration_formatted": "40:00",
                    "distance_km": 7.0,
                    "pace_formatted": "5:43",
                    "avg_hr_bpm": 148,
                    "suggested_type": "steady",
                },
                {
                    "lap_number": 3,
                    "duration_seconds": 600,
                    "duration_formatted": "10:00",
                    "distance_km": 1.8,
                    "pace_formatted": "5:33",
                    "avg_hr_bpm": 138,
                    "suggested_type": "cooldown",
                },
            ]
        ),
        hr_zones_json=json.dumps(
            {
                "zone_1_recovery": {"seconds": 600, "percentage": 16.7, "label": "Zone 1"},
                "zone_2_base": {"seconds": 2400, "percentage": 66.7, "label": "Zone 2"},
                "zone_3_tempo": {"seconds": 600, "percentage": 16.7, "label": "Zone 3"},
            }
        ),
    )
    db.add(workout)
    await db.commit()
    await db.refresh(workout)
    return workout


class TestSessionAnalysisAPI:
    """Integration-Tests für POST /sessions/{id}/analyze."""

    @patch("app.services.session_analysis_service.ai_service")
    async def test_analyze_returns_structured_response(
        self, mock_ai: AsyncMock, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Analyse liefert strukturierte Response."""
        workout = await _create_test_workout(db_session)
        mock_ai.chat = AsyncMock(return_value=MOCK_AI_RESPONSE)
        mock_ai.get_active_provider.return_value = "Claude (test)"

        response = await client.post(f"/api/v1/sessions/{workout.id}/analyze")
        assert response.status_code == 200

        data = response.json()
        assert data["session_id"] == workout.id
        assert data["intensity_rating"] == "moderat"
        assert data["summary"] == "Gutes moderates Lauftraining im GA1-Bereich."
        assert len(data["recommendations"]) == 2
        assert data["cached"] is False

    @patch("app.services.session_analysis_service.ai_service")
    async def test_cached_analysis_no_ai_call(
        self, mock_ai: AsyncMock, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Zweiter Aufruf liefert gecachte Analyse ohne AI-Call."""
        workout = await _create_test_workout(db_session)
        mock_ai.chat = AsyncMock(return_value=MOCK_AI_RESPONSE)
        mock_ai.get_active_provider.return_value = "Claude (test)"

        # Erster Aufruf — AI wird gerufen
        await client.post(f"/api/v1/sessions/{workout.id}/analyze")
        assert mock_ai.chat.call_count == 1

        # Zweiter Aufruf — Cache
        response = await client.post(f"/api/v1/sessions/{workout.id}/analyze")
        assert response.status_code == 200
        assert response.json()["cached"] is True
        assert mock_ai.chat.call_count == 1  # Kein erneuter Aufruf

    @patch("app.services.session_analysis_service.ai_service")
    async def test_force_refresh_bypasses_cache(
        self, mock_ai: AsyncMock, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """force_refresh=True umgeht den Cache."""
        workout = await _create_test_workout(db_session)
        mock_ai.chat = AsyncMock(return_value=MOCK_AI_RESPONSE)
        mock_ai.get_active_provider.return_value = "Claude (test)"

        # Erster Aufruf
        await client.post(f"/api/v1/sessions/{workout.id}/analyze")

        # Force refresh
        response = await client.post(
            f"/api/v1/sessions/{workout.id}/analyze",
            json={"force_refresh": True},
        )
        assert response.status_code == 200
        assert response.json()["cached"] is False
        assert mock_ai.chat.call_count == 2

    async def test_analyze_not_found(self, client: AsyncClient) -> None:
        """404 bei ungültiger Session-ID."""
        response = await client.post("/api/v1/sessions/99999/analyze")
        assert response.status_code == 404

    @patch("app.services.session_analysis_service.ai_service")
    async def test_get_session_includes_cached_analysis(
        self, mock_ai: AsyncMock, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """GET /sessions/{id} enthält ai_analysis wenn gecacht."""
        workout = await _create_test_workout(db_session)
        mock_ai.chat = AsyncMock(return_value=MOCK_AI_RESPONSE)
        mock_ai.get_active_provider.return_value = "Claude (test)"

        # Analyse triggern
        await client.post(f"/api/v1/sessions/{workout.id}/analyze")

        # GET prüfen
        response = await client.get(f"/api/v1/sessions/{workout.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["ai_analysis"] is not None
        assert data["ai_analysis"]["summary"] == "Gutes moderates Lauftraining im GA1-Bereich."


class TestPromptBuilding:
    """Unit-Tests für Prompt-Aufbau."""

    async def test_prompt_contains_session_data(self, db_session: AsyncSession) -> None:
        """Prompt enthält Session-Kerndaten."""
        workout = await _create_test_workout(db_session)
        from app.services.session_analysis_service import AnalysisContext

        ctx = AnalysisContext(history=[], race_goal=None, planned_session=None, athlete=None)
        prompt = _build_analysis_prompt(workout, ctx)

        assert "10.5" in prompt  # Distanz
        assert "5:43" in prompt  # Pace
        assert "145" in prompt  # HR avg
        assert "running" in prompt

    async def test_prompt_contains_laps(self, db_session: AsyncSession) -> None:
        """Prompt enthält Laps-Tabelle."""
        workout = await _create_test_workout(db_session)
        from app.services.session_analysis_service import AnalysisContext

        ctx = AnalysisContext(history=[], race_goal=None, planned_session=None, athlete=None)
        prompt = _build_analysis_prompt(workout, ctx)

        assert "## Laps" in prompt
        assert "warmup" in prompt
        assert "steady" in prompt
        assert "cooldown" in prompt

    async def test_prompt_contains_goal(self, db_session: AsyncSession) -> None:
        """Prompt enthält Wettkampfziel wenn vorhanden."""
        workout = await _create_test_workout(db_session)
        from app.services.session_analysis_service import AnalysisContext

        goal = {
            "title": "Hamburg HM",
            "date": "2026-04-26",
            "distance_km": 21.1,
            "target_time_min": 120,
            "target_pace": "5:41",
        }
        ctx = AnalysisContext(history=[], race_goal=goal, planned_session=None, athlete=None)
        prompt = _build_analysis_prompt(workout, ctx)

        assert "Hamburg HM" in prompt
        assert "5:41" in prompt


class TestJsonParsing:
    """Unit-Tests für _parse_analysis_json."""

    def test_valid_json(self) -> None:
        """Gültiges JSON wird korrekt geparst."""
        result = _parse_analysis_json(MOCK_AI_RESPONSE, 1, "Claude")
        assert isinstance(result, SessionAnalysisResponse)
        assert result.intensity_rating == "moderat"
        assert result.session_id == 1
        assert result.provider == "Claude"

    def test_json_with_provider_prefix(self) -> None:
        """JSON mit Provider-Prefix wird korrekt geparst."""
        raw = f"[Claude (claude-sonnet-4-20250514)] {MOCK_AI_RESPONSE}"
        result = _parse_analysis_json(raw, 1, "Claude")
        assert result.intensity_rating == "moderat"

    def test_json_with_markdown_codeblock(self) -> None:
        """JSON in Markdown-Codeblock wird korrekt geparst."""
        raw = f"```json\n{MOCK_AI_RESPONSE}\n```"
        result = _parse_analysis_json(raw, 1, "Claude")
        assert result.intensity_rating == "moderat"

    def test_invalid_json_fallback(self) -> None:
        """Ungültiges JSON ergibt Fallback-Response."""
        result = _parse_analysis_json("Das ist kein JSON.", 1, "Claude")
        assert result.intensity_rating == "moderat"
        assert "Das ist kein JSON." in result.summary
        assert len(result.recommendations) >= 1
