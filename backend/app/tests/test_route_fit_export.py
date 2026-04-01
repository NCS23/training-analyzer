"""Tests für route_fit_export.py — FIT Course Export (#577)."""

from __future__ import annotations

import pytest

from app.models.training_route import Waypoint
from app.services.route_fit_export import (
    _haversine_m,
    _resolve_altitude,
    generate_fit_course,
    safe_filename,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

WAYPOINTS_SIMPLE = [
    Waypoint(lat=53.5500, lng=9.9900, alt=20.0, km_marker=0.0),
    Waypoint(lat=53.5550, lng=9.9950, alt=22.0, km_marker=0.5),
    Waypoint(lat=53.5600, lng=10.0000, alt=25.0, km_marker=1.0),
]

WAYPOINTS_NO_ALT = [
    Waypoint(lat=53.5500, lng=9.9900, km_marker=0.0),
    Waypoint(lat=53.5550, lng=9.9950, km_marker=0.5),
]


# ---------------------------------------------------------------------------
# generate_fit_course
# ---------------------------------------------------------------------------


class TestGenerateFitCourse:
    def test_returns_bytes(self) -> None:
        result = generate_fit_course("Test Route", WAYPOINTS_SIMPLE, 1.0)
        assert isinstance(result, bytes)
        assert len(result) > 0

    def test_fit_header_magic(self) -> None:
        """FIT-Dateien beginnen mit einem gültigen Header (14 Byte)."""
        result = generate_fit_course("Test", WAYPOINTS_SIMPLE, 1.0)
        # FIT Header: Byte 8-11 = ".FIT" ASCII
        assert result[8:12] == b".FIT"

    def test_empty_waypoints(self) -> None:
        """Leere Waypoints erzeugen noch eine gültige FIT-Datei."""
        result = generate_fit_course("Test", [], 0.0)
        assert isinstance(result, bytes)
        assert result[8:12] == b".FIT"

    def test_waypoints_without_altitude(self) -> None:
        result = generate_fit_course("Route", WAYPOINTS_NO_ALT, 0.5)
        assert isinstance(result, bytes)

    def test_single_waypoint(self) -> None:
        single = [Waypoint(lat=53.55, lng=9.99, km_marker=0.0)]
        result = generate_fit_course("Single", single, 0.0)
        assert isinstance(result, bytes)

    def test_file_size_scales_with_waypoints(self) -> None:
        """Mehr Waypoints → größere Datei."""
        few = WAYPOINTS_SIMPLE[:2]
        many = WAYPOINTS_SIMPLE
        size_few = len(generate_fit_course("R", few, 0.5))
        size_many = len(generate_fit_course("R", many, 1.0))
        assert size_many > size_few


# ---------------------------------------------------------------------------
# safe_filename
# ---------------------------------------------------------------------------


class TestSafeFilename:
    def test_simple_name(self) -> None:
        assert safe_filename("Alsterpark Run") == "Alsterpark_Run"

    def test_special_chars_removed(self) -> None:
        result = safe_filename("Route #1: (Test!)")
        assert "#" not in result
        assert "!" not in result
        assert ":" not in result

    def test_umlauts_preserved(self) -> None:
        result = safe_filename("Läuft schön")
        assert "ä" in result
        assert "ö" in result

    def test_empty_name_returns_fallback(self) -> None:
        assert safe_filename("") == "route"
        assert safe_filename("###") == "route"

    def test_max_length(self) -> None:
        long_name = "A" * 200
        assert len(safe_filename(long_name)) <= 100

    def test_leading_trailing_spaces_trimmed(self) -> None:
        result = safe_filename("  Route  ")
        assert not result.startswith("_")
        assert not result.endswith("_")


# ---------------------------------------------------------------------------
# _haversine_m
# ---------------------------------------------------------------------------


class TestHaversineM:
    def test_same_point_is_zero(self) -> None:
        assert _haversine_m(53.55, 9.99, 53.55, 9.99) == pytest.approx(0.0, abs=1e-6)

    def test_known_distance(self) -> None:
        """Hamburg Rathaus → Alster: ca. 400m."""
        dist = _haversine_m(53.5503, 9.9928, 53.5537, 9.9949)
        assert 300 < dist < 600

    def test_one_degree_latitude(self) -> None:
        """1 Grad Breitengrad ≈ 111.2 km."""
        dist = _haversine_m(0.0, 0.0, 1.0, 0.0)
        assert 110_000 < dist < 112_000

    def test_one_degree_longitude_at_equator(self) -> None:
        """1 Grad Längengrad am Äquator ≈ 111.3 km."""
        dist = _haversine_m(0.0, 0.0, 0.0, 1.0)
        assert 110_000 < dist < 112_000

    def test_symmetry(self) -> None:
        d1 = _haversine_m(53.5, 9.99, 53.6, 10.0)
        d2 = _haversine_m(53.6, 10.0, 53.5, 9.99)
        assert d1 == pytest.approx(d2, rel=1e-10)


# ---------------------------------------------------------------------------
# _resolve_altitude
# ---------------------------------------------------------------------------


class TestResolveAltitude:
    def test_direct_altitude(self) -> None:
        wps = [Waypoint(lat=0.0, lng=0.0, alt=50.0)]
        assert _resolve_altitude(wps[0], wps, 0) == pytest.approx(50.0)

    def test_interpolates_from_neighbors(self) -> None:
        wps = [
            Waypoint(lat=0.0, lng=0.0, alt=0.0),
            Waypoint(lat=0.0, lng=0.1),  # kein alt
            Waypoint(lat=0.0, lng=0.2, alt=20.0),
        ]
        result = _resolve_altitude(wps[1], wps, 1)
        assert result == pytest.approx(10.0)

    def test_falls_back_to_prev_if_no_next(self) -> None:
        wps = [
            Waypoint(lat=0.0, lng=0.0, alt=30.0),
            Waypoint(lat=0.0, lng=0.1),  # kein alt, kein Nachfolger
        ]
        result = _resolve_altitude(wps[1], wps, 1)
        assert result == pytest.approx(30.0)

    def test_falls_back_to_next_if_no_prev(self) -> None:
        wps = [
            Waypoint(lat=0.0, lng=0.0),  # kein alt
            Waypoint(lat=0.0, lng=0.1, alt=40.0),
        ]
        result = _resolve_altitude(wps[0], wps, 0)
        assert result == pytest.approx(40.0)

    def test_returns_none_if_no_altitude_anywhere(self) -> None:
        wps = [
            Waypoint(lat=0.0, lng=0.0),
            Waypoint(lat=0.0, lng=0.1),
        ]
        result = _resolve_altitude(wps[0], wps, 0)
        assert result is None
