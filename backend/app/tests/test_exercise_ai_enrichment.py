"""Tests für Claude API Fallback bei Übungs-Anreicherung."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.services.exercise_ai_enrichment import (
    _validate_and_normalize,
    generate_exercise_enrichment,
)


class TestValidateAndNormalize:
    """Unit Tests für die Validierung der Claude-Antwort."""

    def test_valid_response(self) -> None:
        """Vollständige gültige Antwort wird korrekt normalisiert."""
        data = {
            "instructions": ["Schritt 1", "Schritt 2", "Schritt 3"],
            "primary_muscles": ["chest", "triceps"],
            "secondary_muscles": ["shoulders"],
            "equipment": "barbell",
            "level": "intermediate",
            "force": "push",
            "mechanic": "compound",
        }
        result = _validate_and_normalize(data)
        assert result is not None
        assert json.loads(result["instructions_json"]) == ["Schritt 1", "Schritt 2", "Schritt 3"]
        assert json.loads(result["primary_muscles_json"]) == ["chest", "triceps"]
        assert json.loads(result["secondary_muscles_json"]) == ["shoulders"]
        assert json.loads(result["image_urls_json"]) == []
        assert result["equipment"] == "barbell"
        assert result["level"] == "intermediate"
        assert result["force"] == "push"
        assert result["mechanic"] == "compound"
        assert result["exercise_db_id"] is None

    def test_missing_instructions_returns_none(self) -> None:
        """Fehlende Anleitungen führen zu None."""
        data = {
            "instructions": [],
            "primary_muscles": ["chest"],
        }
        assert _validate_and_normalize(data) is None

    def test_missing_primary_muscles_returns_none(self) -> None:
        """Fehlende Hauptmuskeln führen zu None."""
        data = {
            "instructions": ["Schritt 1"],
            "primary_muscles": [],
        }
        assert _validate_and_normalize(data) is None

    def test_invalid_muscles_filtered(self) -> None:
        """Ungültige Muskelnamen werden herausgefiltert."""
        data = {
            "instructions": ["Schritt 1"],
            "primary_muscles": ["chest", "invalid_muscle", "biceps"],
            "secondary_muscles": ["fake_muscle"],
        }
        result = _validate_and_normalize(data)
        assert result is not None
        assert json.loads(result["primary_muscles_json"]) == ["chest", "biceps"]
        assert json.loads(result["secondary_muscles_json"]) == []

    def test_invalid_equipment_becomes_none(self) -> None:
        """Ungültiges Equipment wird zu None."""
        data = {
            "instructions": ["Schritt 1"],
            "primary_muscles": ["chest"],
            "equipment": "invalid_thing",
        }
        result = _validate_and_normalize(data)
        assert result is not None
        assert result["equipment"] is None

    def test_invalid_level_becomes_none(self) -> None:
        """Ungültiges Level wird zu None."""
        data = {
            "instructions": ["Schritt 1"],
            "primary_muscles": ["chest"],
            "level": "expert",
        }
        result = _validate_and_normalize(data)
        assert result is not None
        assert result["level"] is None

    def test_invalid_force_becomes_none(self) -> None:
        """Ungültige Force wird zu None."""
        data = {
            "instructions": ["Schritt 1"],
            "primary_muscles": ["chest"],
            "force": "twist",
        }
        result = _validate_and_normalize(data)
        assert result is not None
        assert result["force"] is None

    def test_invalid_mechanic_becomes_none(self) -> None:
        """Ungültige Mechanic wird zu None."""
        data = {
            "instructions": ["Schritt 1"],
            "primary_muscles": ["chest"],
            "mechanic": "hybrid",
        }
        result = _validate_and_normalize(data)
        assert result is not None
        assert result["mechanic"] is None

    def test_instructions_not_a_list(self) -> None:
        """Instructions als String statt Liste gibt None."""
        data = {
            "instructions": "nur ein string",
            "primary_muscles": ["chest"],
        }
        assert _validate_and_normalize(data) is None

    def test_minimal_valid_response(self) -> None:
        """Minimale gültige Antwort (nur Pflichtfelder)."""
        data = {
            "instructions": ["Mach das"],
            "primary_muscles": ["quadriceps"],
        }
        result = _validate_and_normalize(data)
        assert result is not None
        assert json.loads(result["instructions_json"]) == ["Mach das"]
        assert json.loads(result["primary_muscles_json"]) == ["quadriceps"]
        assert json.loads(result["secondary_muscles_json"]) == []
        assert result["equipment"] is None
        assert result["level"] is None


class TestGenerateExerciseEnrichment:
    """Tests für die Claude API Integration."""

    @pytest.mark.asyncio
    async def test_no_api_key_returns_none(self) -> None:
        """Ohne API-Key wird sofort None zurückgegeben."""
        result = await generate_exercise_enrichment("Test Übung", "push", "")
        assert result is None

    @pytest.mark.asyncio
    async def test_successful_api_call(self) -> None:
        """Erfolgreicher API-Call gibt normalisierte Daten zurück."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "instructions": ["Schritt 1", "Schritt 2"],
                        "primary_muscles": ["chest", "triceps"],
                        "secondary_muscles": ["shoulders"],
                        "equipment": "barbell",
                        "level": "intermediate",
                        "force": "push",
                        "mechanic": "compound",
                    }
                )
            )
        ]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        with (
            patch("app.services.exercise_ai_enrichment.settings") as mock_settings,
            patch("app.services.exercise_ai_enrichment.anthropic") as mock_anthropic,
        ):
            mock_settings.claude_model = "claude-sonnet-4-20250514"
            mock_anthropic.Anthropic.return_value = mock_client

            result = await generate_exercise_enrichment("Bankdrücken", "push", "test-key")

        assert result is not None
        instructions_json = result["instructions_json"]
        assert instructions_json is not None
        assert json.loads(instructions_json) == ["Schritt 1", "Schritt 2"]
        primary_json = result["primary_muscles_json"]
        assert primary_json is not None
        assert json.loads(primary_json) == ["chest", "triceps"]
        assert result["equipment"] == "barbell"
        assert result["exercise_db_id"] is None

    @pytest.mark.asyncio
    async def test_api_error_returns_none(self) -> None:
        """API-Fehler gibt None zurück."""
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API timeout")

        with (
            patch("app.services.exercise_ai_enrichment.settings") as mock_settings,
            patch("app.services.exercise_ai_enrichment.anthropic") as mock_anthropic,
        ):
            mock_settings.claude_model = "claude-sonnet-4-20250514"
            mock_anthropic.Anthropic.return_value = mock_client

            result = await generate_exercise_enrichment("Test", "push", "test-key")

        assert result is None

    @pytest.mark.asyncio
    async def test_invalid_json_response_returns_none(self) -> None:
        """Ungültiges JSON von der API gibt None zurück."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Das ist kein JSON")]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        with (
            patch("app.services.exercise_ai_enrichment.settings") as mock_settings,
            patch("app.services.exercise_ai_enrichment.anthropic") as mock_anthropic,
        ):
            mock_settings.claude_model = "claude-sonnet-4-20250514"
            mock_anthropic.Anthropic.return_value = mock_client

            result = await generate_exercise_enrichment("Test", "push", "test-key")

        assert result is None

    @pytest.mark.asyncio
    async def test_valid_json_but_invalid_content_returns_none(self) -> None:
        """Gültiges JSON aber ungültiger Inhalt gibt None zurück."""
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    {
                        "instructions": [],
                        "primary_muscles": [],
                    }
                )
            )
        ]

        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response

        with (
            patch("app.services.exercise_ai_enrichment.settings") as mock_settings,
            patch("app.services.exercise_ai_enrichment.anthropic") as mock_anthropic,
        ):
            mock_settings.claude_model = "claude-sonnet-4-20250514"
            mock_anthropic.Anthropic.return_value = mock_client

            result = await generate_exercise_enrichment("Test", "push", "test-key")

        assert result is None
