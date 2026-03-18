"""Tests für recommendation_to_plan_service."""

import json
from datetime import date

from app.services.recommendation_to_plan_service import (
    _build_entries,
    _build_instructions,
    _build_system_prompt,
    _build_user_prompt,
    _format_plan_day,
    _normalize_day,
    _parse_plan,
    _parse_run_details,
)

# ---------------------------------------------------------------------------
# _parse_run_details
# ---------------------------------------------------------------------------


class TestParseRunDetails:
    def test_valid_details(self) -> None:
        rd = _parse_run_details(
            {
                "run_type": "easy",
                "target_duration_minutes": 45,
                "target_pace_min": "6:30",
                "target_pace_max": "7:00",
            }
        )
        assert rd["run_type"] == "easy"
        assert rd["target_duration_minutes"] == 45
        assert rd["target_pace_min"] == "6:30"

    def test_invalid_run_type_falls_back_to_easy(self) -> None:
        rd = _parse_run_details({"run_type": "sprint"})
        assert rd["run_type"] == "easy"

    def test_non_dict_returns_default(self) -> None:
        rd = _parse_run_details("not a dict")
        assert rd == {"run_type": "easy"}

    def test_duration_out_of_range_ignored(self) -> None:
        rd = _parse_run_details({"run_type": "easy", "target_duration_minutes": 500})
        assert "target_duration_minutes" not in rd


# ---------------------------------------------------------------------------
# _normalize_day
# ---------------------------------------------------------------------------


class TestNormalizeDay:
    def test_valid_running_day(self) -> None:
        result = _normalize_day(
            {
                "day_of_week": 1,
                "training_type": "running",
                "run_details": {"run_type": "tempo", "target_duration_minutes": 40},
                "notes": "Tempo-Lauf",
            }
        )
        assert result is not None
        assert result["day_of_week"] == 1
        assert result["training_type"] == "running"
        assert result["run_details"]["run_type"] == "tempo"
        assert result["notes"] == "Tempo-Lauf"

    def test_valid_strength_day(self) -> None:
        result = _normalize_day(
            {
                "day_of_week": 3,
                "training_type": "strength",
                "template_id": 5,
            }
        )
        assert result is not None
        assert result["training_type"] == "strength"
        assert result["template_id"] == 5

    def test_rest_day(self) -> None:
        result = _normalize_day({"day_of_week": 0, "is_rest_day": True})
        assert result is not None
        assert result["is_rest_day"] is True

    def test_invalid_day_returns_none(self) -> None:
        assert _normalize_day({"day_of_week": 7, "training_type": "running"}) is None
        assert _normalize_day({"day_of_week": -1, "training_type": "running"}) is None
        assert _normalize_day({"day_of_week": "Mon", "training_type": "running"}) is None

    def test_invalid_training_type_becomes_rest_day(self) -> None:
        result = _normalize_day({"day_of_week": 0, "training_type": "yoga"})
        assert result is not None
        assert result["is_rest_day"] is True

    def test_notes_truncated(self) -> None:
        result = _normalize_day(
            {
                "day_of_week": 0,
                "training_type": "running",
                "notes": "x" * 600,
            }
        )
        assert result is not None
        assert len(result["notes"]) == 500

    def test_invalid_template_id_ignored(self) -> None:
        result = _normalize_day(
            {
                "day_of_week": 0,
                "training_type": "strength",
                "template_id": "abc",
            }
        )
        assert result is not None
        assert "template_id" not in result


# ---------------------------------------------------------------------------
# _parse_plan
# ---------------------------------------------------------------------------


class TestParsePlan:
    def test_valid_json_array(self) -> None:
        raw = json.dumps(
            [
                {"day_of_week": 0, "is_rest_day": True},
                {"day_of_week": 1, "training_type": "running", "run_details": {"run_type": "easy"}},
                {"day_of_week": 2, "training_type": "strength"},
            ]
        )
        days = _parse_plan(raw)
        assert len(days) == 3

    def test_markdown_codeblock_stripped(self) -> None:
        raw = '```json\n[{"day_of_week": 0, "is_rest_day": true}]\n```'
        days = _parse_plan(raw)
        assert len(days) == 1

    def test_invalid_json_returns_empty(self) -> None:
        assert _parse_plan("not json") == []

    def test_non_array_returns_empty(self) -> None:
        assert _parse_plan('{"key": "value"}') == []

    def test_invalid_items_filtered(self) -> None:
        raw = json.dumps(
            [
                {"day_of_week": 0, "is_rest_day": True},
                {"day_of_week": 99, "training_type": "running"},  # ungültig
                "not a dict",
            ]
        )
        days = _parse_plan(raw)
        assert len(days) == 1

    def test_full_7_day_plan(self) -> None:
        raw = json.dumps(
            [
                {"day_of_week": 0, "is_rest_day": True},
                {
                    "day_of_week": 1,
                    "training_type": "running",
                    "run_details": {"run_type": "easy"},
                },
                {
                    "day_of_week": 2,
                    "training_type": "running",
                    "run_details": {"run_type": "tempo"},
                },
                {"day_of_week": 3, "is_rest_day": True},
                {"day_of_week": 4, "training_type": "strength"},
                {
                    "day_of_week": 5,
                    "training_type": "running",
                    "run_details": {"run_type": "long_run"},
                },
                {"day_of_week": 6, "is_rest_day": True},
            ]
        )
        days = _parse_plan(raw)
        assert len(days) == 7


# ---------------------------------------------------------------------------
# _build_entries
# ---------------------------------------------------------------------------


class TestBuildEntries:
    def test_builds_7_entries(self) -> None:
        ai_days: list[dict] = [
            {"day_of_week": 0, "is_rest_day": True},
            {"day_of_week": 1, "training_type": "running", "run_details": {"run_type": "easy"}},
        ]
        entries = _build_entries(ai_days)
        assert len(entries) == 7
        assert entries[0].is_rest_day is True
        assert len(entries[1].sessions) == 1
        assert entries[1].sessions[0].training_type == "running"
        # Nicht von KI gelieferte Tage = leer
        assert len(entries[2].sessions) == 0

    def test_empty_ai_days(self) -> None:
        entries = _build_entries([])
        assert len(entries) == 7
        for e in entries:
            assert len(e.sessions) == 0


# ---------------------------------------------------------------------------
# _format_plan_day
# ---------------------------------------------------------------------------


class TestFormatPlanDay:
    def test_rest_day(self) -> None:
        result = _format_plan_day("Montag", {"is_rest_day": True, "sessions": []})
        assert "Ruhetag" in result
        assert "Montag" in result

    def test_running_day(self) -> None:
        entry = {
            "is_rest_day": False,
            "notes": "Locker laufen",
            "sessions": [
                {
                    "training_type": "running",
                    "run_details": {"run_type": "easy", "target_duration_minutes": 45},
                }
            ],
        }
        result = _format_plan_day("Dienstag", entry)
        assert "Dienstag" in result
        assert "running" in result
        assert "easy" in result
        assert "45min" in result

    def test_empty_sessions(self) -> None:
        result = _format_plan_day("Mittwoch", {"is_rest_day": False, "sessions": []})
        assert "(leer)" in result


# ---------------------------------------------------------------------------
# Prompt-Builder
# ---------------------------------------------------------------------------


class TestPromptBuilders:
    def test_system_prompt_includes_valid_run_types(self) -> None:
        prompt = _build_system_prompt(None, date(2026, 3, 23))
        assert "easy" in prompt
        assert "intervals" in prompt
        assert "Trainingsplaner" in prompt

    def test_system_prompt_mentions_plan_adjustment(self) -> None:
        prompt = _build_system_prompt(None, date(2026, 3, 23))
        assert "anpass" in prompt.lower() or "bestehend" in prompt.lower()

    def test_system_prompt_with_race_goal(self) -> None:
        goal = {"title": "Halbmarathon", "distance_km": 21.1, "date": "2026-03-29"}
        prompt = _build_system_prompt(goal, date(2026, 3, 23))
        assert "Halbmarathon" in prompt
        assert "21.1" in prompt

    def test_user_prompt_includes_recommendations(self) -> None:
        recs = ["Mehr Tempo-Läufe einbauen", "Kraft-Training 2x pro Woche"]
        prompt = _build_user_prompt(recs, [], [])
        assert "Mehr Tempo-Läufe" in prompt
        assert "Kraft-Training" in prompt

    def test_user_prompt_shows_existing_plan(self) -> None:
        existing: list[dict] = [
            {
                "day_of_week": 0,
                "is_rest_day": True,
                "notes": None,
                "plan_id": 1,
                "sessions": [],
            },
            {
                "day_of_week": 1,
                "is_rest_day": False,
                "notes": None,
                "plan_id": 1,
                "sessions": [{"training_type": "running", "run_details": {"run_type": "easy"}}],
            },
        ]
        prompt = _build_user_prompt(["Test"], existing, [])
        assert "Montag" in prompt
        assert "Ruhetag" in prompt
        assert "Dienstag" in prompt
        assert "running" in prompt

    def test_user_prompt_shows_templates(self) -> None:
        templates = [{"id": 1, "name": "Oberkörper"}]
        prompt = _build_user_prompt(["Test"], [], templates)
        assert "Oberkörper" in prompt

    def test_instructions_mention_all_7_days(self) -> None:
        instructions = _build_instructions()
        assert "ALLE 7 Tage" in instructions
        assert "day_of_week" in instructions
        assert "Passe bestehende Sessions an" in instructions
