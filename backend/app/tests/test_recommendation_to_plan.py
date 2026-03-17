"""Tests für recommendation_to_plan_service."""

import json
from datetime import date

from app.services.recommendation_to_plan_service import (
    _build_instructions,
    _build_system_prompt,
    _build_user_prompt,
    _find_free_day,
    _merge_into_plan,
    _normalize_session,
    _parse_run_details_from_ai,
    _parse_sessions,
)

# ---------------------------------------------------------------------------
# _parse_run_details_from_ai
# ---------------------------------------------------------------------------


class TestParseRunDetailsFromAI:
    def test_valid_details(self) -> None:
        rd = _parse_run_details_from_ai(
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
        rd = _parse_run_details_from_ai({"run_type": "sprint"})
        assert rd["run_type"] == "easy"

    def test_non_dict_returns_default(self) -> None:
        rd = _parse_run_details_from_ai("not a dict")
        assert rd == {"run_type": "easy"}

    def test_duration_out_of_range_ignored(self) -> None:
        rd = _parse_run_details_from_ai({"run_type": "easy", "target_duration_minutes": 500})
        assert "target_duration_minutes" not in rd


# ---------------------------------------------------------------------------
# _normalize_session
# ---------------------------------------------------------------------------


class TestNormalizeSession:
    def test_valid_running_session(self) -> None:
        result = _normalize_session(
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

    def test_valid_strength_session(self) -> None:
        result = _normalize_session(
            {
                "day_of_week": 3,
                "training_type": "strength",
                "template_id": 5,
            }
        )
        assert result is not None
        assert result["training_type"] == "strength"
        assert result["template_id"] == 5

    def test_invalid_day_returns_none(self) -> None:
        assert _normalize_session({"day_of_week": 7, "training_type": "running"}) is None
        assert _normalize_session({"day_of_week": -1, "training_type": "running"}) is None
        assert _normalize_session({"day_of_week": "Mon", "training_type": "running"}) is None

    def test_invalid_training_type_returns_none(self) -> None:
        assert _normalize_session({"day_of_week": 0, "training_type": "yoga"}) is None

    def test_notes_truncated(self) -> None:
        result = _normalize_session(
            {
                "day_of_week": 0,
                "training_type": "running",
                "notes": "x" * 600,
            }
        )
        assert result is not None
        assert len(result["notes"]) == 500

    def test_invalid_template_id_ignored(self) -> None:
        result = _normalize_session(
            {
                "day_of_week": 0,
                "training_type": "strength",
                "template_id": "abc",
            }
        )
        assert result is not None
        assert "template_id" not in result


# ---------------------------------------------------------------------------
# _parse_sessions
# ---------------------------------------------------------------------------


class TestParseSessions:
    def test_valid_json_array(self) -> None:
        raw = json.dumps(
            [
                {"day_of_week": 0, "training_type": "running", "run_details": {"run_type": "easy"}},
                {"day_of_week": 2, "training_type": "strength"},
            ]
        )
        sessions = _parse_sessions(raw)
        assert len(sessions) == 2

    def test_markdown_codeblock_stripped(self) -> None:
        raw = '```json\n[{"day_of_week": 0, "training_type": "running"}]\n```'
        sessions = _parse_sessions(raw)
        assert len(sessions) == 1

    def test_invalid_json_returns_empty(self) -> None:
        assert _parse_sessions("not json") == []

    def test_non_array_returns_empty(self) -> None:
        assert _parse_sessions('{"key": "value"}') == []

    def test_invalid_items_filtered(self) -> None:
        raw = json.dumps(
            [
                {"day_of_week": 0, "training_type": "running"},
                {"day_of_week": 99, "training_type": "running"},  # ungültig
                "not a dict",
            ]
        )
        sessions = _parse_sessions(raw)
        assert len(sessions) == 1


# ---------------------------------------------------------------------------
# _find_free_day
# ---------------------------------------------------------------------------


class TestFindFreeDay:
    def test_finds_next_free_day(self) -> None:
        assert _find_free_day({0, 1, 2}, 0) == 3

    def test_wraps_around(self) -> None:
        assert _find_free_day({4, 5, 6}, 5) == 0

    def test_no_free_day_returns_none(self) -> None:
        assert _find_free_day({0, 1, 2, 3, 4, 5, 6}, 0) is None


# ---------------------------------------------------------------------------
# _merge_into_plan
# ---------------------------------------------------------------------------


class TestMergeIntoPlan:
    def test_new_sessions_on_free_days(self) -> None:
        existing = [{"day_of_week": 0, "is_rest_day": False}]
        new_sessions = [
            {"day_of_week": 1, "training_type": "running", "run_details": {"run_type": "easy"}}
        ]
        merged = _merge_into_plan(existing, new_sessions)
        assert len(merged) == 7
        assert len(merged[1].sessions) == 1

    def test_occupied_day_redirected(self) -> None:
        existing = [{"day_of_week": 0, "is_rest_day": False}]
        new_sessions = [
            {"day_of_week": 0, "training_type": "running", "run_details": {"run_type": "easy"}}
        ]
        merged = _merge_into_plan(existing, new_sessions)
        # Tag 0 ist belegt → Session wird auf nächsten freien Tag verschoben
        assert len(merged[0].sessions) == 0
        # Irgendein anderer Tag hat die Session
        placed = [e for e in merged if len(e.sessions) > 0]
        assert len(placed) == 1

    def test_all_days_occupied_skips_session(self) -> None:
        existing = [{"day_of_week": d, "is_rest_day": False} for d in range(7)]
        new_sessions = [
            {"day_of_week": 0, "training_type": "running", "run_details": {"run_type": "easy"}}
        ]
        merged = _merge_into_plan(existing, new_sessions)
        placed = [e for e in merged if len(e.sessions) > 0]
        assert len(placed) == 0

    def test_empty_days_stay_empty(self) -> None:
        merged = _merge_into_plan([], [])
        assert len(merged) == 7
        for entry in merged:
            assert len(entry.sessions) == 0


# ---------------------------------------------------------------------------
# Prompt-Builder
# ---------------------------------------------------------------------------


class TestPromptBuilders:
    def test_system_prompt_includes_valid_run_types(self) -> None:
        prompt = _build_system_prompt(None, date(2026, 3, 23))
        assert "easy" in prompt
        assert "intervals" in prompt
        assert "Trainingsplaner" in prompt

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

    def test_user_prompt_shows_occupied_days(self) -> None:
        existing = [{"day_of_week": 0, "is_rest_day": False}]
        prompt = _build_user_prompt(["Test"], existing, [])
        assert "Montag" in prompt
        assert "NICHT belegen" in prompt

    def test_user_prompt_shows_templates(self) -> None:
        templates = [{"id": 1, "name": "Oberkörper"}]
        prompt = _build_user_prompt(["Test"], [], templates)
        assert "Oberkörper" in prompt

    def test_instructions_format(self) -> None:
        instructions = _build_instructions()
        assert "JSON-Array" in instructions
        assert "day_of_week" in instructions
