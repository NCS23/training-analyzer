"""Tests für die Fitness-Score Engine.

Testet TRIMP-Berechnung, CTL/ATL/TSB, Form-Indikator, ACWR, Trend und Score-Normalisierung.
"""

from datetime import date, timedelta
from typing import Any
from unittest.mock import MagicMock

from app.services.fitness_score import (
    _ewma_update,
    _get_hr_zone,
    _trimp_from_avg_hr,
    _trimp_from_hr_timeseries,
    calculate_acwr,
    calculate_fitness_metrics,
    calculate_form,
    calculate_trend,
    calculate_trimp,
    compute_full_score,
    generate_context_message,
    normalize_score,
)

# ---------------------------------------------------------------------------
# HR-Zonen Tests
# ---------------------------------------------------------------------------


class TestGetHRZone:
    """Karvonen HR-Zonen-Bestimmung."""

    def test_zone_1_low_intensity(self) -> None:
        # Resting=60, Max=200 → HRR=140
        # Zone 1: 60 + 140*0.5 = 130 bis 60 + 140*0.6 = 144
        assert _get_hr_zone(135.0, 60, 200) == 1

    def test_zone_2(self) -> None:
        # Zone 2: 144-158
        assert _get_hr_zone(150.0, 60, 200) == 2

    def test_zone_3(self) -> None:
        # Zone 3: 158-172
        assert _get_hr_zone(165.0, 60, 200) == 3

    def test_zone_4(self) -> None:
        # Zone 4: 172-186
        assert _get_hr_zone(180.0, 60, 200) == 4

    def test_zone_5(self) -> None:
        # Zone 5: 186+
        assert _get_hr_zone(195.0, 60, 200) == 5

    def test_below_zone_1_returns_zone_1(self) -> None:
        assert _get_hr_zone(100.0, 60, 200) == 1

    def test_at_max_hr_returns_zone_5(self) -> None:
        assert _get_hr_zone(200.0, 60, 200) == 5

    def test_invalid_hr_range_returns_zone_1(self) -> None:
        assert _get_hr_zone(100.0, 200, 100) == 1


# ---------------------------------------------------------------------------
# TRIMP Tests
# ---------------------------------------------------------------------------


class TestTRIMPFromTimeseries:
    """Edwards TRIMP aus sekündlichen HR-Daten."""

    def test_30_min_zone_2(self) -> None:
        # 30 Min = 1800 Sekunden in Zone 2 → 30 * 2 = 60 TRIMP
        hr_data = [150] * 1800  # Alles Zone 2 bei resting=60, max=200
        trimp = _trimp_from_hr_timeseries(hr_data, 60, 200)
        assert trimp == 60.0

    def test_mixed_zones(self) -> None:
        # 10 Min Zone 1 (600s) + 10 Min Zone 3 (600s)
        hr_data = [135] * 600 + [165] * 600
        trimp = _trimp_from_hr_timeseries(hr_data, 60, 200)
        # Zone 1: 10*1=10, Zone 3: 10*3=30 → 40
        assert trimp == 40.0

    def test_empty_data_returns_zero(self) -> None:
        assert _trimp_from_hr_timeseries([], 60, 200) == 0.0

    def test_zero_hr_values_ignored(self) -> None:
        hr_data = [0, 0, 0]
        assert _trimp_from_hr_timeseries(hr_data, 60, 200) == 0.0


class TestTRIMPFromAvgHR:
    """TRIMP-Schätzung aus Durchschnitts-HR."""

    def test_60_min_zone_2(self) -> None:
        # 60 Min bei 150 bpm (Zone 2) → 60 * 2 = 120
        trimp = _trimp_from_avg_hr(150, 3600, 60, 200)
        assert trimp == 120.0

    def test_30_min_zone_4(self) -> None:
        # 30 Min bei 180 bpm (Zone 4) → 30 * 4 = 120
        trimp = _trimp_from_avg_hr(180, 1800, 60, 200)
        assert trimp == 120.0


class TestCalculateTRIMP:
    """Integration: TRIMP für verschiedene Session-Typen."""

    def _mock_session(self, **kwargs: object) -> MagicMock:
        session = MagicMock()
        session.workout_type = kwargs.get("workout_type", "running")
        session.hr_timeseries_json = kwargs.get("hr_timeseries_json")
        session.hr_zones_json = kwargs.get("hr_zones_json")
        session.hr_avg = kwargs.get("hr_avg")
        session.duration_sec = kwargs.get("duration_sec", 3600)
        session.athlete_resting_hr = kwargs.get("athlete_resting_hr", 60)
        session.athlete_max_hr = kwargs.get("athlete_max_hr", 200)
        session.rpe = kwargs.get("rpe")
        session.exercises_json = kwargs.get("exercises_json")
        session.trimp_score = kwargs.get("trimp_score")
        return session

    def test_running_with_avg_hr(self) -> None:
        session = self._mock_session(hr_avg=150, duration_sec=3600)
        trimp = calculate_trimp(session)
        assert trimp > 0

    def test_strength_with_rpe(self) -> None:
        session = self._mock_session(workout_type="strength", rpe=7, duration_sec=3600)
        trimp = calculate_trimp(session)
        # RPE 7 * 60 Min * 0.5 = 210
        assert trimp == 210.0

    def test_strength_without_rpe(self) -> None:
        session = self._mock_session(workout_type="strength", rpe=None, duration_sec=3600)
        trimp = calculate_trimp(session)
        # Fallback: 60 Min * 2.0 = 120
        assert trimp == 120.0

    def test_no_data_no_duration_returns_zero(self) -> None:
        session = self._mock_session(hr_avg=None, hr_timeseries_json=None, duration_sec=0)
        trimp = calculate_trimp(session)
        assert trimp == 0.0


# ---------------------------------------------------------------------------
# CTL / ATL / TSB Tests
# ---------------------------------------------------------------------------


class TestEWMA:
    """EWMA Update-Funktion."""

    def test_first_step_from_zero(self) -> None:
        # Von 0 mit TRIMP 42 und tau=42 → 42 * (1/42) = 1.0
        result = _ewma_update(0.0, 42.0, 42)
        assert abs(result - 1.0) < 0.01

    def test_decay_without_training(self) -> None:
        # Ohne Training: vorheriger Wert zerfällt
        result = _ewma_update(10.0, 0.0, 42)
        assert result < 10.0
        assert result > 9.0  # Nur leichter Zerfall bei tau=42


class TestFitnessMetrics:
    """CTL/ATL/TSB Berechnung."""

    def test_empty_data(self) -> None:
        metrics = calculate_fitness_metrics({})
        assert metrics.ctl == 0.0
        assert metrics.atl == 0.0
        assert metrics.tsb == 0.0

    def test_single_day_training(self) -> None:
        today = date.today()
        trimps = {today: 100.0}
        metrics = calculate_fitness_metrics(trimps, today)
        # Nach einem Tag: CTL sehr niedrig, ATL etwas höher
        assert metrics.ctl > 0
        assert metrics.atl > 0
        assert metrics.atl > metrics.ctl  # ATL reagiert schneller

    def test_consistent_training_builds_ctl(self) -> None:
        """6 Wochen tägliches Training sollte CTL aufbauen."""
        today = date.today()
        trimps = {}
        for i in range(42):
            d = today - timedelta(days=41 - i)
            trimps[d] = 50.0  # 50 TRIMP jeden Tag

        metrics = calculate_fitness_metrics(trimps, today)
        assert metrics.ctl > 30  # CTL sollte sich 50 annähern
        assert len(metrics.ctl_history) == 42

    def test_tsb_positive_after_rest(self) -> None:
        """Nach Trainingsblock + Ruhewoche: TSB positiv (frisch)."""
        today = date.today()
        trimps = {}
        # 3 Wochen hart trainieren
        for i in range(21):
            d = today - timedelta(days=27 - i)
            trimps[d] = 80.0
        # Dann 7 Tage Pause (kein Eintrag = 0 TRIMP)

        metrics = calculate_fitness_metrics(trimps, today)
        # TSB sollte positiv sein (CTL noch hoch, ATL gefallen)
        assert metrics.tsb > 0


# ---------------------------------------------------------------------------
# Normalisierung Tests
# ---------------------------------------------------------------------------


class TestNormalizeScore:
    """Score-Normalisierung auf 0-100 (absolute Referenzskala)."""

    def test_zero_ctl(self) -> None:
        assert normalize_score(0.0) == 0

    def test_negative_ctl(self) -> None:
        assert normalize_score(-5.0) == 0

    def test_low_ctl_beginner(self) -> None:
        """CTL ~5: Einsteiger → Score ca. 15-20."""
        score = normalize_score(5.0)
        assert 10 <= score <= 25

    def test_moderate_ctl_regular(self) -> None:
        """CTL ~30: Regelmäßiges Training → Score ca. 50."""
        score = normalize_score(30.0)
        assert 45 <= score <= 55

    def test_good_ctl_ambitious(self) -> None:
        """CTL ~60: Ambitionierter Hobbyathlet → Score ca. 65-70."""
        score = normalize_score(60.0)
        assert 62 <= score <= 72

    def test_high_ctl_trained(self) -> None:
        """CTL ~80: Gut trainiert → Score ca. 73-78."""
        score = normalize_score(80.0)
        assert 70 <= score <= 80

    def test_elite_ctl_capped(self) -> None:
        """CTL >200: Elite → Score maximal 100."""
        score = normalize_score(200.0)
        assert 95 <= score <= 100

    def test_monotonically_increasing(self) -> None:
        """Höherer CTL → höherer Score (immer)."""
        prev = 0
        for ctl in [1, 5, 10, 20, 30, 50, 80, 120]:
            score = normalize_score(float(ctl))
            assert score >= prev, f"Score fiel bei CTL={ctl}: {score} < {prev}"
            prev = score


# ---------------------------------------------------------------------------
# Form-Indikator Tests
# ---------------------------------------------------------------------------


class TestFormIndicator:
    """TSB → Form-Bewertung."""

    def test_fresh(self) -> None:
        form = calculate_form(15.0)
        assert form.status == "fresh"
        assert form.label == "Frisch"
        assert form.color == "green"

    def test_normal(self) -> None:
        form = calculate_form(0.0)
        assert form.status == "normal"

    def test_fatigued(self) -> None:
        form = calculate_form(-15.0)
        assert form.status == "fatigued"
        assert form.label == "Ermüdet"
        assert form.color == "orange"

    def test_borderline_fresh(self) -> None:
        form = calculate_form(10.1)
        assert form.status == "fresh"

    def test_borderline_fatigued(self) -> None:
        form = calculate_form(-10.1)
        assert form.status == "fatigued"


# ---------------------------------------------------------------------------
# ACWR Tests
# ---------------------------------------------------------------------------


class TestACWR:
    """Acute:Chronic Workload Ratio."""

    def test_optimal_range(self) -> None:
        result = calculate_acwr(10.0, 10.0)
        assert result is not None
        assert result.zone == "optimal"
        assert result.ratio == 1.0

    def test_danger_zone(self) -> None:
        result = calculate_acwr(20.0, 10.0)
        assert result is not None
        assert result.zone == "danger"
        assert result.ratio == 2.0

    def test_warning_zone(self) -> None:
        result = calculate_acwr(14.0, 10.0)
        assert result is not None
        assert result.zone == "warning"

    def test_low_zone(self) -> None:
        result = calculate_acwr(3.0, 10.0)
        assert result is not None
        assert result.zone == "low"

    def test_ctl_too_low_returns_none(self) -> None:
        result = calculate_acwr(5.0, 0.5)
        assert result is None


# ---------------------------------------------------------------------------
# Trend Tests
# ---------------------------------------------------------------------------


class TestTrend:
    """CTL-Trend über 14 Tage."""

    def test_rising(self) -> None:
        today = date.today()
        history = [
            (today - timedelta(days=14), 30.0),
            (today, 40.0),
        ]
        assert calculate_trend(history) == "rising"

    def test_falling(self) -> None:
        today = date.today()
        history = [
            (today - timedelta(days=14), 40.0),
            (today, 30.0),
        ]
        assert calculate_trend(history) == "falling"

    def test_stable(self) -> None:
        today = date.today()
        history = [
            (today - timedelta(days=14), 40.0),
            (today, 40.5),
        ]
        assert calculate_trend(history) == "stable"

    def test_empty_history(self) -> None:
        assert calculate_trend([]) == "stable"


# ---------------------------------------------------------------------------
# Kontext-Satz Tests
# ---------------------------------------------------------------------------


class TestContextMessage:
    """Dashboard-Kontext-Satz."""

    def test_acwr_danger_has_priority(self) -> None:
        from app.services.fitness_score import ACWRResult, FormIndicator

        form = FormIndicator("normal", "Normal", "yellow", "")
        acwr = ACWRResult(2.0, "danger", "Verletzungsrisiko!")
        msg = generate_context_message(50, "stable", form, acwr)
        assert "Verletzungsrisiko" in msg

    def test_fatigued_form(self) -> None:
        from app.services.fitness_score import FormIndicator

        form = FormIndicator("fatigued", "Ermüdet", "orange", "")
        msg = generate_context_message(50, "stable", form, None)
        assert "ermüdet" in msg.lower()

    def test_rising_trend(self) -> None:
        from app.services.fitness_score import FormIndicator

        form = FormIndicator("normal", "Normal", "yellow", "")
        msg = generate_context_message(50, "rising", form, None)
        assert "positiv" in msg.lower() or "weiter so" in msg.lower()

    def test_zero_score_new_user(self) -> None:
        from app.services.fitness_score import FormIndicator

        form = FormIndicator("normal", "Normal", "yellow", "")
        msg = generate_context_message(0, "stable", form, None)
        assert "erstes training" in msg.lower()


# ---------------------------------------------------------------------------
# Integrationstest: compute_full_score
# ---------------------------------------------------------------------------


class TestComputeFullScore:
    """End-to-End Score-Berechnung."""

    def _mock_session(self, days_ago: int, trimp: float, workout_type: str = "running") -> Any:
        session = MagicMock()
        session.date = date.today() - timedelta(days=days_ago)
        session.trimp_score = trimp
        session.workout_type = workout_type
        return session

    def test_no_sessions(self) -> None:
        result = compute_full_score([])
        assert result["score"] == 0
        assert result["form"]["status"] == "normal"

    def test_regular_training(self) -> None:
        sessions: Any = [self._mock_session(i, 60.0) for i in range(28)]
        result = compute_full_score(sessions)
        assert 0 < result["score"] < 100  # Sinnvoller Wert, nicht 100
        assert result["trend"] in ("rising", "stable", "falling")
        assert result["form"]["status"] in ("fresh", "normal", "fatigued")

    def test_mixed_running_and_strength(self) -> None:
        sessions: Any = [self._mock_session(i, 60.0, "running") for i in range(0, 28, 2)] + [
            self._mock_session(i, 40.0, "strength") for i in range(1, 28, 2)
        ]
        result = compute_full_score(sessions)
        assert result["endurance_score"] > 0
        assert result["strength_score"] > 0

    def test_no_new_max_ctl_in_result(self) -> None:
        """compute_full_score soll kein new_max_ctl mehr zurückgeben."""
        sessions: Any = [self._mock_session(i, 60.0) for i in range(7)]
        result = compute_full_score(sessions)
        assert "new_max_ctl" not in result
