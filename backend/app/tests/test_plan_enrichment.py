"""Tests für Plan-Enrichment (VDOT-Paces + HR-Zonen)."""

from __future__ import annotations

from app.services.plan_enrichment import (
    enrich_run_details_params,
    get_hr_zone_for_run_type,
    get_pace_for_run_type,
    get_vdot_paces,
)

# ---------------------------------------------------------------------------
# VDOT-basierte Paces
# ---------------------------------------------------------------------------


class TestGetVdotPaces:
    """VDOT zu formatierten Pace-Strings."""

    def test_returns_all_run_types(self) -> None:
        paces = get_vdot_paces(50.0)
        expected = {
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
        assert set(paces.keys()) == expected

    def test_format_is_m_ss(self) -> None:
        """Alle Paces sind im 'M:SS' Format."""
        paces = get_vdot_paces(50.0)
        for run_type, (fast, slow) in paces.items():
            assert ":" in fast, f"{run_type} fast: {fast}"
            assert ":" in slow, f"{run_type} slow: {slow}"

    def test_higher_vdot_faster_paces(self) -> None:
        """Höherer VDOT = niedrigere Pace-Zahlen (schneller)."""
        paces_40 = get_vdot_paces(40.0)
        paces_60 = get_vdot_paces(60.0)
        # Easy pace: VDOT 60 sollte schneller sein als VDOT 40
        fast_40 = paces_40["easy"][0]  # z.B. "5:56"
        fast_60 = paces_60["easy"][0]  # z.B. "4:34"

        # Konvertiere zu Sekunden für Vergleich
        def to_sec(p: str) -> int:
            m, s = p.split(":")
            return int(m) * 60 + int(s)

        assert to_sec(fast_60) < to_sec(fast_40)


class TestGetPaceForRunType:
    """Pace-Berechnung mit Fallback-Kette."""

    def test_vdot_has_priority(self) -> None:
        """VDOT-Paces haben Vorrang über Race-Pace."""
        pace_vdot = get_pace_for_run_type("easy", vdot=50.0, race_pace=300.0)
        pace_race = get_pace_for_run_type("easy", vdot=None, race_pace=300.0)
        # Beide geben Paces zurück, aber mit unterschiedlichen Werten
        assert pace_vdot[0] is not None
        assert pace_race[0] is not None
        assert pace_vdot != pace_race  # Unterschiedliche Berechnung

    def test_fallback_to_race_pace(self) -> None:
        """Ohne VDOT → Race-Pace Multiplikatoren."""
        pace_min, pace_max = get_pace_for_run_type("easy", vdot=None, race_pace=300.0)
        assert pace_min is not None
        assert pace_max is not None

    def test_no_data_returns_none(self) -> None:
        """Ohne jede Daten → (None, None)."""
        pace_min, pace_max = get_pace_for_run_type("easy", vdot=None, race_pace=None)
        assert pace_min is None
        assert pace_max is None

    def test_unknown_run_type_uses_easy(self) -> None:
        """Unbekannter Run-Type fällt auf Easy zurück."""
        pace_min, pace_max = get_pace_for_run_type("unknown_type", race_pace=300.0)
        assert pace_min is not None

    def test_tempo_faster_than_easy(self) -> None:
        """Tempo-Pace ist schneller als Easy-Pace."""
        easy = get_pace_for_run_type("easy", vdot=50.0)
        tempo = get_pace_for_run_type("tempo", vdot=50.0)

        def to_sec(p: str) -> int:
            m, s = p.split(":")
            return int(m) * 60 + int(s)

        assert easy[0] is not None and tempo[0] is not None
        assert to_sec(tempo[0]) < to_sec(easy[0])


# ---------------------------------------------------------------------------
# HR-Zonen
# ---------------------------------------------------------------------------


class TestGetHrZone:
    """HR-Ziel-Zonen für Run-Typen."""

    def test_friel_zones_with_lthr(self) -> None:
        """Friel-Zonen werden aus LTHR berechnet."""
        hr_min, hr_max = get_hr_zone_for_run_type("easy", lthr=170)
        assert hr_min is not None
        assert hr_max is not None
        # Easy = Zone 2 (Aerobic) bei Friel: 85-90% LTHR
        assert hr_min < 170  # Unter LTHR
        assert hr_max <= 170

    def test_karvonen_zones_fallback(self) -> None:
        """Karvonen-Zonen als Fallback."""
        hr_min, hr_max = get_hr_zone_for_run_type("easy", resting_hr=52, max_hr=190)
        assert hr_min is not None
        assert hr_max is not None

    def test_no_data_returns_none(self) -> None:
        """Ohne HR-Daten → (None, None)."""
        hr_min, hr_max = get_hr_zone_for_run_type("easy")
        assert hr_min is None
        assert hr_max is None

    def test_tempo_higher_zone_than_easy(self) -> None:
        """Tempo hat höhere HR-Zone als Easy."""
        easy_min, easy_max = get_hr_zone_for_run_type("easy", lthr=170)
        tempo_min, tempo_max = get_hr_zone_for_run_type("tempo", lthr=170)
        assert easy_max is not None and tempo_min is not None
        assert tempo_min >= easy_max  # Tempo-Zone beginnt über Easy-Zone

    def test_intervals_zone_5(self) -> None:
        """Intervalle nutzen Zone 5 (VO2max/Supra-Threshold)."""
        hr_min, hr_max = get_hr_zone_for_run_type("intervals", lthr=170)
        assert hr_min is not None
        assert hr_min >= 170  # Zone 5 bei Friel: >100% LTHR

    def test_recovery_zone_1(self) -> None:
        """Recovery nutzt Zone 1."""
        hr_min, hr_max = get_hr_zone_for_run_type("recovery", lthr=170)
        assert hr_max is not None
        assert hr_max <= round(170 * 0.85)  # Zone 1 bei Friel: <85% LTHR

    def test_friel_priority_over_karvonen(self) -> None:
        """Friel hat Vorrang über Karvonen wenn LTHR vorhanden."""
        friel_min, _ = get_hr_zone_for_run_type("easy", lthr=170, resting_hr=52, max_hr=190)
        karv_min, _ = get_hr_zone_for_run_type("easy", resting_hr=52, max_hr=190)
        # Friel und Karvonen geben unterschiedliche Zone-2-Grenzen
        assert friel_min is not None and karv_min is not None
        # Friel Zone 2 starts at 85% LTHR = 144.5
        assert friel_min == round(170 * 0.85)


# ---------------------------------------------------------------------------
# Kombiniertes Enrichment
# ---------------------------------------------------------------------------


class TestEnrichRunDetailsParams:
    """Kombinierte Pace + HR Enrichment."""

    def test_full_enrichment(self) -> None:
        """Alle Parameter vorhanden → Pace + HR."""
        result = enrich_run_details_params(
            "easy",
            vdot=50.0,
            lthr=170,
            resting_hr=52,
            max_hr=190,
        )
        assert result["pace_min"] is not None
        assert result["pace_max"] is not None
        assert result["hr_min"] is not None
        assert result["hr_max"] is not None

    def test_vdot_only(self) -> None:
        """Nur VDOT → Pace ja, HR nein."""
        result = enrich_run_details_params("easy", vdot=50.0)
        assert result["pace_min"] is not None
        assert result["hr_min"] is None

    def test_hr_only(self) -> None:
        """Nur HR → kein Pace, HR ja."""
        result = enrich_run_details_params("easy", lthr=170)
        assert result["pace_min"] is None
        assert result["hr_min"] is not None

    def test_no_data(self) -> None:
        """Keine Daten → alles None."""
        result = enrich_run_details_params("easy")
        assert all(v is None for v in result.values())
