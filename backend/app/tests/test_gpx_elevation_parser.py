"""Tests fuer den GPX-Elevation-Parser."""

import xml.etree.ElementTree as ET

import pytest

from app.services.gpx_elevation_parser import parse_gpx_elevation

# ---------------------------------------------------------------------------
# Test-GPX Daten
# ---------------------------------------------------------------------------

_SIMPLE_GPX = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="52.5200" lon="13.4050"><ele>34.0</ele></trkpt>
    <trkpt lat="52.5290" lon="13.4050"><ele>36.0</ele></trkpt>
    <trkpt lat="52.5380" lon="13.4050"><ele>33.0</ele></trkpt>
    <trkpt lat="52.5470" lon="13.4050"><ele>35.0</ele></trkpt>
  </trkseg></trk>
</gpx>
"""

_FLAT_3KM_GPX = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="52.5200" lon="13.4050"><ele>34.0</ele></trkpt>
    <trkpt lat="52.5290" lon="13.4050"><ele>34.0</ele></trkpt>
    <trkpt lat="52.5380" lon="13.4050"><ele>34.0</ele></trkpt>
    <trkpt lat="52.5470" lon="13.4050"><ele>34.0</ele></trkpt>
    <trkpt lat="52.5560" lon="13.4050"><ele>34.0</ele></trkpt>
  </trkseg></trk>
</gpx>
"""

_WAYPOINT_GPX = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="52.5200" lon="13.4050"><ele>34.0</ele></wpt>
  <wpt lat="52.5290" lon="13.4050"><ele>36.0</ele></wpt>
  <wpt lat="52.5380" lon="13.4050"><ele>33.0</ele></wpt>
  <wpt lat="52.5470" lon="13.4050"><ele>35.0</ele></wpt>
</gpx>
"""

_ROUTE_GPX = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <rte>
    <rtept lat="52.5200" lon="13.4050"><ele>34.0</ele></rtept>
    <rtept lat="52.5290" lon="13.4050"><ele>36.0</ele></rtept>
    <rtept lat="52.5380" lon="13.4050"><ele>33.0</ele></rtept>
    <rtept lat="52.5470" lon="13.4050"><ele>35.0</ele></rtept>
  </rte>
</gpx>
"""


class TestGpxElevationParser:
    """Tests fuer parse_gpx_elevation."""

    def test_returns_segments(self) -> None:
        """Gibt eine nicht-leere Liste von ElevationSegments zurueck."""
        segments = parse_gpx_elevation(_SIMPLE_GPX)
        assert len(segments) > 0

    def test_segments_have_km_numbers(self) -> None:
        """Jeder Segment hat eine aufsteigende km-Nummer."""
        segments = parse_gpx_elevation(_SIMPLE_GPX)
        for i, seg in enumerate(segments):
            assert seg.km == i + 1

    def test_flat_course_no_elevation(self) -> None:
        """Flache Strecke: kein Hoehengewinn/-verlust."""
        segments = parse_gpx_elevation(_FLAT_3KM_GPX)
        for seg in segments:
            assert seg.gain_m == 0.0
            assert seg.loss_m == 0.0

    def test_gain_and_loss_are_non_negative(self) -> None:
        """Gain und Loss sind immer >= 0."""
        segments = parse_gpx_elevation(_SIMPLE_GPX)
        for seg in segments:
            assert seg.gain_m >= 0.0
            assert seg.loss_m >= 0.0

    def test_too_few_points_raises(self) -> None:
        """Weniger als 2 Trackpunkte wirft ValueError."""
        gpx = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg>
    <trkpt lat="52.5200" lon="13.4050"><ele>34.0</ele></trkpt>
  </trkseg></trk>
</gpx>
"""
        with pytest.raises(ValueError, match="zu wenige"):
            parse_gpx_elevation(gpx)

    def test_empty_gpx_raises(self) -> None:
        """Leere GPX-Datei ohne Trackpunkte wirft ValueError."""
        gpx = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" xmlns="http://www.topografix.com/GPX/1/1">
  <trk><trkseg></trkseg></trk>
</gpx>
"""
        with pytest.raises(ValueError, match="zu wenige"):
            parse_gpx_elevation(gpx)

    def test_waypoint_gpx_returns_segments(self) -> None:
        """GPX mit <wpt> Elementen wird korrekt geparst."""
        segments = parse_gpx_elevation(_WAYPOINT_GPX)
        assert len(segments) > 0

    def test_route_gpx_returns_segments(self) -> None:
        """GPX mit <rtept> Elementen wird korrekt geparst."""
        segments = parse_gpx_elevation(_ROUTE_GPX)
        assert len(segments) > 0

    def test_invalid_xml_raises(self) -> None:
        """Ungueltige XML-Datei wirft ET.ParseError."""
        with pytest.raises(ET.ParseError):
            parse_gpx_elevation(b"this is not xml")
