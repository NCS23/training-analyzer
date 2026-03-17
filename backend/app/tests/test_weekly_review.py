"""Tests für wöchentliches KI-Trainingsreview (E06-S06)."""

import json
from datetime import date

import pytest

from app.models.weekly_review import (
    FatigueLevel,
    OverallRating,
    VolumeComparison,
    WeeklyReviewResponse,
)
from app.services.weekly_review_service import (
    WeeklyContext,
    _build_review_prompt,
    _calculate_volume,
    _ensure_str_list,
    _fallback_review,
    _normalize_review,
    _parse_review_json,
    _validate_week_start,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MONDAY = date(2026, 3, 16)  # Montag
TUESDAY = date(2026, 3, 17)  # Dienstag


def _make_context(
    sessions: list[dict] | None = None,
    volume: dict | None = None,
) -> WeeklyContext:
    return WeeklyContext(
        week_start=MONDAY,
        sessions=sessions or [],
        volume=volume
        or {
            "total_km": 42.0,
            "total_hours": 5.5,
            "session_count": 4,
            "run_count": 3,
            "strength_count": 1,
        },
        race_goal=None,
        current_phase=None,
        session_analyses=[],
    )


VALID_AI_RESPONSE = json.dumps(
    {
        "summary": "Gute Trainingswoche mit solider Grundlage.",
        "volume_comparison": {
            "actual_km": 42.0,
            "actual_sessions": 4,
            "actual_hours": 5.5,
        },
        "highlights": ["Guter Long Run", "Konstante Paces"],
        "improvements": ["Mehr Stretching"],
        "next_week_recommendations": [
            "Tempolauf am Dienstag einfuegen",
            "Ruhetag am Freitag",
        ],
        "overall_rating": "good",
        "fatigue_assessment": "moderate",
    }
)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class TestValidation:
    def test_valid_monday(self) -> None:
        _validate_week_start(MONDAY)  # Sollte keine Exception werfen

    def test_invalid_tuesday(self) -> None:
        with pytest.raises(ValueError, match="Montag"):
            _validate_week_start(TUESDAY)

    def test_invalid_sunday(self) -> None:
        with pytest.raises(ValueError, match="Montag"):
            _validate_week_start(date(2026, 3, 22))


# ---------------------------------------------------------------------------
# Volume Calculation
# ---------------------------------------------------------------------------


class TestCalculateVolume:
    def test_empty_sessions(self) -> None:
        vol = _calculate_volume([])
        assert vol["total_km"] == 0
        assert vol["session_count"] == 0

    def test_mixed_sessions(self) -> None:
        class FakeSession:
            def __init__(
                self, distance_km: float | None, duration_sec: int | None, workout_type: str
            ) -> None:
                self.distance_km = distance_km
                self.duration_sec = duration_sec
                self.workout_type = workout_type

        sessions = [
            FakeSession(10.0, 3600, "running"),
            FakeSession(8.0, 2400, "running"),
            FakeSession(None, 3600, "strength"),
        ]
        vol = _calculate_volume(sessions)  # type: ignore[arg-type]
        assert vol["total_km"] == 18.0
        assert vol["run_count"] == 2
        assert vol["strength_count"] == 1
        assert vol["session_count"] == 3


# ---------------------------------------------------------------------------
# JSON Parsing
# ---------------------------------------------------------------------------


class TestParseReviewJson:
    def test_valid_json(self) -> None:
        ctx = _make_context()
        result = _parse_review_json(VALID_AI_RESPONSE, ctx)
        assert result["summary"] == "Gute Trainingswoche mit solider Grundlage."
        assert result["overall_rating"] == "good"
        assert len(result["highlights"]) == 2

    def test_markdown_codeblock(self) -> None:
        ctx = _make_context()
        wrapped = f"```json\n{VALID_AI_RESPONSE}\n```"
        result = _parse_review_json(wrapped, ctx)
        assert result["overall_rating"] == "good"

    def test_provider_tag(self) -> None:
        ctx = _make_context()
        tagged = f"[Claude (3.5 Sonnet)] {VALID_AI_RESPONSE}"
        result = _parse_review_json(tagged, ctx)
        assert result["overall_rating"] == "good"

    def test_invalid_json_fallback(self) -> None:
        ctx = _make_context()
        result = _parse_review_json("This is not JSON", ctx)
        assert "erneut versuchen" in result["summary"]
        assert result["overall_rating"] == "moderate"

    def test_invalid_rating_normalized(self) -> None:
        ctx = _make_context()
        data = json.loads(VALID_AI_RESPONSE)
        data["overall_rating"] = "super_duper"
        result = _normalize_review(data, ctx)
        assert result["overall_rating"] == "moderate"

    def test_invalid_fatigue_normalized(self) -> None:
        ctx = _make_context()
        data = json.loads(VALID_AI_RESPONSE)
        data["fatigue_assessment"] = "extreme"
        result = _normalize_review(data, ctx)
        assert result["fatigue_assessment"] == "moderate"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestEnsureStrList:
    def test_list(self) -> None:
        assert _ensure_str_list(["a", "b"]) == ["a", "b"]

    def test_string(self) -> None:
        assert _ensure_str_list("hello") == ["hello"]

    def test_empty_list(self) -> None:
        assert _ensure_str_list([]) == []

    def test_none(self) -> None:
        assert _ensure_str_list(None) == []

    def test_filters_empty(self) -> None:
        assert _ensure_str_list(["a", "", "b"]) == ["a", "b"]


# ---------------------------------------------------------------------------
# Prompt Builder
# ---------------------------------------------------------------------------


class TestBuildPrompt:
    def test_includes_week_dates(self) -> None:
        ctx = _make_context()
        prompt = _build_review_prompt(ctx)
        assert "16.03.2026" in prompt
        assert "22.03.2026" in prompt

    def test_includes_sessions(self) -> None:
        ctx = _make_context(
            sessions=[
                {
                    "date": "2026-03-16",
                    "type": "running",
                    "subtype": "easy",
                    "distance_km": 10.0,
                    "pace": "5:30",
                }
            ]
        )
        prompt = _build_review_prompt(ctx)
        assert "easy" in prompt
        assert "10.0 km" in prompt

    def test_empty_sessions(self) -> None:
        ctx = _make_context()
        prompt = _build_review_prompt(ctx)
        assert "Keine Sessions" in prompt

    def test_includes_volume(self) -> None:
        ctx = _make_context()
        prompt = _build_review_prompt(ctx)
        assert "42.0 km" in prompt
        assert "5.5 Stunden" in prompt


# ---------------------------------------------------------------------------
# Fallback
# ---------------------------------------------------------------------------


class TestFallback:
    def test_fallback_uses_context_volume(self) -> None:
        ctx = _make_context(
            volume={
                "total_km": 30.0,
                "total_hours": 4.0,
                "session_count": 3,
                "run_count": 2,
                "strength_count": 1,
            }
        )
        result = _fallback_review(ctx)
        assert result["volume_comparison"]["actual_km"] == 30.0
        assert result["volume_comparison"]["actual_sessions"] == 3


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------


class TestModels:
    def test_weekly_review_response(self) -> None:
        response = WeeklyReviewResponse(
            id=1,
            week_start="2026-03-16",
            summary="Gute Woche",
            volume_comparison=VolumeComparison(
                actual_km=42.0,
                actual_sessions=4,
                actual_hours=5.5,
            ),
            highlights=["A"],
            improvements=["B"],
            next_week_recommendations=["C"],
            overall_rating=OverallRating.GOOD,
            fatigue_assessment=FatigueLevel.MODERATE,
            session_count=4,
            provider="Claude",
            cached=False,
            created_at="2026-03-17T10:00:00",
        )
        assert response.overall_rating == OverallRating.GOOD
        assert response.volume_comparison.actual_km == 42.0

    def test_overall_rating_enum(self) -> None:
        assert OverallRating.EXCELLENT.value == "excellent"
        assert OverallRating.POOR.value == "poor"

    def test_fatigue_level_enum(self) -> None:
        assert FatigueLevel.LOW.value == "low"
        assert FatigueLevel.CRITICAL.value == "critical"
