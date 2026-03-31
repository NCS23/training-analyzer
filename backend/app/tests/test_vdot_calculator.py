"""Tests für den VDOT-Rechner (Daniels' Running Formula)."""

import pytest

from app.services.vdot_calculator import (
    GoalAssessment,
    GoalCategory,
    equivalent_race_time,
    estimate_vdot,
    is_goal_realistic,
    training_paces_for_plan,
    training_paces_from_vdot,
)

# ---------------------------------------------------------------------------
# estimate_vdot
# ---------------------------------------------------------------------------


class TestEstimateVdot:
    """VDOT-Schätzung aus bekannter Leistung."""

    def test_5k_in_20_minutes(self) -> None:
        """20:00 auf 5K ≈ VDOT ~47-48 (Daniels-Tabelle)."""
        vdot = estimate_vdot(5.0, 20 * 60)
        assert vdot is not None
        assert 46.0 <= vdot <= 49.0

    def test_5k_in_25_minutes(self) -> None:
        """25:00 auf 5K ≈ VDOT ~36-38."""
        vdot = estimate_vdot(5.0, 25 * 60)
        assert vdot is not None
        assert 36.0 <= vdot <= 39.0

    def test_10k_in_50_minutes(self) -> None:
        """50:00 auf 10K ≈ VDOT ~38-41."""
        vdot = estimate_vdot(10.0, 50 * 60)
        assert vdot is not None
        assert 38.0 <= vdot <= 41.0

    def test_hm_sub_2h(self) -> None:
        """HM in 1:55:00 (6900s) ≈ VDOT ~36-39."""
        vdot = estimate_vdot(21.0975, 115 * 60)
        assert vdot is not None
        assert 36.0 <= vdot <= 39.0

    def test_hm_sub_1h30(self) -> None:
        """HM in 1:30:00 (5400s) ≈ VDOT ~48-50."""
        vdot = estimate_vdot(21.0975, 90 * 60)
        assert vdot is not None
        assert 47.0 <= vdot <= 50.0

    def test_marathon_sub_4h(self) -> None:
        """Marathon in 3:55:00 ≈ VDOT ~37-40."""
        vdot = estimate_vdot(42.195, 3 * 3600 + 55 * 60)
        assert vdot is not None
        assert 37.0 <= vdot <= 40.0

    def test_marathon_sub_3h(self) -> None:
        """Marathon in 2:59:00 ≈ VDOT ~50-53."""
        vdot = estimate_vdot(42.195, 2 * 3600 + 59 * 60)
        assert vdot is not None
        assert 50.0 <= vdot <= 53.0

    def test_very_slow_returns_lower_bound(self) -> None:
        """Sehr langsame Zeit wird auf Untergrenze geclampt."""
        vdot = estimate_vdot(5.0, 60 * 60)  # 1h auf 5K
        assert vdot is not None
        assert vdot == pytest.approx(30.0, abs=1.0)

    def test_very_fast_returns_upper_bound(self) -> None:
        """Sehr schnelle Zeit wird auf Obergrenze geclampt."""
        vdot = estimate_vdot(5.0, 10 * 60)  # 10:00 auf 5K
        assert vdot is not None
        assert vdot >= 80.0

    def test_invalid_time_returns_none(self) -> None:
        """Ungültige Zeit gibt None zurück."""
        assert estimate_vdot(5.0, 0) is None
        assert estimate_vdot(5.0, -100) is None

    def test_invalid_distance_returns_none(self) -> None:
        """Ungültige Distanz gibt None zurück."""
        assert estimate_vdot(0, 1200) is None
        assert estimate_vdot(-5, 1200) is None

    def test_non_standard_distance_3k(self) -> None:
        """Nicht-Standard-Distanz (3K) über Pace-Extrapolation."""
        vdot = estimate_vdot(3.0, 12 * 60)  # 12:00 auf 3K
        assert vdot is not None
        assert 35.0 <= vdot <= 50.0  # Plausibilitätscheck

    def test_non_standard_distance_8k(self) -> None:
        """Nicht-Standard-Distanz (8K) über Riegel-Formel."""
        vdot = estimate_vdot(8.0, 35 * 60)  # 35:00 auf 8K
        assert vdot is not None
        assert 35.0 <= vdot <= 50.0

    def test_1500m_distance(self) -> None:
        """1500m-Zeit wird korrekt erkannt (Toleranz ±5%)."""
        vdot = estimate_vdot(1.5, 5 * 60 + 30)  # 5:30 auf 1500m
        assert vdot is not None
        assert 47.0 <= vdot <= 51.0

    def test_monotonicity_faster_time_higher_vdot(self) -> None:
        """Schnellere Zeit = höherer VDOT."""
        vdot_slow = estimate_vdot(5.0, 25 * 60)
        vdot_fast = estimate_vdot(5.0, 20 * 60)
        assert vdot_slow is not None
        assert vdot_fast is not None
        assert vdot_fast > vdot_slow


# ---------------------------------------------------------------------------
# training_paces_from_vdot
# ---------------------------------------------------------------------------


class TestTrainingPaces:
    """Daniels-Trainingszonen aus VDOT."""

    def test_returns_all_zones(self) -> None:
        """Alle fünf Daniels-Zonen werden zurückgegeben."""
        paces = training_paces_from_vdot(50.0)
        assert set(paces.keys()) == {"easy", "marathon", "threshold", "interval", "repetition"}

    def test_zone_ordering(self) -> None:
        """Schnellere Zonen haben niedrigere sec/km Werte."""
        paces = training_paces_from_vdot(50.0)
        # Repetition < Interval < Threshold < Marathon < Easy
        assert paces["repetition"][1] < paces["interval"][1]
        assert paces["interval"][1] < paces["threshold"][1]
        assert paces["threshold"][1] < paces["marathon"][1]
        assert paces["marathon"][1] < paces["easy"][1]

    def test_each_zone_has_range(self) -> None:
        """Jede Zone hat min < max (schnell < langsam)."""
        paces = training_paces_from_vdot(50.0)
        for zone, (fast, slow) in paces.items():
            assert fast < slow, f"Zone {zone}: {fast} sollte < {slow} sein"

    def test_higher_vdot_faster_paces(self) -> None:
        """Höherer VDOT = schnellere Paces in allen Zonen."""
        paces_40 = training_paces_from_vdot(40.0)
        paces_60 = training_paces_from_vdot(60.0)
        for zone in paces_40:
            assert paces_60[zone][0] < paces_40[zone][0], (
                f"Zone {zone}: VDOT 60 sollte schneller sein als VDOT 40"
            )

    def test_easy_pace_plausibility_vdot_50(self) -> None:
        """VDOT 50: Easy Pace sollte ca. 4:45-5:20 min/km sein."""
        paces = training_paces_from_vdot(50.0)
        fast, slow = paces["easy"]
        assert 270 <= fast <= 330, f"Easy fast {fast}s/km unplausibel"
        assert 300 <= slow <= 360, f"Easy slow {slow}s/km unplausibel"

    def test_threshold_pace_plausibility_vdot_50(self) -> None:
        """VDOT 50: Threshold Pace sollte ca. 4:00-4:15 min/km sein."""
        paces = training_paces_from_vdot(50.0)
        fast, slow = paces["threshold"]
        assert 230 <= fast <= 270, f"Threshold fast {fast}s/km unplausibel"
        assert 240 <= slow <= 280, f"Threshold slow {slow}s/km unplausibel"


class TestTrainingPacesForPlan:
    """Plan-Generator-kompatible Trainingszonen."""

    def test_returns_all_plan_zones(self) -> None:
        """Alle Plan-Generator Session-Typen sind abgedeckt."""
        paces = training_paces_for_plan(50.0)
        expected_keys = {
            "easy",
            "recovery",
            "tempo",
            "intervals",
            "long_run",
            "progression",
            "repetitions",
            "fartlek",
            "race",
            "marathon_race",
        }
        assert set(paces.keys()) == expected_keys

    def test_recovery_slower_than_easy(self) -> None:
        """Recovery ist langsamer als Easy."""
        paces = training_paces_for_plan(50.0)
        assert paces["recovery"][0] >= paces["easy"][0]

    def test_tempo_faster_than_easy(self) -> None:
        """Tempo ist schneller als Easy."""
        paces = training_paces_for_plan(50.0)
        assert paces["tempo"][1] < paces["easy"][0]

    def test_intervals_faster_than_tempo(self) -> None:
        """Intervalle sind schneller als Tempo."""
        paces = training_paces_for_plan(50.0)
        assert paces["intervals"][1] < paces["tempo"][0]


# ---------------------------------------------------------------------------
# equivalent_race_time
# ---------------------------------------------------------------------------


class TestEquivalentRaceTime:
    """Äquivalente Wettkampfzeiten."""

    def test_5k_from_vdot_50(self) -> None:
        """VDOT 50 → 5K in ca. 19:00-19:30."""
        time = equivalent_race_time(50.0, 5.0)
        assert time is not None
        assert 1100 <= time <= 1200  # 18:20 - 20:00

    def test_hm_from_vdot_50(self) -> None:
        """VDOT 50 → HM in ca. 1:27-1:29."""
        time = equivalent_race_time(50.0, 21.0975)
        assert time is not None
        assert 5200 <= time <= 5400  # ~1:27-1:30

    def test_marathon_from_vdot_50(self) -> None:
        """VDOT 50 → Marathon in ca. 3:03-3:06."""
        time = equivalent_race_time(50.0, 42.195)
        assert time is not None
        assert 10800 <= time <= 11400  # 3:00-3:10

    def test_higher_vdot_faster_time(self) -> None:
        """Höherer VDOT = schnellere Zeit."""
        time_40 = equivalent_race_time(40.0, 21.0975)
        time_60 = equivalent_race_time(60.0, 21.0975)
        assert time_40 is not None
        assert time_60 is not None
        assert time_60 < time_40

    def test_non_standard_distance(self) -> None:
        """Nicht-Standard-Distanz (15K) wird über Riegel-Formel berechnet."""
        time = equivalent_race_time(50.0, 15.0)
        assert time is not None
        assert 3600 <= time <= 4200  # ~60-70 min

    def test_consistency_5k_roundtrip(self) -> None:
        """Roundtrip: 5K-Zeit → VDOT → 5K-Zeit sollte konsistent sein."""
        original_time = 20 * 60  # 20:00
        vdot = estimate_vdot(5.0, original_time)
        assert vdot is not None
        reconstructed = equivalent_race_time(vdot, 5.0)
        assert reconstructed is not None
        assert abs(reconstructed - original_time) < 30  # Max 30s Abweichung


# ---------------------------------------------------------------------------
# is_goal_realistic
# ---------------------------------------------------------------------------


class TestGoalValidation:
    """Ziel-Validierung."""

    def test_realistic_goal(self) -> None:
        """Ziel innerhalb 3% des aktuellen VDOT → realistic."""
        # VDOT 48 → HM ca. 1:31:18 (5478s). Ziel: 1:30:00 (5400s) → VDOT ~49
        result = is_goal_realistic(48.0, 21.0975, 5400)
        assert result.category == GoalCategory.REALISTIC
        assert result.current_vdot == 48.0

    def test_ambitious_goal(self) -> None:
        """Ziel 3-10% über VDOT → ambitious."""
        # VDOT 46 → HM ca. 1:35. Ziel: 1:30:00 (5400s) → VDOT ~49 (Gap ~6%)
        result = is_goal_realistic(46.0, 21.0975, 5400)
        assert result.category == GoalCategory.AMBITIOUS
        assert result.suggested_time_seconds is not None
        assert "ambitioniert" in result.message

    def test_unrealistic_goal(self) -> None:
        """Ziel >10% über VDOT → unrealistic."""
        # VDOT 35 → HM ca. 2:05. Ziel: 1:30:00 (5400s) → VDOT ~49
        result = is_goal_realistic(35.0, 21.0975, 5400)
        assert result.category == GoalCategory.UNREALISTIC
        assert result.suggested_time_seconds is not None
        assert "unrealistisch" in result.message

    def test_assessment_has_vdot_values(self) -> None:
        """Assessment enthält aktuelle und benötigte VDOT-Werte."""
        result = is_goal_realistic(45.0, 21.0975, 5400)
        assert result.current_vdot == 45.0
        assert result.required_vdot > 0

    def test_realistic_at_boundary(self) -> None:
        """Exakt aktuelles VDOT-Niveau → realistic."""
        time = equivalent_race_time(50.0, 21.0975)
        assert time is not None
        result = is_goal_realistic(50.0, 21.0975, time)
        assert result.category == GoalCategory.REALISTIC

    def test_returns_valid_model(self) -> None:
        """GoalAssessment ist ein gültiges Pydantic Model."""
        result = is_goal_realistic(50.0, 21.0975, 5400)
        assert isinstance(result, GoalAssessment)
        assert isinstance(result.category, GoalCategory)
        assert isinstance(result.message, str)
        assert len(result.message) > 10
