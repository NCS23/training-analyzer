"""Tests für 80/20 Intensitätsverteilungs-Validierung."""

from __future__ import annotations

from app.services.intensity_validation import (
    IntensityDistribution,
    PlanIntensityReport,
    validate_intensity_distribution,
    validate_plan_intensity,
)


class TestValidateIntensityDistribution:
    """Wöchentliche Intensitätsverteilung."""

    def test_perfect_8020(self) -> None:
        """4 easy + 1 tempo = 80/20 → valid."""
        dist = validate_intensity_distribution(["easy", "easy", "easy", "long_run", "tempo"])
        assert dist.is_valid is True
        assert dist.easy_pct == 80.0
        assert dist.hard_pct == 20.0
        assert dist.warning is None

    def test_all_easy(self) -> None:
        """Nur lockere Läufe → valid, >80%."""
        dist = validate_intensity_distribution(["easy", "easy", "easy", "long_run"])
        assert dist.is_valid is True
        assert dist.easy_pct == 100.0
        assert dist.hard_pct == 0.0

    def test_too_many_hard(self) -> None:
        """2 hard von 4 = 50% → invalid."""
        dist = validate_intensity_distribution(["easy", "tempo", "intervals", "long_run"])
        assert dist.is_valid is False
        assert dist.hard_pct == 50.0
        assert dist.warning is not None
        assert "zu hart" in dist.warning

    def test_moderate_counts_as_half(self) -> None:
        """Fartlek zählt 50/50."""
        dist = validate_intensity_distribution(["easy", "easy", "easy", "fartlek"])
        assert dist.easy_count == 3
        assert dist.moderate_count == 1
        assert dist.easy_pct == 87.5  # (3 + 0.5) / 4 * 100
        assert dist.hard_pct == 12.5

    def test_progression_is_moderate(self) -> None:
        """Progression zählt als moderat."""
        dist = validate_intensity_distribution(["easy", "easy", "progression", "long_run"])
        assert dist.moderate_count == 1
        assert dist.easy_pct == 87.5

    def test_borderline_acceptable(self) -> None:
        """Genau 75% easy → valid aber mit Warnung."""
        # 3 easy + 1 hard = 75/25
        dist = validate_intensity_distribution(["easy", "easy", "long_run", "tempo"])
        assert dist.is_valid is True
        assert dist.easy_pct == 75.0
        assert dist.warning is not None
        assert "akzeptabel" in dist.warning

    def test_empty_input(self) -> None:
        """Leere Liste → Standard-Werte."""
        dist = validate_intensity_distribution([])
        assert dist.total_running == 0
        assert dist.is_valid is True

    def test_counts_are_correct(self) -> None:
        dist = validate_intensity_distribution(
            ["easy", "recovery", "tempo", "intervals", "long_run", "fartlek"]
        )
        assert dist.easy_count == 3  # easy, recovery, long_run
        assert dist.moderate_count == 1  # fartlek
        assert dist.hard_count == 2  # tempo, intervals
        assert dist.total_running == 6

    def test_unknown_type_defaults_to_easy(self) -> None:
        """Unbekannter Typ wird als easy gezählt."""
        dist = validate_intensity_distribution(["easy", "unknown_type", "tempo"])
        assert dist.easy_count == 2  # easy + unknown
        assert dist.hard_count == 1

    def test_typical_base_phase(self) -> None:
        """Typische Base-Phase: 3 easy + 1 long_run → 100% easy."""
        dist = validate_intensity_distribution(["easy", "easy", "easy", "long_run"])
        assert dist.is_valid is True
        assert dist.easy_pct == 100.0

    def test_typical_build_phase(self) -> None:
        """Typische Build-Phase: easy + progression + fartlek + long_run → ~87.5%."""
        dist = validate_intensity_distribution(["easy", "progression", "fartlek", "long_run"])
        # 2 easy + 2 moderate → (2 + 1) / 4 = 75%
        assert dist.easy_pct == 75.0
        assert dist.is_valid is True

    def test_typical_peak_phase(self) -> None:
        """Typische Peak-Phase: easy + intervals + tempo + long_run → 50%."""
        dist = validate_intensity_distribution(["easy", "intervals", "tempo", "long_run"])
        assert dist.easy_pct == 50.0
        assert dist.is_valid is False


class TestValidatePlanIntensity:
    """Plan-Level Validierung."""

    def test_valid_plan(self) -> None:
        """Plan mit nur validen Wochen."""
        weeks = [
            ["easy", "easy", "easy", "long_run"],
            ["easy", "easy", "easy", "long_run", "tempo"],
        ]
        report = validate_plan_intensity(weeks)
        assert report.is_plan_valid is True
        assert len(report.violation_weeks) == 0

    def test_plan_with_violations(self) -> None:
        """Plan mit einer verletzten Woche."""
        weeks = [
            ["easy", "easy", "easy", "long_run"],  # OK
            ["easy", "tempo", "intervals", "long_run"],  # 50% hard → violation
        ]
        report = validate_plan_intensity(weeks)
        assert report.is_plan_valid is False
        assert 2 in report.violation_weeks  # Woche 2 (1-basiert)

    def test_overall_distribution(self) -> None:
        """Gesamtverteilung über alle Wochen."""
        weeks = [
            ["easy", "easy", "long_run"],
            ["easy", "easy", "tempo"],
        ]
        report = validate_plan_intensity(weeks)
        assert report.overall.total_running == 6

    def test_returns_pydantic_models(self) -> None:
        weeks = [["easy", "easy", "long_run"]]
        report = validate_plan_intensity(weeks)
        assert isinstance(report, PlanIntensityReport)
        assert isinstance(report.overall, IntensityDistribution)
        assert all(isinstance(w, IntensityDistribution) for w in report.weeks)

    def test_empty_plan(self) -> None:
        report = validate_plan_intensity([])
        assert report.is_plan_valid is True
        assert len(report.weeks) == 0
