"""Tests für Fitness-Profil-Aggregation."""

from __future__ import annotations

import sys
from datetime import date
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock für DB-Models (Python 3.9 kann `str | None` Syntax nicht parsen)
_mock_models = ModuleType("app.infrastructure.database.models")
for _name in (
    "AthleteModel",
    "RaceGoalModel",
    "ThresholdTestModel",
    "WorkoutModel",
    "Base",
):
    setattr(_mock_models, _name, MagicMock())
sys.modules.setdefault("app.infrastructure.database.models", _mock_models)

from app.services.athlete_fitness import (  # noqa: E402
    FitnessProfile,
    _assess_data_quality,
    _estimate_vdot_from_data,
    build_fitness_profile,
)

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


_MODULE = "app.services.athlete_fitness"


# ---------------------------------------------------------------------------
# build_fitness_profile — Tests mit gepatchten internen Funktionen
# ---------------------------------------------------------------------------


class TestBuildFitnessProfile:
    """Fitness-Profil-Aggregation aus DB-Daten."""

    @pytest.mark.asyncio
    async def test_full_data_high_quality(self) -> None:
        """Alle Datenquellen vorhanden → high quality."""
        db = AsyncMock()
        with (
            patch(
                f"{_MODULE}._get_threshold_data",
                return_value={
                    "lthr": 170,
                    "max_hr_measured": 190,
                    "avg_pace_sec": 300.0,
                    "test_date": date(2025, 1, 15),
                },
            ),
            patch(
                f"{_MODULE}._get_athlete_data",
                return_value={
                    "resting_hr": 52,
                    "max_hr": 188,
                },
            ),
            patch(
                f"{_MODULE}._get_training_history",
                return_value={
                    "avg_weekly_km": 25.0,
                    "avg_weekly_sessions": 3.0,
                    "weeks_consistent": 5,
                    "avg_easy_pace": 360.0,
                    "best_pace": 290.0,
                },
            ),
            patch(
                f"{_MODULE}._get_active_goal",
                return_value={
                    "distance_km": 21.0975,
                    "target_time_seconds": 6900,
                    "race_date": date(2025, 10, 15),
                },
            ),
        ):
            profile = await build_fitness_profile(db)

        assert isinstance(profile, FitnessProfile)
        assert profile.lthr == 170
        assert profile.max_hr == 190  # Schwellentest > Athlet
        assert profile.resting_hr == 52
        assert profile.vdot is not None
        assert profile.avg_weekly_km == 25.0
        assert profile.data_quality == "high"
        assert "threshold_test" in profile.data_sources
        assert "training_history" in profile.data_sources

    @pytest.mark.asyncio
    async def test_no_threshold_medium_quality(self) -> None:
        """Kein Schwellentest, aber Training → medium quality."""
        db = AsyncMock()
        with (
            patch(f"{_MODULE}._get_threshold_data", return_value=None),
            patch(
                f"{_MODULE}._get_athlete_data",
                return_value={
                    "resting_hr": 55,
                    "max_hr": 185,
                },
            ),
            patch(
                f"{_MODULE}._get_training_history",
                return_value={
                    "avg_weekly_km": 20.0,
                    "avg_weekly_sessions": 2.5,
                    "weeks_consistent": 5,
                    "avg_easy_pace": 380.0,
                    "best_pace": 310.0,
                },
            ),
            patch(f"{_MODULE}._get_active_goal", return_value=None),
        ):
            profile = await build_fitness_profile(db)

        assert profile.lthr is None
        assert profile.max_hr == 185
        assert profile.resting_hr == 55
        assert profile.vdot is not None
        assert profile.data_quality == "medium"

    @pytest.mark.asyncio
    async def test_no_data_none_quality(self) -> None:
        """Keine Daten vorhanden → none quality."""
        db = AsyncMock()
        with (
            patch(f"{_MODULE}._get_threshold_data", return_value=None),
            patch(f"{_MODULE}._get_athlete_data", return_value=None),
            patch(f"{_MODULE}._get_training_history", return_value=None),
            patch(f"{_MODULE}._get_active_goal", return_value=None),
        ):
            profile = await build_fitness_profile(db)

        assert profile.vdot is None
        assert profile.avg_weekly_km is None
        assert profile.data_quality == "none"
        assert profile.data_sources == []

    @pytest.mark.asyncio
    async def test_only_goal_low_quality(self) -> None:
        """Nur Race Goal → low quality (VDOT aus Zielzeit)."""
        db = AsyncMock()
        with (
            patch(f"{_MODULE}._get_threshold_data", return_value=None),
            patch(f"{_MODULE}._get_athlete_data", return_value=None),
            patch(f"{_MODULE}._get_training_history", return_value=None),
            patch(
                f"{_MODULE}._get_active_goal",
                return_value={
                    "distance_km": 21.0975,
                    "target_time_seconds": 6900,
                    "race_date": date(2025, 10, 15),
                },
            ),
        ):
            profile = await build_fitness_profile(db)

        assert profile.goal_distance_km == 21.0975
        assert profile.goal_time_seconds == 6900
        assert profile.vdot is not None
        assert profile.data_quality == "low"

    @pytest.mark.asyncio
    async def test_max_hr_priority_threshold_over_athlete(self) -> None:
        """Schwellentest-MaxHR hat Vorrang über Athleten-MaxHR."""
        db = AsyncMock()
        with (
            patch(
                f"{_MODULE}._get_threshold_data",
                return_value={
                    "lthr": 165,
                    "max_hr_measured": 195,
                    "avg_pace_sec": 300.0,
                    "test_date": date(2025, 1, 15),
                },
            ),
            patch(
                f"{_MODULE}._get_athlete_data",
                return_value={
                    "resting_hr": None,
                    "max_hr": 188,
                },
            ),
            patch(
                f"{_MODULE}._get_training_history",
                return_value={
                    "avg_weekly_km": 10.0,
                    "avg_weekly_sessions": 1.3,
                    "weeks_consistent": 1,
                    "avg_easy_pace": None,
                    "best_pace": None,
                },
            ),
            patch(f"{_MODULE}._get_active_goal", return_value=None),
        ):
            profile = await build_fitness_profile(db)

        assert profile.max_hr == 195  # Schwellentest, nicht Athlet (188)

    @pytest.mark.asyncio
    async def test_max_hr_fallback_to_athlete(self) -> None:
        """Kein MaxHR im Schwellentest → Fallback auf Athlet."""
        db = AsyncMock()
        with (
            patch(
                f"{_MODULE}._get_threshold_data",
                return_value={
                    "lthr": 165,
                    "max_hr_measured": None,
                    "avg_pace_sec": 300.0,
                    "test_date": date(2025, 1, 15),
                },
            ),
            patch(
                f"{_MODULE}._get_athlete_data",
                return_value={
                    "resting_hr": None,
                    "max_hr": 188,
                },
            ),
            patch(
                f"{_MODULE}._get_training_history",
                return_value={
                    "avg_weekly_km": 10.0,
                    "avg_weekly_sessions": 1.3,
                    "weeks_consistent": 1,
                    "avg_easy_pace": None,
                    "best_pace": None,
                },
            ),
            patch(f"{_MODULE}._get_active_goal", return_value=None),
        ):
            profile = await build_fitness_profile(db)

        assert profile.max_hr == 188  # Fallback auf Athlet

    @pytest.mark.asyncio
    async def test_goal_race_date_preserved(self) -> None:
        """Race Date wird korrekt übernommen."""
        race = date(2025, 9, 21)
        db = AsyncMock()
        with (
            patch(f"{_MODULE}._get_threshold_data", return_value=None),
            patch(f"{_MODULE}._get_athlete_data", return_value=None),
            patch(f"{_MODULE}._get_training_history", return_value=None),
            patch(
                f"{_MODULE}._get_active_goal",
                return_value={
                    "distance_km": 10.0,
                    "target_time_seconds": 3000,
                    "race_date": race,
                },
            ),
        ):
            profile = await build_fitness_profile(db)

        assert profile.goal_race_date == race


# ---------------------------------------------------------------------------
# VDOT-Schätzung
# ---------------------------------------------------------------------------


class TestVdotEstimation:
    """VDOT-Schätzung aus verschiedenen Datenquellen."""

    def test_from_threshold_pace(self) -> None:
        """VDOT aus Schwellentest-Pace (genaueste Quelle)."""
        hr_data = {"avg_pace_sec": 300.0}  # 5:00/km ≈ 10K in 50:00
        vdot = _estimate_vdot_from_data(hr_data, None, None)
        assert vdot is not None
        assert 35.0 <= vdot <= 55.0

    def test_from_best_pace(self) -> None:
        """VDOT aus bester kürzlicher Pace."""
        training_data = {"best_pace": 280.0}  # 4:40/km
        vdot = _estimate_vdot_from_data(None, training_data, None)
        assert vdot is not None
        assert 35.0 <= vdot <= 60.0

    def test_from_goal_time(self) -> None:
        """VDOT aus Zielzeit (konservativ)."""
        goal_data = {"distance_km": 21.0975, "target_time_seconds": 6900}
        vdot = _estimate_vdot_from_data(None, None, goal_data)
        assert vdot is not None
        # Konservativ (×0.92), daher niedriger als reiner Ziel-VDOT
        assert 30.0 <= vdot <= 50.0

    def test_priority_threshold_over_pace(self) -> None:
        """Schwellentest hat Vorrang über Trainingspace."""
        hr_data = {"avg_pace_sec": 300.0}
        training_data = {"best_pace": 280.0}
        vdot_threshold = _estimate_vdot_from_data(hr_data, None, None)
        vdot_both = _estimate_vdot_from_data(hr_data, training_data, None)
        # Wenn Schwellentest vorhanden → gleicher VDOT
        assert vdot_threshold == vdot_both

    def test_no_data_returns_none(self) -> None:
        """Keine Daten → None."""
        assert _estimate_vdot_from_data(None, None, None) is None

    def test_threshold_without_pace_falls_through(self) -> None:
        """Schwellentest ohne Pace → Fallback auf nächste Quelle."""
        hr_data = {"avg_pace_sec": None}
        training_data = {"best_pace": 300.0}
        vdot = _estimate_vdot_from_data(hr_data, training_data, None)
        assert vdot is not None  # Aus Trainingspace


# ---------------------------------------------------------------------------
# Datenqualität
# ---------------------------------------------------------------------------


class TestDataQuality:
    """Bewertung der Datenqualität."""

    def test_high_quality(self) -> None:
        sources = ["threshold_test", "training_history"]
        assert _assess_data_quality(sources, 45.0, {"weeks_consistent": 6}) == "high"

    def test_medium_quality_no_threshold(self) -> None:
        sources = ["training_history"]
        assert _assess_data_quality(sources, 42.0, {"weeks_consistent": 5}) == "medium"

    def test_low_quality_few_weeks(self) -> None:
        sources = ["training_history"]
        assert _assess_data_quality(sources, 40.0, {"weeks_consistent": 2}) == "low"

    def test_low_quality_vdot_only(self) -> None:
        sources = ["race_goal"]
        assert _assess_data_quality(sources, 38.0, None) == "low"

    def test_none_quality(self) -> None:
        assert _assess_data_quality([], None, None) == "none"

    def test_threshold_without_enough_training(self) -> None:
        """Schwellentest aber wenig Training → low (nicht high)."""
        sources = ["threshold_test"]
        assert _assess_data_quality(sources, 45.0, None) == "low"
