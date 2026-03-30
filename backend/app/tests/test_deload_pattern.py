"""Tests für Entlastungswochen und progressive Taper-Logik."""

from app.services.deload_pattern import (
    DeloadRatio,
    PhaseType,
    WeekVolumeFactor,
    compute_volume_factors,
    suggest_deload_ratio,
    suggest_taper_weeks,
)

# ---------------------------------------------------------------------------
# Deload-Muster (3:1)
# ---------------------------------------------------------------------------


class TestDeload31:
    """Deload-Muster 3:1 (3 Aufbau + 1 Entlastung)."""

    def test_4_week_base_has_deload_on_week_4(self) -> None:
        """4 Wochen Base → Deload auf Woche 4."""
        phases = [{"phase_type": "base", "weeks": 4}]
        factors = compute_volume_factors(phases, DeloadRatio.RATIO_3_1)
        assert len(factors) == 4
        assert factors[0].volume_factor == 1.0
        assert factors[1].volume_factor == 1.0
        assert factors[2].volume_factor == 1.0
        assert factors[3].is_deload is True
        assert factors[3].volume_factor == 0.75

    def test_8_week_base_has_two_deloads(self) -> None:
        """8 Wochen Base → Deloads auf Woche 4 und 8."""
        phases = [{"phase_type": "base", "weeks": 8}]
        factors = compute_volume_factors(phases, DeloadRatio.RATIO_3_1)
        deload_weeks = [f for f in factors if f.is_deload]
        assert len(deload_weeks) == 2
        assert deload_weeks[0].week_number == 4
        assert deload_weeks[1].week_number == 8

    def test_5_week_base_deload_on_week_4_only(self) -> None:
        """5 Wochen Base → Deload nur auf Woche 4 (Woche 5 ist kein Deload-Punkt)."""
        phases = [{"phase_type": "base", "weeks": 5}]
        factors = compute_volume_factors(phases, DeloadRatio.RATIO_3_1)
        deload_weeks = [f for f in factors if f.is_deload]
        assert len(deload_weeks) == 1
        assert deload_weeks[0].week_number == 4

    def test_3_week_phase_no_deload(self) -> None:
        """3 Wochen Phase → kein Deload (Zyklus nicht komplett)."""
        phases = [{"phase_type": "build", "weeks": 3}]
        factors = compute_volume_factors(phases, DeloadRatio.RATIO_3_1)
        deload_weeks = [f for f in factors if f.is_deload]
        assert len(deload_weeks) == 0


# ---------------------------------------------------------------------------
# Deload-Muster (2:1)
# ---------------------------------------------------------------------------


class TestDeload21:
    """Deload-Muster 2:1 (2 Aufbau + 1 Entlastung) für Anfänger."""

    def test_3_week_base_has_deload_on_week_3(self) -> None:
        """3 Wochen Base → Deload auf Woche 3."""
        phases = [{"phase_type": "base", "weeks": 3}]
        factors = compute_volume_factors(phases, DeloadRatio.RATIO_2_1)
        assert factors[0].volume_factor == 1.0
        assert factors[1].volume_factor == 1.0
        assert factors[2].is_deload is True
        assert factors[2].volume_factor == 0.75

    def test_6_week_base_has_two_deloads(self) -> None:
        """6 Wochen Base → Deloads auf Woche 3 und 6."""
        phases = [{"phase_type": "base", "weeks": 6}]
        factors = compute_volume_factors(phases, DeloadRatio.RATIO_2_1)
        deload_weeks = [f for f in factors if f.is_deload]
        assert len(deload_weeks) == 2
        assert deload_weeks[0].week_number == 3
        assert deload_weeks[1].week_number == 6

    def test_more_deloads_than_31(self) -> None:
        """2:1 hat mehr Deload-Wochen als 3:1 bei gleicher Phasenlänge."""
        phases = [{"phase_type": "base", "weeks": 12}]
        deloads_21 = len(
            [f for f in compute_volume_factors(phases, DeloadRatio.RATIO_2_1) if f.is_deload]
        )
        deloads_31 = len(
            [f for f in compute_volume_factors(phases, DeloadRatio.RATIO_3_1) if f.is_deload]
        )
        assert deloads_21 > deloads_31


# ---------------------------------------------------------------------------
# No-Deload-Before-Taper Regel
# ---------------------------------------------------------------------------


class TestNoDeloadBeforeTaper:
    """Keine Deload-Woche direkt vor Taper-Phase."""

    def test_skip_deload_before_taper(self) -> None:
        """Wenn letzte Woche einer Phase vor Taper ein Deload wäre → überspringen."""
        phases = [
            {"phase_type": "build", "weeks": 4},  # Woche 4 wäre Deload
            {"phase_type": "taper", "weeks": 2},
        ]
        factors = compute_volume_factors(phases, DeloadRatio.RATIO_3_1)
        # Woche 4 (letzte Build-Woche vor Taper) darf KEIN Deload sein
        week_4 = factors[3]
        assert week_4.is_deload is False
        assert week_4.volume_factor == 1.0

    def test_deload_ok_when_not_before_taper(self) -> None:
        """Deload ist ok wenn nach der Phase noch kein Taper kommt."""
        phases = [
            {"phase_type": "base", "weeks": 4},  # Woche 4 = Deload
            {"phase_type": "build", "weeks": 4},
        ]
        factors = compute_volume_factors(phases, DeloadRatio.RATIO_3_1)
        week_4 = factors[3]
        assert week_4.is_deload is True


# ---------------------------------------------------------------------------
# Progressive Taper
# ---------------------------------------------------------------------------


class TestProgressiveTaper:
    """Progressive Taper-Phase (stufenweise Reduktion)."""

    def test_2_week_taper(self) -> None:
        """2-Wochen Taper: 70% → 45%."""
        phases = [{"phase_type": "taper", "weeks": 2}]
        factors = compute_volume_factors(phases)
        assert factors[0].volume_factor == 0.70
        assert factors[1].volume_factor == 0.45
        assert all(f.is_taper for f in factors)

    def test_3_week_taper(self) -> None:
        """3-Wochen Taper: 75% → 60% → 40%."""
        phases = [{"phase_type": "taper", "weeks": 3}]
        factors = compute_volume_factors(phases)
        assert factors[0].volume_factor == 0.75
        assert factors[1].volume_factor == 0.60
        assert factors[2].volume_factor == 0.40

    def test_1_week_taper(self) -> None:
        """1-Woche Taper: 50%."""
        phases = [{"phase_type": "taper", "weeks": 1}]
        factors = compute_volume_factors(phases)
        assert factors[0].volume_factor == 0.50

    def test_taper_is_always_decreasing(self) -> None:
        """Taper-Faktoren sind strikt abnehmend."""
        for taper_weeks in [2, 3, 4]:
            phases = [{"phase_type": "taper", "weeks": taper_weeks}]
            factors = compute_volume_factors(phases)
            volumes = [f.volume_factor for f in factors]
            for i in range(1, len(volumes)):
                assert volumes[i] < volumes[i - 1], (
                    f"Taper {taper_weeks}W: Woche {i + 1} ({volumes[i]}) "
                    f"nicht kleiner als Woche {i} ({volumes[i - 1]})"
                )

    def test_taper_not_marked_as_deload(self) -> None:
        """Taper-Wochen sind kein Deload (eigene Logik)."""
        phases = [{"phase_type": "taper", "weeks": 3}]
        factors = compute_volume_factors(phases)
        assert all(not f.is_deload for f in factors)
        assert all(f.is_taper for f in factors)


# ---------------------------------------------------------------------------
# Recovery/Transition
# ---------------------------------------------------------------------------


class TestRecoveryTransition:
    """Recovery- und Transition-Phasen."""

    def test_recovery_constant_factor(self) -> None:
        """Recovery-Phase hat konstant reduzierten Faktor."""
        phases = [{"phase_type": "recovery", "weeks": 2}]
        factors = compute_volume_factors(phases)
        assert all(f.volume_factor == 0.70 for f in factors)

    def test_transition_constant_factor(self) -> None:
        """Transition-Phase hat gleichen Faktor wie Recovery."""
        phases = [{"phase_type": "transition", "weeks": 3}]
        factors = compute_volume_factors(phases)
        assert all(f.volume_factor == 0.70 for f in factors)

    def test_recovery_no_deloads(self) -> None:
        """Recovery braucht keine extra Deloads."""
        phases = [{"phase_type": "recovery", "weeks": 6}]
        factors = compute_volume_factors(phases)
        assert all(not f.is_deload for f in factors)


# ---------------------------------------------------------------------------
# Kompletter Plan (Multi-Phase)
# ---------------------------------------------------------------------------


class TestCompletePlan:
    """Komplett-Plan mit mehreren Phasen."""

    def test_12_week_hm_plan(self) -> None:
        """Typischer 12-Wochen HM-Plan: Base(5) + Build(4) + Peak(1) + Taper(2)."""
        phases = [
            {"phase_type": "base", "weeks": 5},
            {"phase_type": "build", "weeks": 4},
            {"phase_type": "peak", "weeks": 1},
            {"phase_type": "taper", "weeks": 2},
        ]
        factors = compute_volume_factors(phases, DeloadRatio.RATIO_3_1)
        assert len(factors) == 12

        # Deloads in Base (Woche 4)
        assert factors[3].is_deload is True

        # Build Woche 4 (= Woche 9 global, letzte vor Peak, nicht Taper) → Deload
        assert factors[8].is_deload is True

        # Taper (Wochen 11-12)
        assert factors[10].is_taper is True
        assert factors[11].is_taper is True
        assert factors[10].volume_factor > factors[11].volume_factor

    def test_total_weeks_matches(self) -> None:
        """Gesamtwochen = Summe aller Phasen-Wochen."""
        phases = [
            {"phase_type": "base", "weeks": 6},
            {"phase_type": "build", "weeks": 3},
            {"phase_type": "taper", "weeks": 2},
        ]
        factors = compute_volume_factors(phases)
        assert len(factors) == 11

    def test_week_numbers_are_sequential(self) -> None:
        """Wochennummern sind sequentiell (1, 2, 3, ...)."""
        phases = [
            {"phase_type": "base", "weeks": 4},
            {"phase_type": "build", "weeks": 3},
            {"phase_type": "taper", "weeks": 2},
        ]
        factors = compute_volume_factors(phases)
        week_numbers = [f.week_number for f in factors]
        assert week_numbers == list(range(1, 10))

    def test_phase_types_are_correct(self) -> None:
        """Phasen-Typ wird korrekt zugewiesen."""
        phases = [
            {"phase_type": "base", "weeks": 2},
            {"phase_type": "build", "weeks": 2},
            {"phase_type": "taper", "weeks": 1},
        ]
        factors = compute_volume_factors(phases)
        assert factors[0].phase == PhaseType.BASE
        assert factors[1].phase == PhaseType.BASE
        assert factors[2].phase == PhaseType.BUILD
        assert factors[3].phase == PhaseType.BUILD
        assert factors[4].phase == PhaseType.TAPER

    def test_returns_pydantic_models(self) -> None:
        """Ergebnis sind WeekVolumeFactor Pydantic-Models."""
        phases = [{"phase_type": "base", "weeks": 2}]
        factors = compute_volume_factors(phases)
        assert all(isinstance(f, WeekVolumeFactor) for f in factors)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


class TestSuggestDeloadRatio:
    """Empfehlung für Deload-Verhältnis."""

    def test_beginner_gets_21(self) -> None:
        """Anfänger (<20 km/Woche) → 2:1."""
        assert suggest_deload_ratio(15.0, 20) == DeloadRatio.RATIO_2_1

    def test_low_experience_gets_21(self) -> None:
        """Wenig Trainingserfahrung (<12 Wochen) → 2:1."""
        assert suggest_deload_ratio(40.0, 8) == DeloadRatio.RATIO_2_1

    def test_experienced_gets_31(self) -> None:
        """Erfahren (≥20 km/Woche + ≥12 Wochen) → 3:1."""
        assert suggest_deload_ratio(40.0, 20) == DeloadRatio.RATIO_3_1


class TestSuggestTaperWeeks:
    """Empfehlung für Taper-Länge."""

    def test_marathon_3_weeks(self) -> None:
        assert suggest_taper_weeks(42.195) == 3

    def test_half_marathon_2_weeks(self) -> None:
        assert suggest_taper_weeks(21.0975) == 2

    def test_10k_2_weeks(self) -> None:
        assert suggest_taper_weeks(10.0) == 2

    def test_5k_1_week(self) -> None:
        assert suggest_taper_weeks(5.0) == 1
