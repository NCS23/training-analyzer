"""Tests für Ziel-Validierung und Warnsystem."""

from __future__ import annotations

from app.services.goal_validation import (
    get_equivalent_times,
    validate_goal,
    validate_goal_for_plan,
)


class TestValidateGoal:
    """Ziel-Validierung aus VDOT."""

    def test_realistic_goal(self) -> None:
        """Realistisches Ziel → valid=True, category=realistic."""
        result = validate_goal(48.0, 21.0975, 5478)  # ~VDOT 48 HM-Zeit
        assert result.valid is True
        assert result.category == "realistic"

    def test_ambitious_goal(self) -> None:
        """Ambitioniertes Ziel → valid=True, category=ambitious."""
        result = validate_goal(46.0, 21.0975, 5400)  # Gap ~6%
        assert result.valid is True
        assert result.category == "ambitious"

    def test_unrealistic_goal(self) -> None:
        """Unrealistisches Ziel → valid=False, category=unrealistic."""
        result = validate_goal(35.0, 21.0975, 5400)  # Riesiger Gap
        assert result.valid is False
        assert result.category == "unrealistic"
        assert result.suggested_time_formatted is not None

    def test_no_vdot_returns_unknown(self) -> None:
        """Kein VDOT → valid=True, category=unknown mit Hinweis."""
        result = validate_goal(None, 21.0975, 5400)
        assert result.valid is True
        assert result.category == "unknown"
        assert "Schwellentest" in result.message

    def test_result_has_vdot_values(self) -> None:
        result = validate_goal(48.0, 21.0975, 5400)
        assert result.current_vdot is not None
        assert result.required_vdot is not None


class TestGoalValidationResult:
    """GoalValidationResult Methoden."""

    def test_to_dict_realistic(self) -> None:
        result = validate_goal(48.0, 21.0975, 5478)
        d = result.to_dict()
        assert d["valid"] is True
        assert d["category"] == "realistic"
        assert "message" in d

    def test_to_dict_unrealistic_has_suggestion(self) -> None:
        result = validate_goal(35.0, 21.0975, 5400)
        d = result.to_dict()
        assert "suggested_time" in d
        assert d["suggested_time"] is not None

    def test_to_chat_warning_none_for_realistic(self) -> None:
        """Kein Warning für realistische Ziele."""
        result = validate_goal(48.0, 21.0975, 5478)
        assert result.to_chat_warning() is None

    def test_to_chat_warning_present_for_unrealistic(self) -> None:
        """Warning vorhanden für unrealistische Ziele."""
        result = validate_goal(35.0, 21.0975, 5400)
        warning = result.to_chat_warning()
        assert warning is not None
        assert "unrealistic" in warning.lower() or "Empfehlung" in warning

    def test_to_chat_warning_for_ambitious(self) -> None:
        """Warning vorhanden für ambitionierte Ziele."""
        result = validate_goal(46.0, 21.0975, 5400)
        warning = result.to_chat_warning()
        assert warning is not None
        assert "Ambitious" in warning or "ambitious" in warning.lower()


class TestValidateGoalForPlan:
    """Plan-Kontext Validierung."""

    def test_returns_none_for_realistic(self) -> None:
        """Kein Warning für realistische Ziele."""
        result = validate_goal_for_plan(48.0, 21.0975, 5478)
        assert result is None

    def test_returns_warning_for_unrealistic(self) -> None:
        result = validate_goal_for_plan(35.0, 21.0975, 5400)
        assert result is not None
        assert "Empfehlung" in result

    def test_returns_none_without_goal(self) -> None:
        """Ohne Ziel → keine Warnung."""
        assert validate_goal_for_plan(48.0, None, None) is None
        assert validate_goal_for_plan(48.0, 21.0975, None) is None


class TestGetEquivalentTimes:
    """Äquivalente Wettkampfzeiten."""

    def test_returns_all_distances(self) -> None:
        times = get_equivalent_times(50.0)
        assert "5K" in times
        assert "10K" in times
        assert "Halbmarathon" in times
        assert "Marathon" in times

    def test_format_is_time_string(self) -> None:
        times = get_equivalent_times(50.0)
        for label, time_str in times.items():
            assert ":" in time_str, f"{label}: {time_str}"

    def test_higher_vdot_faster_times(self) -> None:
        """Höherer VDOT = schnellere Zeiten."""
        times_40 = get_equivalent_times(40.0)
        times_60 = get_equivalent_times(60.0)
        # 5K VDOT 60 schneller als 5K VDOT 40
        assert times_60["5K"] < times_40["5K"]  # String-Vergleich funktioniert hier

    def test_plausible_hm_time_vdot_50(self) -> None:
        """VDOT 50 → HM ca. 1:27-1:30."""
        times = get_equivalent_times(50.0)
        hm = times["Halbmarathon"]
        assert hm.startswith("1:")  # > 1 Stunde
