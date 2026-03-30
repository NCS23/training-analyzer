"""Tests für Volumen-Kalibrierung aus Trainingshistorie."""

from __future__ import annotations

from app.services.deload_pattern import DeloadRatio
from app.services.volume_calibration import (
    WeeklyVolumeTarget,
    calibrate_weekly_volumes,
)


class TestCalibrateWeeklyVolumes:
    """Volumen-Kalibrierung für einen Plan."""

    def test_returns_correct_week_count(self) -> None:
        phases = [
            {"phase_type": "base", "weeks": 4},
            {"phase_type": "build", "weeks": 3},
            {"phase_type": "taper", "weeks": 2},
        ]
        targets = calibrate_weekly_volumes(phases, current_weekly_km=30.0)
        assert len(targets) == 9

    def test_week_numbers_sequential(self) -> None:
        phases = [{"phase_type": "base", "weeks": 6}]
        targets = calibrate_weekly_volumes(phases, current_weekly_km=30.0)
        assert [t.week_number for t in targets] == [1, 2, 3, 4, 5, 6]

    def test_overall_trend_increases(self) -> None:
        """Gesamttrend steigt (letzte Nicht-Deload-Woche > erste)."""
        phases = [
            {"phase_type": "base", "weeks": 5},
            {"phase_type": "build", "weeks": 4},
            {"phase_type": "peak", "weeks": 1},
        ]
        targets = calibrate_weekly_volumes(phases, current_weekly_km=25.0)
        non_deload = [t for t in targets if not t.is_deload]
        assert non_deload[-1].adjusted_volume_km > non_deload[0].adjusted_volume_km

    def test_deload_weeks_have_reduced_volume(self) -> None:
        """Deload-Wochen haben reduziertes Volumen."""
        phases = [{"phase_type": "base", "weeks": 8}]
        targets = calibrate_weekly_volumes(phases, current_weekly_km=30.0)
        deloads = [t for t in targets if t.is_deload]
        assert len(deloads) >= 1
        for d in deloads:
            assert d.adjusted_volume_km < d.base_volume_km

    def test_taper_weeks_decrease(self) -> None:
        """Taper-Wochen haben abnehmendes Volumen."""
        phases = [
            {"phase_type": "base", "weeks": 4},
            {"phase_type": "taper", "weeks": 3},
        ]
        targets = calibrate_weekly_volumes(phases, current_weekly_km=40.0)
        taper = [t for t in targets if t.is_taper]
        assert len(taper) == 3
        for i in range(1, len(taper)):
            assert taper[i].adjusted_volume_km <= taper[i - 1].adjusted_volume_km

    def test_minimum_volume_enforced(self) -> None:
        """Volumen fällt nie unter 10 km."""
        phases = [
            {"phase_type": "base", "weeks": 2},
            {"phase_type": "taper", "weeks": 2},
        ]
        targets = calibrate_weekly_volumes(phases, current_weekly_km=15.0)
        for t in targets:
            assert t.adjusted_volume_km >= 10.0

    def test_peak_capped_at_2x_start(self) -> None:
        """Peak-Volumen wird auf 2x Start gecappt."""
        phases = [{"phase_type": "base", "weeks": 20}]
        targets = calibrate_weekly_volumes(phases, current_weekly_km=20.0, peak_volume_km=100.0)
        # 100 km wird auf 2x20=40 km gecappt
        max_vol = max(t.adjusted_volume_km for t in targets)
        assert max_vol <= 40.0 * 1.01  # Kleine Rundungstoleranz

    def test_custom_peak_volume(self) -> None:
        """Benutzerdefiniertes Peak-Volumen wird respektiert."""
        phases = [
            {"phase_type": "base", "weeks": 4},
            {"phase_type": "peak", "weeks": 2},
        ]
        targets = calibrate_weekly_volumes(phases, current_weekly_km=30.0, peak_volume_km=45.0)
        # Peak sollte in Richtung 45 km gehen (nicht überschreiten)
        peak_weeks = [t for t in targets if t.phase == "peak"]
        for pw in peak_weeks:
            assert pw.base_volume_km <= 46.0  # Leichte Rundung ok


class TestTenPercentRule:
    """10%-Regel wird durchgesetzt."""

    def test_no_week_exceeds_10_percent(self) -> None:
        """Keine Woche steigt mehr als 10% gegenüber Vorwoche."""
        phases = [
            {"phase_type": "base", "weeks": 6},
            {"phase_type": "build", "weeks": 4},
            {"phase_type": "peak", "weeks": 2},
        ]
        targets = calibrate_weekly_volumes(phases, current_weekly_km=20.0)

        for i in range(1, len(targets)):
            curr = targets[i]
            prev = targets[i - 1]
            # Deload/Taper dürfen reduzieren
            if curr.is_deload or curr.is_taper:
                continue
            # Nach Deload darf es wieder hoch (auf Pre-Deload-Niveau)
            if prev.is_deload:
                continue
            max_allowed = prev.adjusted_volume_km * 1.10 + 0.2  # Rundungstoleranz
            assert curr.adjusted_volume_km <= max_allowed, (
                f"Woche {curr.week_number}: {curr.adjusted_volume_km} > 110% von "
                f"Woche {prev.week_number}: {prev.adjusted_volume_km}"
            )


class TestDeloadRatioIntegration:
    """Integration mit verschiedenen Deload-Ratios."""

    def test_21_has_more_deloads(self) -> None:
        phases = [{"phase_type": "base", "weeks": 12}]
        targets_21 = calibrate_weekly_volumes(
            phases, current_weekly_km=30.0, deload_ratio=DeloadRatio.RATIO_2_1
        )
        targets_31 = calibrate_weekly_volumes(
            phases, current_weekly_km=30.0, deload_ratio=DeloadRatio.RATIO_3_1
        )
        deloads_21 = sum(1 for t in targets_21 if t.is_deload)
        deloads_31 = sum(1 for t in targets_31 if t.is_deload)
        assert deloads_21 > deloads_31


class TestWeeklyVolumeTarget:
    """WeeklyVolumeTarget Datenklasse."""

    def test_all_fields_present(self) -> None:
        phases = [{"phase_type": "base", "weeks": 2}]
        targets = calibrate_weekly_volumes(phases, current_weekly_km=30.0)
        t = targets[0]
        assert isinstance(t, WeeklyVolumeTarget)
        assert t.week_number == 1
        assert t.phase == "base"
        assert t.base_volume_km > 0
        assert t.adjusted_volume_km > 0
        assert isinstance(t.is_deload, bool)
        assert isinstance(t.is_taper, bool)
