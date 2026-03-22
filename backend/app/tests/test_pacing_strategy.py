"""Tests fuer den Pacing-Strategie Generator."""

import pytest

from app.models.pacing import ElevationSegment, PacingRequest, PacingResponse
from app.services.pacing_strategy import generate_pacing_strategy

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _hm_request(**overrides: object) -> PacingRequest:
    """Erzeugt einen Standard-HM-Request (21.1 km, 1:59:59 = 7199s)."""
    defaults: dict[str, object] = {
        "target_time_seconds": 7199,
        "distance_km": 21.1,
        "strategy": "even",
    }
    defaults.update(overrides)
    return PacingRequest(**defaults)  # type: ignore[arg-type]


def _total_time(response: PacingResponse) -> float:
    """Berechnet die Gesamtzeit aus allen Splits."""
    return sum(s.target_pace_sec_per_km * s.distance_km for s in response.splits)


# ---------------------------------------------------------------------------
# Even Split
# ---------------------------------------------------------------------------


class TestEvenSplit:
    """Tests fuer die gleichmaessige Strategie."""

    def test_flat_course_all_splits_equal(self) -> None:
        """Flache Strecke: alle Splits haben die gleiche Pace."""
        result = generate_pacing_strategy(_hm_request(elevation_preset="flat"))

        paces = [s.target_pace_sec_per_km for s in result.splits]
        # Alle vollen km sollten gleiche Pace haben (Rundungsdifferenz < 0.5s)
        full_km_paces = paces[:-1]  # letzte km ist partial
        for pace in full_km_paces:
            assert abs(pace - full_km_paces[0]) < 0.5

    def test_total_matches_target(self) -> None:
        """Gesamtzeit muss exakt der Zielzeit entsprechen."""
        result = generate_pacing_strategy(_hm_request(elevation_preset="flat"))
        total = _total_time(result)
        assert abs(total - 7199) < 1.0  # Max 1 Sekunde Abweichung

    def test_correct_number_of_splits(self) -> None:
        """21.1 km = 21 volle km + 1 partielle km = 22 Splits."""
        result = generate_pacing_strategy(_hm_request())
        assert len(result.splits) == 22

    def test_last_split_is_partial(self) -> None:
        """Letzter Split hat distance_km < 1.0."""
        result = generate_pacing_strategy(_hm_request())
        last = result.splits[-1]
        assert last.distance_km == pytest.approx(0.1, abs=0.01)

    def test_cumulative_time_monotonic(self) -> None:
        """Kumulative Zeit muss streng monoton steigend sein."""
        result = generate_pacing_strategy(_hm_request())
        for i in range(1, len(result.splits)):
            assert result.splits[i].cumulative_seconds > result.splits[i - 1].cumulative_seconds

    def test_response_metadata(self) -> None:
        """Response enthaelt korrekte Metadaten."""
        result = generate_pacing_strategy(_hm_request())
        assert result.strategy == "even"
        assert result.strategy_label == "Gleichmäßig"
        assert result.distance_km == 21.1
        assert result.target_time_seconds == 7199
        assert result.target_time_formatted == "1:59:59"


# ---------------------------------------------------------------------------
# Negative Split
# ---------------------------------------------------------------------------


class TestNegativeSplit:
    """Tests fuer Negative-Split-Strategie."""

    def test_second_half_faster(self) -> None:
        """Zweite Haelfte muss schneller sein als erste."""
        result = generate_pacing_strategy(_hm_request(strategy="negative"))
        mid = len(result.splits) // 2
        first_half_avg = sum(s.target_pace_sec_per_km for s in result.splits[:mid]) / mid
        second_half_paces = [
            s.target_pace_sec_per_km for s in result.splits[mid:] if s.distance_km >= 0.5
        ]
        second_half_avg = sum(second_half_paces) / len(second_half_paces)
        assert second_half_avg < first_half_avg

    def test_total_matches_target(self) -> None:
        """Gesamtzeit muss auch bei Negative Split exakt stimmen."""
        result = generate_pacing_strategy(_hm_request(strategy="negative"))
        total = _total_time(result)
        assert abs(total - 7199) < 1.0

    def test_first_km_slowest(self) -> None:
        """Erste km sollte die langsamste sein."""
        result = generate_pacing_strategy(_hm_request(strategy="negative", elevation_preset="flat"))
        paces = [s.target_pace_sec_per_km for s in result.splits if s.distance_km >= 0.5]
        assert paces[0] == max(paces)


# ---------------------------------------------------------------------------
# Effort-Based
# ---------------------------------------------------------------------------


class TestEffortBased:
    """Tests fuer die Effort-Based Strategie mit Hoehenanpassung."""

    def test_uphill_slower_than_downhill(self) -> None:
        """Bergauf-km muss langsamer sein als Bergab-km."""
        segments = [
            ElevationSegment(km=1, gain_m=0, loss_m=0),
            ElevationSegment(km=2, gain_m=50, loss_m=0),  # bergauf
            ElevationSegment(km=3, gain_m=0, loss_m=50),  # bergab
        ]
        req = _hm_request(
            target_time_seconds=900,
            distance_km=3.0,
            strategy="effort_based",
            elevation_segments=segments,
        )
        result = generate_pacing_strategy(req)
        uphill = result.splits[1].target_pace_sec_per_km  # km 2
        downhill = result.splits[2].target_pace_sec_per_km  # km 3
        assert uphill > downhill

    def test_total_matches_with_elevation(self) -> None:
        """Gesamtzeit stimmt auch mit Hoehenprofil."""
        result = generate_pacing_strategy(
            _hm_request(strategy="effort_based", elevation_preset="hilly")
        )
        total = _total_time(result)
        assert abs(total - 7199) < 1.0

    def test_adjustment_notes_present(self) -> None:
        """Bergauf/bergab-Splits haben Anpassungshinweise."""
        segments = [
            ElevationSegment(km=1, gain_m=50, loss_m=0),
            ElevationSegment(km=2, gain_m=0, loss_m=50),
        ]
        req = _hm_request(
            target_time_seconds=600,
            distance_km=2.0,
            strategy="effort_based",
            elevation_segments=segments,
        )
        result = generate_pacing_strategy(req)
        assert result.splits[0].adjustment_note is not None
        assert "Bergauf" in result.splits[0].adjustment_note
        assert result.splits[1].adjustment_note is not None
        assert "Bergab" in result.splits[1].adjustment_note


# ---------------------------------------------------------------------------
# Elevation Presets
# ---------------------------------------------------------------------------


class TestElevationPresets:
    """Tests fuer die Hoehenprofil-Presets."""

    def test_flat_no_elevation(self) -> None:
        """Flat-Preset: kein Hoehenunterschied."""
        result = generate_pacing_strategy(_hm_request(elevation_preset="flat"))
        for split in result.splits:
            assert split.elevation_gain_m == 0.0
            assert split.elevation_loss_m == 0.0

    def test_rolling_has_variation(self) -> None:
        """Rolling-Preset: hat sowohl gain als auch loss."""
        result = generate_pacing_strategy(_hm_request(elevation_preset="rolling"))
        gains = [s.elevation_gain_m for s in result.splits]
        losses = [s.elevation_loss_m for s in result.splits]
        assert any(g > 0 for g in gains)
        assert any(lo > 0 for lo in losses)

    def test_hilly_significant_elevation(self) -> None:
        """Hilly-Preset: deutlich mehr Hoehenmeter als Rolling."""
        rolling = generate_pacing_strategy(_hm_request(elevation_preset="rolling"))
        hilly = generate_pacing_strategy(_hm_request(elevation_preset="hilly"))
        rolling_total = sum(s.elevation_gain_m for s in rolling.splits)
        hilly_total = sum(s.elevation_gain_m for s in hilly.splits)
        assert hilly_total > rolling_total


# ---------------------------------------------------------------------------
# Wetter-Anpassung
# ---------------------------------------------------------------------------


class TestWeatherAdjustment:
    """Tests fuer Wetter-bedingte Pace-Anpassung."""

    def test_heat_produces_weather_adjustment(self) -> None:
        """Hitze (30°C) erzeugt eine Wetter-Anpassung mit Penalty."""
        result = generate_pacing_strategy(_hm_request(temperature_celsius=30.0))
        assert result.weather_adjustment is not None
        assert result.weather_adjustment.penalty_sec_per_km > 0
        assert "Hitze" in result.weather_adjustment.description

    def test_no_penalty_below_threshold(self) -> None:
        """Unter 15°C kein Temperatur-Aufschlag."""
        result = generate_pacing_strategy(_hm_request(temperature_celsius=10.0))
        assert result.weather_adjustment is None

    def test_wind_produces_weather_adjustment(self) -> None:
        """Wind erzeugt eine Wetter-Anpassung."""
        result = generate_pacing_strategy(_hm_request(wind_speed_kmh=20.0))
        assert result.weather_adjustment is not None
        assert result.weather_adjustment.penalty_sec_per_km > 0
        assert "Wind" in result.weather_adjustment.description

    def test_combined_weather_description(self) -> None:
        """Kombinierte Wetter-Anpassung enthaelt beide Faktoren."""
        result = generate_pacing_strategy(
            _hm_request(temperature_celsius=30.0, wind_speed_kmh=15.0)
        )
        assert result.weather_adjustment is not None
        assert "Hitze" in result.weather_adjustment.description
        assert "Wind" in result.weather_adjustment.description

    def test_total_still_matches_with_weather(self) -> None:
        """Gesamtzeit stimmt auch mit Wetter-Anpassung (Normalisierung)."""
        result = generate_pacing_strategy(
            _hm_request(temperature_celsius=30.0, wind_speed_kmh=15.0)
        )
        total = _total_time(result)
        assert abs(total - 7199) < 1.0


# ---------------------------------------------------------------------------
# Normalisierung
# ---------------------------------------------------------------------------


class TestNormalization:
    """Tests fuer die Normalisierung auf exakte Zielzeit."""

    def test_exact_target_even(self) -> None:
        """Even: Summe == Zielzeit."""
        result = generate_pacing_strategy(_hm_request())
        assert abs(_total_time(result) - 7199) < 1.0

    def test_exact_target_with_all_adjustments(self) -> None:
        """Alle Anpassungen zusammen: Summe == Zielzeit."""
        result = generate_pacing_strategy(
            _hm_request(
                strategy="negative",
                elevation_preset="hilly",
                temperature_celsius=28.0,
                wind_speed_kmh=10.0,
            )
        )
        assert abs(_total_time(result) - 7199) < 1.0


# ---------------------------------------------------------------------------
# Formatierung
# ---------------------------------------------------------------------------


class TestFormatting:
    """Tests fuer Pace- und Zeit-Formatierung."""

    def test_pace_format(self) -> None:
        """Pace wird als M:SS formatiert."""
        result = generate_pacing_strategy(_hm_request())
        for split in result.splits:
            assert ":" in split.target_pace_formatted
            parts = split.target_pace_formatted.split(":")
            assert len(parts) == 2
            assert len(parts[1]) == 2  # Sekunden immer zweistellig

    def test_cumulative_format(self) -> None:
        """Kumulative Zeit wird als H:MM:SS oder MM:SS formatiert."""
        result = generate_pacing_strategy(_hm_request())
        last = result.splits[-1]
        assert ":" in last.cumulative_formatted


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests fuer Randfaelle."""

    def test_short_distance(self) -> None:
        """1 km Distanz: genau 1 Split."""
        result = generate_pacing_strategy(_hm_request(target_time_seconds=300, distance_km=1.0))
        assert len(result.splits) == 1
        assert result.splits[0].distance_km == 1.0

    def test_exact_km_no_partial(self) -> None:
        """Ganzzahlige Distanz: kein partieller Split."""
        result = generate_pacing_strategy(_hm_request(target_time_seconds=3000, distance_km=10.0))
        assert len(result.splits) == 10
        assert all(s.distance_km == 1.0 for s in result.splits)

    def test_marathon_distance(self) -> None:
        """Marathon (42.195 km): korrekte Anzahl Splits."""
        result = generate_pacing_strategy(
            _hm_request(target_time_seconds=14400, distance_km=42.195)
        )
        assert len(result.splits) == 43  # 42 volle + 1 partielle

    def test_notes_for_negative_split(self) -> None:
        """Negative-Split Strategie bekommt passenden Hinweis."""
        result = generate_pacing_strategy(_hm_request(strategy="negative"))
        assert any("langsamer" in n for n in result.notes)
