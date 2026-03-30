"""Tests für Route-Pacing Integration (#548)."""

from app.models.training_route import RouteSegment, Waypoint
from app.services.route_pacing import (
    RoutePacingRequest,
    _extract_elevation_per_km,
    calculate_route_pacing,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _flat_waypoints(distance_km: float, count: int = 20) -> list[Waypoint]:
    """Erzeugt gleichmäßig verteilte flache Waypoints."""
    return [
        Waypoint(
            lat=53.55 + i * 0.001,
            lng=9.99 + i * 0.001,
            alt=10.0,
            km_marker=round(i * distance_km / (count - 1), 2),
        )
        for i in range(count)
    ]


def _hilly_waypoints(distance_km: float, count: int = 20) -> list[Waypoint]:
    """Erzeugt Waypoints mit Höhenprofil (Anstieg in der Mitte)."""
    import math

    return [
        Waypoint(
            lat=53.55 + i * 0.001,
            lng=9.99 + i * 0.001,
            alt=10.0 + 40.0 * math.sin(math.pi * i / (count - 1)),
            km_marker=round(i * distance_km / (count - 1), 2),
        )
        for i in range(count)
    ]


def _three_segments(distance_km: float) -> list[RouteSegment]:
    """Standard 3-Segment-Aufteilung: Warmup 15%, Steady 70%, Cooldown 15%."""
    wu_end = round(distance_km * 0.15, 1)
    cd_start = round(distance_km * 0.85, 1)
    return [
        RouteSegment(segment_type="warmup", start_km=0, end_km=wu_end),
        RouteSegment(segment_type="steady", start_km=wu_end, end_km=cd_start),
        RouteSegment(segment_type="cooldown", start_km=cd_start, end_km=distance_km),
    ]


# ---------------------------------------------------------------------------
# Tests: Elevation-Extraktion
# ---------------------------------------------------------------------------


class TestElevationExtraction:
    def test_flat_waypoints_zero_elevation(self) -> None:
        wps = _flat_waypoints(10.0)
        result = _extract_elevation_per_km(wps, 10.0)
        assert len(result) == 10
        assert all(seg.gain_m == 0 and seg.loss_m == 0 for seg in result)

    def test_hilly_waypoints_nonzero_elevation(self) -> None:
        wps = _hilly_waypoints(10.0)
        result = _extract_elevation_per_km(wps, 10.0)
        assert len(result) == 10
        total_gain = sum(s.gain_m for s in result)
        total_loss = sum(s.loss_m for s in result)
        assert total_gain > 0
        assert total_loss > 0

    def test_no_altitude_returns_empty(self) -> None:
        wps = [
            Waypoint(lat=53.55, lng=9.99, km_marker=0),
            Waypoint(lat=53.56, lng=10.0, km_marker=5),
        ]
        result = _extract_elevation_per_km(wps, 5.0)
        assert result == []

    def test_single_waypoint_returns_empty(self) -> None:
        wps = [Waypoint(lat=53.55, lng=9.99, alt=10.0, km_marker=0)]
        result = _extract_elevation_per_km(wps, 1.0)
        assert result == []


# ---------------------------------------------------------------------------
# Tests: Pacing-Berechnung
# ---------------------------------------------------------------------------


class TestCalculateRoutePacing:
    def test_flat_even_strategy(self) -> None:
        distance = 10.0
        wps = _flat_waypoints(distance)
        segs = _three_segments(distance)
        req = RoutePacingRequest(target_time_seconds=3000, strategy="even")

        result = calculate_route_pacing(distance, wps, segs, req)

        assert result.strategy == "even"
        assert result.distance_km == distance
        assert result.target_time_seconds == 3000
        assert len(result.segment_pacing) == 3
        # Flach + Even → alle Segmente ähnliche Pace
        paces = [sp.avg_pace_sec_per_km for sp in result.segment_pacing]
        assert max(paces) - min(paces) < 5  # weniger als 5s Unterschied

    def test_negative_strategy_first_half_slower(self) -> None:
        distance = 10.0
        wps = _flat_waypoints(distance)
        segs = _three_segments(distance)
        req = RoutePacingRequest(target_time_seconds=3000, strategy="negative")

        result = calculate_route_pacing(distance, wps, segs, req)

        warmup_pace = result.segment_pacing[0].avg_pace_sec_per_km
        cooldown_pace = result.segment_pacing[2].avg_pace_sec_per_km
        # Bei Negative Splits: Cooldown-Pace schneller als Warmup
        assert cooldown_pace < warmup_pace

    def test_effort_based_adjusts_for_hills(self) -> None:
        distance = 10.0
        wps = _hilly_waypoints(distance)
        segs = _three_segments(distance)
        req = RoutePacingRequest(target_time_seconds=3000, strategy="effort_based")

        result = calculate_route_pacing(distance, wps, segs, req)

        assert len(result.segment_pacing) == 3
        # Effort-Based: Paces variieren wegen Höhenprofil
        paces = [sp.avg_pace_sec_per_km for sp in result.segment_pacing]
        assert max(paces) - min(paces) > 0

    def test_segment_times_sum_to_target(self) -> None:
        distance = 12.0
        wps = _flat_waypoints(distance)
        segs = _three_segments(distance)
        req = RoutePacingRequest(target_time_seconds=3600, strategy="even")

        result = calculate_route_pacing(distance, wps, segs, req)

        total_time = sum(sp.target_time_seconds for sp in result.segment_pacing)
        # Rundungstoleranzen erlauben
        assert abs(total_time - 3600) < 5

    def test_pace_min_always_less_than_max(self) -> None:
        distance = 10.0
        wps = _flat_waypoints(distance)
        segs = _three_segments(distance)
        req = RoutePacingRequest(target_time_seconds=3000, strategy="even")

        result = calculate_route_pacing(distance, wps, segs, req)

        for sp in result.segment_pacing:
            min_sec = _parse_pace(sp.target_pace_min)
            max_sec = _parse_pace(sp.target_pace_max)
            assert min_sec < max_sec, (
                f"Segment {sp.segment_index}: {sp.target_pace_min} >= {sp.target_pace_max}"
            )

    def test_weather_adjustment_included(self) -> None:
        distance = 10.0
        wps = _flat_waypoints(distance)
        segs = _three_segments(distance)
        req = RoutePacingRequest(
            target_time_seconds=3000,
            strategy="even",
            temperature_celsius=30.0,
            wind_speed_kmh=20.0,
        )

        result = calculate_route_pacing(distance, wps, segs, req)

        assert result.weather_notes is not None
        assert "Hitze" in result.weather_notes or "Wind" in result.weather_notes

    def test_no_weather_notes_without_weather(self) -> None:
        distance = 10.0
        wps = _flat_waypoints(distance)
        segs = _three_segments(distance)
        req = RoutePacingRequest(target_time_seconds=3000, strategy="even")

        result = calculate_route_pacing(distance, wps, segs, req)

        assert result.weather_notes is None

    def test_segment_notes_contain_hints(self) -> None:
        distance = 10.0
        wps = _flat_waypoints(distance)
        segs = _three_segments(distance)
        req = RoutePacingRequest(target_time_seconds=3000, strategy="even")

        result = calculate_route_pacing(distance, wps, segs, req)

        warmup = result.segment_pacing[0]
        cooldown = result.segment_pacing[2]
        assert warmup.notes is not None and "einlaufen" in warmup.notes.lower()
        assert cooldown.notes is not None and "auslaufen" in cooldown.notes.lower()

    def test_response_formatted_fields(self) -> None:
        distance = 10.0
        wps = _flat_waypoints(distance)
        segs = _three_segments(distance)
        req = RoutePacingRequest(target_time_seconds=3000, strategy="even")

        result = calculate_route_pacing(distance, wps, segs, req)

        assert ":" in result.target_time_formatted
        assert ":" in result.avg_pace_formatted
        for sp in result.segment_pacing:
            assert ":" in sp.target_pace_min
            assert ":" in sp.target_pace_max
            assert ":" in sp.target_time_formatted


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_pace(pace_str: str) -> float:
    """Parst 'M:SS' zu Sekunden."""
    parts = pace_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])
