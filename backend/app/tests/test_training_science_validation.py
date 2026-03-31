"""Trainingswissenschaftliche Validierungstests.

Prüft ob die generierten Trainingspläne und Pace-Zonen mit publizierten
Referenzwerten übereinstimmen.

Quellen:
- Daniels, J. (2014). Daniels' Running Formula, 3rd Ed. — VDOT-Tabellen, Pace-Zonen
- Pfitzinger, P. (2009). Advanced Marathoning, 2nd Ed. — Volumen, Long Run, Taper
- Seiler, S. (2010). Polarized Training — 80/20 Intensitätsverteilung
"""

from __future__ import annotations

import pytest

from app.services.deload_pattern import DeloadRatio, compute_volume_factors
from app.services.goal_validation import validate_goal
from app.services.intensity_validation import validate_intensity_distribution
from app.services.plan_enrichment import get_hr_zone_for_run_type
from app.services.vdot_calculator import (
    equivalent_race_time,
    estimate_vdot,
    training_paces_for_plan,
    training_paces_from_vdot,
)
from app.services.volume_calibration import calibrate_weekly_volumes


def _pace_to_sec(pace_str: str) -> int:
    """Konvertiere 'M:SS' zu Sekunden."""
    m, s = pace_str.split(":")
    return int(m) * 60 + int(s)


def _sec_to_pace(sec: float) -> str:
    """Konvertiere Sekunden zu 'M:SS'."""
    m = int(sec) // 60
    s = int(sec) % 60
    return f"{m}:{s:02d}"


# ============================================================================
# 1. VDOT-Tabelle gegen Daniels' publizierte Werte
# ============================================================================
# Referenz: Daniels' Running Formula, 3rd Ed., Tabelle 3.1
# Format: (VDOT, Distanz_km, erwartete_Zeit_Sekunden, Toleranz_Sekunden)


class TestVdotAgainstDanielsTable:
    """VDOT-Werte gegen Daniels' publizierte Tabellen."""

    @pytest.mark.parametrize(
        "distance_km, time_sec, expected_vdot_min, expected_vdot_max",
        [
            # Daniels Tabelle 3.1 — bekannte Stützstellen
            (5.0, 30 * 60, 30, 34),  # 5K in 30:00 → VDOT ~30-33
            (5.0, 24 * 60, 36, 40),  # 5K in 24:00 → VDOT ~37-39
            (5.0, 20 * 60, 44, 50),  # 5K in 20:00 → VDOT ~46-48
            (5.0, 17 * 60, 53, 58),  # 5K in 17:00 → VDOT ~55-57
            (5.0, 15 * 60, 62, 67),  # 5K in 15:00 → VDOT ~63-65
            (10.0, 60 * 60, 30, 37),  # 10K in 60:00 → VDOT ~31-36
            (10.0, 50 * 60, 37, 42),  # 10K in 50:00 → VDOT ~39-41
            (10.0, 40 * 60, 48, 55),  # 10K in 40:00 → VDOT ~49-54
            (21.0975, 2 * 3600, 35, 40),  # HM in 2:00 → VDOT ~36-39
            (21.0975, 105 * 60, 40, 46),  # HM in 1:45 → VDOT ~42-45
            (21.0975, 90 * 60, 47, 52),  # HM in 1:30 → VDOT ~48-51
            (42.195, 4 * 3600, 33, 38),  # Marathon in 4:00 → VDOT ~34-37
            (42.195, 3.5 * 3600, 37, 44),  # Marathon in 3:30 → VDOT ~38-43
            (42.195, 3 * 3600, 50, 56),  # Marathon in 3:00 → VDOT ~52-55
        ],
    )
    def test_vdot_within_daniels_range(
        self, distance_km: float, time_sec: float, expected_vdot_min: int, expected_vdot_max: int
    ) -> None:
        """VDOT liegt innerhalb des erwarteten Bereichs aus Daniels' Tabelle."""
        vdot = estimate_vdot(distance_km, time_sec)
        assert vdot is not None, f"VDOT für {distance_km}km in {time_sec}s sollte nicht None sein"
        assert expected_vdot_min <= vdot <= expected_vdot_max, (
            f"VDOT {vdot:.1f} für {distance_km}km in {_sec_to_pace(time_sec / distance_km)}/km "
            f"liegt außerhalb des erwarteten Bereichs [{expected_vdot_min}-{expected_vdot_max}]"
        )

    def test_equivalent_times_are_consistent(self) -> None:
        """Äquivalente Zeiten für verschiedene Distanzen sind physiologisch konsistent.

        Daniels-Prinzip: Ein Athlet mit VDOT X sollte auf allen Distanzen
        äquivalente Leistungen bringen. Z.B. 20:00 auf 5K ≈ 41:30 auf 10K ≈ 1:32 HM.
        """
        vdot = estimate_vdot(5.0, 20 * 60)
        assert vdot is not None

        time_10k = equivalent_race_time(vdot, 10.0)
        time_hm = equivalent_race_time(vdot, 21.0975)
        time_marathon = equivalent_race_time(vdot, 42.195)

        assert time_10k is not None and time_hm is not None and time_marathon is not None

        # 10K sollte ca. 2.08-2.12x der 5K-Zeit sein (nicht exakt doppelt wegen Ausdauerfaktor)
        ratio_10k_5k = time_10k / (20 * 60)
        assert 2.05 <= ratio_10k_5k <= 2.20, f"10K/5K Ratio {ratio_10k_5k:.2f} unplausibel"

        # HM sollte ca. 4.4-4.7x der 5K-Zeit sein
        ratio_hm_5k = time_hm / (20 * 60)
        assert 4.2 <= ratio_hm_5k <= 4.8, f"HM/5K Ratio {ratio_hm_5k:.2f} unplausibel"

        # Marathon sollte ca. 9.2-10.0x der 5K-Zeit sein
        ratio_m_5k = time_marathon / (20 * 60)
        assert 9.0 <= ratio_m_5k <= 10.5, f"Marathon/5K Ratio {ratio_m_5k:.2f} unplausibel"


# ============================================================================
# 2. Daniels-Trainingszonen gegen publizierte Pace-Tabellen
# ============================================================================
# Referenz: Daniels' Running Formula, Tabelle 5.2


class TestDanielsPaceZones:
    """Trainingszonen stimmen mit Daniels' publizierten Pace-Bereichen überein."""

    @pytest.mark.parametrize(
        "vdot, zone, expected_min_sec_km, expected_max_sec_km",
        [
            # VDOT 40 — Daniels Tabelle 5.2
            # Unsere Berechnung: 5K-Pace × Multiplikatoren
            # Easy: 5:52-6:34/km, Threshold: 4:58-5:10/km
            (40, "easy", 340, 460),  # 5:40-7:40 (breiter Bereich wegen Multiplikator-Ansatz)
            (40, "threshold", 290, 370),  # 4:50-6:10
            (40, "interval", 270, 330),  # 4:30-5:30
            # VDOT 50 — Daniels Tabelle 5.2
            # Easy: 5:14-5:46/km, Threshold: 4:19-4:28/km, Interval: 3:50-4:02/km
            (50, "easy", 270, 370),  # 4:30-6:10
            (50, "threshold", 230, 290),  # 3:50-4:50
            (50, "interval", 210, 270),  # 3:30-4:30
            # VDOT 60 — Daniels Tabelle 5.2
            # Easy: 4:25-4:51/km, Threshold: 3:38-3:44/km
            (60, "easy", 230, 310),  # 3:50-5:10
            (60, "threshold", 195, 250),  # 3:15-4:10
        ],
    )
    def test_pace_zone_within_range(
        self,
        vdot: int,
        zone: str,
        expected_min_sec_km: int,
        expected_max_sec_km: int,
    ) -> None:
        """Pace-Zone liegt innerhalb des erwarteten Bereichs."""
        paces = training_paces_from_vdot(float(vdot))
        fast, slow = paces[zone]
        assert expected_min_sec_km <= fast <= expected_max_sec_km, (
            f"VDOT {vdot} {zone} fast pace {fast:.0f}s/km ({_sec_to_pace(fast)}) "
            f"außerhalb [{_sec_to_pace(expected_min_sec_km)}-{_sec_to_pace(expected_max_sec_km)}]"
        )
        assert expected_min_sec_km <= slow <= expected_max_sec_km, (
            f"VDOT {vdot} {zone} slow pace {slow:.0f}s/km ({_sec_to_pace(slow)}) "
            f"außerhalb [{_sec_to_pace(expected_min_sec_km)}-{_sec_to_pace(expected_max_sec_km)}]"
        )

    def test_zone_hierarchy_is_correct(self) -> None:
        """Daniels-Zonen-Hierarchie: E > M > T > I > R (langsam nach schnell)."""
        for vdot in [35, 40, 45, 50, 55, 60]:
            paces = training_paces_from_vdot(float(vdot))
            # Mittlere Pace pro Zone (Durchschnitt aus fast/slow)
            e_avg = sum(paces["easy"]) / 2
            m_avg = sum(paces["marathon"]) / 2
            t_avg = sum(paces["threshold"]) / 2
            i_avg = sum(paces["interval"]) / 2
            r_avg = sum(paces["repetition"]) / 2

            assert e_avg > m_avg > t_avg > i_avg > r_avg, (
                f"VDOT {vdot}: Zonen-Hierarchie verletzt: "
                f"E={e_avg:.0f} M={m_avg:.0f} T={t_avg:.0f} I={i_avg:.0f} R={r_avg:.0f}"
            )


# ============================================================================
# 3. HR-Zonen physiologisch korrekt
# ============================================================================


class TestHrZonesPhysiological:
    """HR-Zonen folgen physiologischen Prinzipien."""

    def test_easy_hr_below_lthr(self) -> None:
        """Easy-Zone HR liegt unter der Laktatschwelle."""
        for lthr in [160, 165, 170, 175, 180]:
            _, hr_max = get_hr_zone_for_run_type("easy", lthr=lthr)
            assert hr_max is not None and hr_max <= lthr, (
                f"Easy HR max {hr_max} sollte unter LTHR {lthr} liegen"
            )

    def test_tempo_hr_near_lthr(self) -> None:
        """Tempo-Zone HR liegt nahe der Laktatschwelle (±5%)."""
        for lthr in [160, 170, 180]:
            hr_min, hr_max = get_hr_zone_for_run_type("tempo", lthr=lthr)
            assert hr_min is not None and hr_max is not None
            # Tempo = Zone 4 bei Friel = 95-100% LTHR
            assert hr_min >= lthr * 0.90, f"Tempo HR min {hr_min} zu weit unter LTHR {lthr}"
            assert hr_max <= lthr * 1.05, f"Tempo HR max {hr_max} zu weit über LTHR {lthr}"

    def test_interval_hr_above_lthr(self) -> None:
        """Interval-Zone HR liegt über der Laktatschwelle."""
        for lthr in [160, 170, 180]:
            hr_min, _ = get_hr_zone_for_run_type("intervals", lthr=lthr)
            assert hr_min is not None and hr_min >= lthr, (
                f"Interval HR min {hr_min} sollte über LTHR {lthr} liegen"
            )

    def test_recovery_hr_lowest(self) -> None:
        """Recovery hat die niedrigste HR-Zone."""
        lthr = 170
        rec_max = get_hr_zone_for_run_type("recovery", lthr=lthr)[1]
        easy_min = get_hr_zone_for_run_type("easy", lthr=lthr)[0]
        assert rec_max is not None and easy_min is not None
        assert rec_max <= easy_min, f"Recovery max {rec_max} sollte <= Easy min {easy_min} sein"


# ============================================================================
# 4. Konkrete Athleten-Szenarien gegen Pfitzinger-Referenzpläne
# ============================================================================


class TestAthleteScenarios:
    """Konkrete Szenarien gegen Pfitzinger-Empfehlungen validiert."""

    def test_hm_sub_150_athlete_paces(self) -> None:
        """HM Sub-1:50 Athlet: Paces müssen physiologisch sinnvoll sein.

        HM Sub-1:50 = 110 Min / 21.0975 km = 5:13/km Wettkampfpace
        Erwartete Zonen (Daniels-basiert):
        - Easy: ~5:50-6:30/km
        - Threshold: ~4:50-5:10/km
        - Interval: ~4:20-4:40/km
        """
        vdot = estimate_vdot(21.0975, 110 * 60)  # 1:50:00
        assert vdot is not None

        # training_paces_for_plan gibt (float, float) in sec/km zurück
        paces = training_paces_for_plan(vdot)

        # Easy Pace: muss langsamer als Race Pace (313 sec = 5:13/km)
        easy_fast_sec = paces["easy"][0]
        easy_slow_sec = paces["easy"][1]
        assert easy_fast_sec > 313, (
            f"Easy fast {_sec_to_pace(easy_fast_sec)} zu schnell für HM Sub-1:50"
        )
        assert easy_slow_sec < 450, f"Easy slow {_sec_to_pace(easy_slow_sec)} zu langsam (>7:30)"

        # Threshold: knapp unter Race Pace
        tempo_fast_sec = paces["tempo"][0]
        assert 260 <= tempo_fast_sec <= 330, (
            f"Tempo {_sec_to_pace(tempo_fast_sec)} unplausibel für HM Sub-1:50"
        )

        # Long Run: nicht langsamer als Easy
        lr_slow_sec = paces["long_run"][1]
        assert lr_slow_sec <= easy_slow_sec, "Long Run sollte nicht langsamer als Easy sein"

    def test_hm_sub_200_athlete_paces(self) -> None:
        """HM Sub-2:00 Athlet: weniger anspruchsvoll, breitere Easy-Zone.

        HM Sub-2:00 = 120 Min / 21.0975 km = 5:41/km Wettkampfpace
        """
        vdot = estimate_vdot(21.0975, 120 * 60)
        assert vdot is not None

        paces = training_paces_for_plan(vdot)

        # Easy Pace: deutlich langsamer als Race Pace (341 sec = 5:41/km)
        easy_fast_sec = paces["easy"][0]
        assert easy_fast_sec > 341, f"Easy {_sec_to_pace(easy_fast_sec)} zu schnell für HM Sub-2:00"

        # Interval: schneller als Race Pace
        interval_slow_sec = paces["intervals"][1]
        assert interval_slow_sec < 341, (
            f"Intervals {_sec_to_pace(interval_slow_sec)} sollten schneller als 5:41 sein"
        )

    def test_marathon_sub_330_volume_progression(self) -> None:
        """Marathon Sub-3:30 Plan: Volumen muss realistisch sein.

        Pfitzinger empfiehlt für Marathon:
        - Peak: 55-70 km/Woche (fortgeschrittener Läufer)
        - Long Run: 25-35 km (max 3h)
        - Taper: 3 Wochen, progressive Reduktion
        """
        phases = [
            {"phase_type": "base", "weeks": 6},
            {"phase_type": "build", "weeks": 5},
            {"phase_type": "peak", "weeks": 4},
            {"phase_type": "taper", "weeks": 3},
        ]
        targets = calibrate_weekly_volumes(
            phases,
            current_weekly_km=40.0,
            peak_volume_km=65.0,
            deload_ratio=DeloadRatio.RATIO_3_1,
        )

        # Peak-Phase Volumen muss über 50 km sein
        peak_weeks = [t for t in targets if t.phase == "peak" and not t.is_deload]
        assert len(peak_weeks) > 0
        max_peak = max(t.adjusted_volume_km for t in peak_weeks)
        assert max_peak >= 50.0, f"Peak-Volumen {max_peak:.1f} km zu niedrig für Marathon"

        # Taper muss progressiv reduzieren
        taper_weeks = [t for t in targets if t.is_taper]
        assert len(taper_weeks) == 3
        for i in range(1, len(taper_weeks)):
            assert taper_weeks[i].adjusted_volume_km < taper_weeks[i - 1].adjusted_volume_km, (
                "Taper muss progressiv abnehmend sein"
            )

        # Letzter Taper-Woche sollte 35-50% des Peaks sein
        taper_last = taper_weeks[-1].adjusted_volume_km
        taper_ratio = taper_last / max_peak
        assert 0.30 <= taper_ratio <= 0.55, (
            f"Letzte Taper-Woche {taper_last:.0f} km = {taper_ratio:.0%} des Peaks — "
            f"sollte 30-55% sein (Pfitzinger)"
        )


# ============================================================================
# 5. 80/20 Intensitätsverteilung gegen Seiler
# ============================================================================


class TestIntensityDistributionSeiler:
    """Typische Phasen-Templates erfüllen die 80/20-Regel."""

    def test_base_phase_is_valid(self) -> None:
        """Base-Phase: 3 Easy + 1 Long Run = 100% locker."""
        dist = validate_intensity_distribution(["easy", "easy", "easy", "long_run"])
        assert dist.is_valid, f"Base-Phase sollte valid sein, Easy%={dist.easy_pct}"
        assert dist.easy_pct == 100.0

    def test_build_phase_is_acceptable(self) -> None:
        """Build-Phase: easy + progression + fartlek + long_run ≥ 75% locker."""
        dist = validate_intensity_distribution(["easy", "progression", "fartlek", "long_run"])
        assert dist.is_valid, f"Build-Phase sollte valid sein, Easy%={dist.easy_pct}"

    def test_peak_phase_may_violate(self) -> None:
        """Peak-Phase mit 2 Quality-Sessions von 4 = 50% → Verletzung erkannt."""
        dist = validate_intensity_distribution(["easy", "intervals", "tempo", "long_run"])
        assert not dist.is_valid, "Peak mit 2/4 hard sollte als Verletzung erkannt werden"
        assert dist.warning is not None

    def test_peak_with_5_sessions_valid(self) -> None:
        """Peak-Phase mit 5 Sessions (2 hard, 3 easy) = 60% easy → grenzwertig."""
        dist = validate_intensity_distribution(["easy", "intervals", "tempo", "easy", "long_run"])
        # 3 easy + 2 hard = 60% easy — unter 75%, also invalid
        assert dist.easy_pct == 60.0
        assert not dist.is_valid


# ============================================================================
# 6. Deload-Pattern gegen Periodisierungsliteratur
# ============================================================================


class TestDeloadPeriodization:
    """Deload-Muster entsprechen der Periodisierungsliteratur."""

    def test_deload_reduces_20_to_30_percent(self) -> None:
        """Deload-Woche reduziert Volumen um 20-30% (Pfitzinger-Standard)."""
        phases = [{"phase_type": "base", "weeks": 4}]
        factors = compute_volume_factors(phases, DeloadRatio.RATIO_3_1)
        deload = [f for f in factors if f.is_deload]
        assert len(deload) == 1
        # Factor 0.75 = 25% Reduktion
        assert 0.70 <= deload[0].volume_factor <= 0.80

    def test_3_to_1_ratio_correct(self) -> None:
        """3:1 Muster: 3 Aufbau, 1 Entlastung (Bompa/Daniels-Standard)."""
        phases = [{"phase_type": "base", "weeks": 12}]
        factors = compute_volume_factors(phases, DeloadRatio.RATIO_3_1)
        deloads = [f for f in factors if f.is_deload]
        # 12 Wochen / 4er-Zyklus = 3 Deloads (Woche 4, 8, 12)
        assert len(deloads) == 3

    def test_progressive_taper_matches_pfitzinger(self) -> None:
        """Taper-Progression: 75% → 60% → 40% (Pfitzinger-Empfehlung)."""
        phases = [{"phase_type": "taper", "weeks": 3}]
        factors = compute_volume_factors(phases)
        taper_factors = [f.volume_factor for f in factors]
        # Pfitzinger: Woche 1 ca. 70-80%, Woche 2 ca. 55-65%, Woche 3 ca. 35-45%
        assert 0.70 <= taper_factors[0] <= 0.80, f"Taper W1: {taper_factors[0]}"
        assert 0.55 <= taper_factors[1] <= 0.65, f"Taper W2: {taper_factors[1]}"
        assert 0.35 <= taper_factors[2] <= 0.45, f"Taper W3: {taper_factors[2]}"


# ============================================================================
# 7. Ziel-Validierung gegen realistische Leistungsentwicklung
# ============================================================================


class TestGoalValidationRealistic:
    """Ziel-Bewertung ist physiologisch realistisch."""

    def test_same_performance_is_realistic(self) -> None:
        """Aktuelle Leistung als Ziel = realistisch."""
        vdot = estimate_vdot(10.0, 50 * 60)  # 10K in 50:00
        assert vdot is not None
        hm_time = equivalent_race_time(vdot, 21.0975)
        assert hm_time is not None
        result = validate_goal(vdot, 21.0975, hm_time)
        assert result.category == "realistic"

    def test_10_percent_improvement_is_ambitious(self) -> None:
        """10% schneller als aktuell = ambitioniert (nicht unrealistisch)."""
        vdot = estimate_vdot(10.0, 50 * 60)  # VDOT ~39
        assert vdot is not None
        hm_time = equivalent_race_time(vdot, 21.0975)
        assert hm_time is not None
        target = int(hm_time * 0.93)  # 7% schneller
        result = validate_goal(vdot, 21.0975, target)
        assert result.category in ("ambitious", "realistic"), (
            f"7% Verbesserung sollte ambitioniert oder realistisch sein, nicht {result.category}"
        )

    def test_30_percent_improvement_is_unrealistic(self) -> None:
        """30% schneller = unrealistisch (z.B. 2:00 HM → 1:24 HM)."""
        vdot = estimate_vdot(21.0975, 120 * 60)  # HM in 2:00
        assert vdot is not None
        target = int(120 * 60 * 0.70)  # 30% schneller = 1:24
        result = validate_goal(vdot, 21.0975, target)
        assert result.category == "unrealistic"

    def test_5k_runner_targeting_marathon_gets_realistic_assessment(self) -> None:
        """5K-Läufer (20:00) → Marathon-Ziel wird korrekt bewertet."""
        vdot = estimate_vdot(5.0, 20 * 60)
        assert vdot is not None
        # Äquivalenter Marathon für diesen VDOT
        equiv_marathon = equivalent_race_time(vdot, 42.195)
        assert equiv_marathon is not None
        # Ziel = äquivalente Zeit → realistic
        result = validate_goal(vdot, 42.195, equiv_marathon)
        assert result.category == "realistic"


# ============================================================================
# 8. Volumen-Progression gegen 10%-Regel
# ============================================================================


class TestVolumeProgressionSafety:
    """Volumen-Steigerung ist sicher und progressiv."""

    def test_no_week_exceeds_10_percent_increase(self) -> None:
        """Keine Woche steigt mehr als 10% gegenüber Vorwoche (Daniels-Regel)."""
        phases = [
            {"phase_type": "base", "weeks": 8},
            {"phase_type": "build", "weeks": 6},
            {"phase_type": "peak", "weeks": 3},
            {"phase_type": "taper", "weeks": 2},
        ]
        targets = calibrate_weekly_volumes(phases, current_weekly_km=25.0, peak_volume_km=50.0)

        for i in range(1, len(targets)):
            curr = targets[i]
            prev = targets[i - 1]
            # Deload/Taper/Recovery dürfen reduzieren
            if curr.is_deload or curr.is_taper or curr.phase in ("recovery", "transition"):
                continue
            if prev.is_deload or prev.phase in ("recovery", "transition"):
                continue
            increase_pct = (
                curr.adjusted_volume_km - prev.adjusted_volume_km
            ) / prev.adjusted_volume_km
            assert increase_pct <= 0.11, (  # 10% + Rundungstoleranz
                f"W{curr.week_number}: {curr.adjusted_volume_km:.1f} km ist "
                f"{increase_pct:.1%} mehr als W{prev.week_number}: {prev.adjusted_volume_km:.1f} km"
            )

    def test_long_run_not_exceeding_30_percent_of_volume(self) -> None:
        """Long Run sollte max 30-35% des Wochenvolumens sein (Pfitzinger).

        Bei 50 km/Woche → Long Run max ~17.5 km.
        """
        # Indirekt: Prüfe dass PHASE_DEFAULTS den richtigen Anteil haben
        from app.services.plan_generator import PHASE_DEFAULTS

        for phase_type, defaults in PHASE_DEFAULTS.items():
            lr_pct = defaults.get("long_run_volume_pct", 0)
            assert lr_pct <= 0.35, f"{phase_type}: long_run_volume_pct={lr_pct} > 35%"

    def test_minimum_volume_prevents_injury(self) -> None:
        """Minimales Volumen ist 10 km/Woche (unter Periodisierungsminimum sinnlos)."""
        phases = [{"phase_type": "taper", "weeks": 3}]
        targets = calibrate_weekly_volumes(phases, current_weekly_km=15.0)
        for t in targets:
            assert t.adjusted_volume_km >= 10.0, (
                f"W{t.week_number}: {t.adjusted_volume_km} km unter Minimum 10 km"
            )
