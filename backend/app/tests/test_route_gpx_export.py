"""Tests für GPX-Export mit Training-Extensions (#553)."""

import xml.etree.ElementTree as ET

from app.models.training_route import RouteSegment, Waypoint
from app.services.route_gpx_export import generate_gpx, safe_filename

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_NS = {
    "gpx": "http://www.topografix.com/GPX/1/1",
    "ta": "http://training-analyzer.app/gpx/extensions/v1",
}


def _flat_waypoints(distance_km: float = 5.0, count: int = 10) -> list[Waypoint]:
    return [
        Waypoint(
            lat=53.55 + i * 0.001,
            lng=9.99 + i * 0.001,
            alt=15.0,
            km_marker=round(i * distance_km / (count - 1), 2),
        )
        for i in range(count)
    ]


def _two_segments(distance_km: float = 5.0) -> list[RouteSegment]:
    return [
        RouteSegment(
            segment_type="warmup",
            start_km=0.0,
            end_km=round(distance_km * 0.4, 1),
            target_pace_min="5:30",
            target_pace_max="6:00",
            target_hr_min=130,
            target_hr_max=145,
        ),
        RouteSegment(
            segment_type="steady",
            start_km=round(distance_km * 0.4, 1),
            end_km=distance_km,
            target_pace_min="5:00",
            target_pace_max="5:20",
            target_hr_min=145,
            target_hr_max=160,
        ),
    ]


# ---------------------------------------------------------------------------
# Tests: generate_gpx
# ---------------------------------------------------------------------------


class TestGenerateGpx:
    def test_returns_bytes(self) -> None:
        result = generate_gpx("Test Route", _flat_waypoints(), [])
        assert isinstance(result, bytes)

    def test_valid_xml(self) -> None:
        result = generate_gpx("Test Route", _flat_waypoints(), [])
        root = ET.fromstring(result.decode("utf-8"))
        assert root.tag == "{http://www.topografix.com/GPX/1/1}gpx"

    def test_gpx_version_11(self) -> None:
        result = generate_gpx("Test Route", _flat_waypoints(), [])
        root = ET.fromstring(result.decode("utf-8"))
        assert root.get("version") == "1.1"

    def test_track_name(self) -> None:
        result = generate_gpx("Alster Runde", _flat_waypoints(), [])
        root = ET.fromstring(result.decode("utf-8"))
        name = root.find(".//gpx:trk/gpx:name", _NS)
        assert name is not None
        assert name.text == "Alster Runde"

    def test_trackpoints_count(self) -> None:
        waypoints = _flat_waypoints(count=15)
        result = generate_gpx("Route", waypoints, [])
        root = ET.fromstring(result.decode("utf-8"))
        trkpts = root.findall(".//gpx:trkseg/gpx:trkpt", _NS)
        assert len(trkpts) == 15

    def test_trackpoint_lat_lon(self) -> None:
        wps = _flat_waypoints(count=3)
        result = generate_gpx("Route", wps, [])
        root = ET.fromstring(result.decode("utf-8"))
        first = root.findall(".//gpx:trkseg/gpx:trkpt", _NS)[0]
        assert abs(float(first.get("lat", "0")) - wps[0].lat) < 0.0001
        assert abs(float(first.get("lon", "0")) - wps[0].lng) < 0.0001

    def test_elevation_included(self) -> None:
        result = generate_gpx("Route", _flat_waypoints(), [])
        root = ET.fromstring(result.decode("utf-8"))
        ele = root.find(".//gpx:trkseg/gpx:trkpt/gpx:ele", _NS)
        assert ele is not None
        assert float(ele.text or "0") == 15.0

    def test_segment_extensions_in_trk(self) -> None:
        segs = _two_segments()
        result = generate_gpx("Route", _flat_waypoints(), segs)
        root = ET.fromstring(result.decode("utf-8"))
        ta_segs = root.findall(".//gpx:trk/gpx:extensions/ta:segments/ta:segment", _NS)
        assert len(ta_segs) == 2

    def test_segment_extension_attributes(self) -> None:
        segs = _two_segments()
        result = generate_gpx("Route", _flat_waypoints(), segs)
        root = ET.fromstring(result.decode("utf-8"))
        first_seg = root.find(".//gpx:trk/gpx:extensions/ta:segments/ta:segment", _NS)
        assert first_seg is not None
        assert first_seg.get("type") == "warmup"
        assert first_seg.get("pace_min") == "5:30"
        assert first_seg.get("pace_max") == "6:00"
        assert first_seg.get("hr_min") == "130"
        assert first_seg.get("hr_max") == "145"

    def test_trackpoint_training_extension(self) -> None:
        segs = _two_segments()
        result = generate_gpx("Route", _flat_waypoints(), segs)
        root = ET.fromstring(result.decode("utf-8"))
        # Erster Trackpoint liegt im Warmup-Segment (km_marker=0)
        first_trkpt = root.findall(".//gpx:trkseg/gpx:trkpt", _NS)[0]
        ta_training = first_trkpt.find(".//ta:training", _NS)
        assert ta_training is not None
        assert ta_training.get("segment_type") == "warmup"

    def test_no_segments_no_trk_extensions(self) -> None:
        result = generate_gpx("Route", _flat_waypoints(), [])
        root = ET.fromstring(result.decode("utf-8"))
        ta_segs = root.findall(".//gpx:trk/gpx:extensions/ta:segments", _NS)
        assert len(ta_segs) == 0

    def test_no_segments_no_trkpt_extensions(self) -> None:
        result = generate_gpx("Route", _flat_waypoints(), [])
        root = ET.fromstring(result.decode("utf-8"))
        ta_training = root.findall(".//ta:training", _NS)
        assert len(ta_training) == 0

    def test_description_included(self) -> None:
        result = generate_gpx("Route", _flat_waypoints(), [], description="Mein Test")
        root = ET.fromstring(result.decode("utf-8"))
        desc = root.find(".//gpx:trk/gpx:desc", _NS)
        assert desc is not None
        assert desc.text == "Mein Test"

    def test_waypoints_without_km_marker_no_extension(self) -> None:
        wps = [Waypoint(lat=53.5, lng=9.9, alt=10.0) for _ in range(5)]
        segs = _two_segments()
        result = generate_gpx("Route", wps, segs)
        root = ET.fromstring(result.decode("utf-8"))
        # Keine km_marker → kein Segment-Match → kein Training-Extension
        ta_training = root.findall(".//ta:training", _NS)
        assert len(ta_training) == 0

    def test_lap_type_mapping(self) -> None:
        segs = [
            RouteSegment(segment_type="work", start_km=0.0, end_km=2.0),
        ]
        wps = [Waypoint(lat=53.5, lng=9.9, alt=10.0, km_marker=0.0)]
        result = generate_gpx("Route", wps, segs)
        root = ET.fromstring(result.decode("utf-8"))
        ta_training = root.find(".//ta:training", _NS)
        assert ta_training is not None
        assert ta_training.get("lap_type") == "interval"


# ---------------------------------------------------------------------------
# Tests: safe_filename
# ---------------------------------------------------------------------------


class TestSafeFilename:
    def test_simple_name(self) -> None:
        assert safe_filename("AlsterRunde") == "AlsterRunde"

    def test_spaces_to_underscore(self) -> None:
        assert safe_filename("Alster Runde 10km") == "Alster_Runde_10km"

    def test_special_chars_removed(self) -> None:
        result = safe_filename("Route: Test!")
        assert ":" not in result
        assert "!" not in result

    def test_umlauts_preserved(self) -> None:
        result = safe_filename("Münchener Straße")
        assert "ü" in result
        assert "ß" in result

    def test_empty_name_fallback(self) -> None:
        assert safe_filename("!!!") == "route"

    def test_long_name_truncated(self) -> None:
        long_name = "A" * 200
        assert len(safe_filename(long_name)) <= 100
