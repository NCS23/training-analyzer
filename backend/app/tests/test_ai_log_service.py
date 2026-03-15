"""Tests für den zentralen KI-Logging-Service."""

from unittest.mock import AsyncMock

import pytest

from app.services.ai_log_service import AICallData, log_ai_call


class TestLogAiCall:
    """Tests für log_ai_call()."""

    @pytest.mark.asyncio
    async def test_creates_log_entry_with_all_fields(self) -> None:
        """Erstellt einen vollständigen Log-Eintrag."""
        mock_db = AsyncMock()

        await log_ai_call(
            mock_db,
            AICallData(
                use_case="session_analysis",
                provider="claude (claude-sonnet-4-20250514)",
                system_prompt="Du bist ein Trainer.",
                user_prompt="Analysiere diese Session.",
                raw_response='{"summary": "Gut gemacht."}',
                parsed_ok=True,
                duration_ms=1200,
                workout_id=42,
            ),
        )

        mock_db.add.assert_called_once()
        log_entry = mock_db.add.call_args[0][0]
        assert log_entry.use_case == "session_analysis"
        assert log_entry.provider == "claude (claude-sonnet-4-20250514)"
        assert log_entry.parsed_ok is True
        assert log_entry.duration_ms == 1200
        assert log_entry.workout_id == 42
        assert log_entry.context_label is None

    @pytest.mark.asyncio
    async def test_creates_log_entry_without_workout(self) -> None:
        """Log-Eintrag ohne workout_id (z.B. Übungs-Anreicherung)."""
        mock_db = AsyncMock()

        await log_ai_call(
            mock_db,
            AICallData(
                use_case="exercise_enrichment",
                provider="claude (claude-sonnet-4-20250514)",
                system_prompt="Fitness-Experte",
                user_prompt="Generiere Infos für Bankdrücken.",
                raw_response='{"instructions": ["Schritt 1"]}',
                parsed_ok=True,
                duration_ms=800,
                context_label="Bankdrücken",
            ),
        )

        mock_db.add.assert_called_once()
        log_entry = mock_db.add.call_args[0][0]
        assert log_entry.use_case == "exercise_enrichment"
        assert log_entry.workout_id is None
        assert log_entry.context_label == "Bankdrücken"

    @pytest.mark.asyncio
    async def test_creates_log_entry_for_failed_parse(self) -> None:
        """Log-Eintrag mit parsed_ok=False."""
        mock_db = AsyncMock()

        await log_ai_call(
            mock_db,
            AICallData(
                use_case="exercise_enrichment",
                provider="claude",
                system_prompt="",
                user_prompt="Test",
                raw_response="Kein JSON",
                parsed_ok=False,
            ),
        )

        mock_db.add.assert_called_once()
        log_entry = mock_db.add.call_args[0][0]
        assert log_entry.parsed_ok is False
        assert log_entry.duration_ms is None
