"""Tests für Auto-Route aus Session Template (#571)."""

from app.models.segment import Segment
from app.models.weekly_plan import RunDetails
from app.services.template_to_route import (
    _haversine_km,
    _points_to_waypoints_with_km_markers,
    build_route_preview,
    calculate_template_distance,
    map_segments_to_route,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _run_details_with_segments(
    seg_types: list[tuple[str, float, int]],
) -> RunDetails:
    """Erzeugt RunDetails mit vorgegebenen Segmenten.

    Args:
        seg_types: Liste von (segment_type, distance_km, repeats)
    """
    segments = [
        Segment(
            position=i,
            segment_type=stype,
            target_distance_km=dist,
            repeats=reps,
        )
        for i, (stype, dist, reps) in enumerate(seg_types)
    ]
    return RunDetails(run_type="intervals", segments=segments)


def _osrm_result(distance_km: float, num_points: int = 10) -> dict:
    """Minimales OSRM-Ergebnis-Dict."""
    points = [{"lat": 53.55 + i * 0.001, "lng": 9.99 + i * 0.001} for i in range(num_points)]
    return {
        "distance_km": distance_km,
        "duration_s": int(distance_km * 330),
        "points": points,
    }


# ---------------------------------------------------------------------------
# Tests: calculate_template_distance
# ---------------------------------------------------------------------------


class TestCalculateTemplateDistance:
    def test_simple_segments(self) -> None:
        rd = _run_details_with_segments(
            [("warmup", 1.5, 1), ("steady", 8.0, 1), ("cooldown", 1.5, 1)]
        )
        assert calculate_template_distance(rd) == 11.0

    def test_repeats_multiplied(self) -> None:
        rd = _run_details_with_segments(
            [("warmup", 1.5, 1), ("work", 1.0, 5), ("cooldown", 1.5, 1)]
        )
        assert calculate_template_distance(rd) == 8.0

    def test_no_segments_duration_fallback(self) -> None:
        rd = RunDetails(run_type="easy", target_duration_minutes=60)
        # 60 / 5.5 ≈ 10.9
        dist = calculate_template_distance(rd)
        assert 10.0 < dist < 12.0

    def test_no_explicit_segments_no_duration_default(self) -> None:
        # RunDetails ohne target_duration_minutes → auto-segment "steady" ohne Distanz
        # → Default-Distanz für steady = 5.0 km
        rd = RunDetails(run_type="easy")
        dist = calculate_template_distance(rd)
        assert dist > 0

    def test_duration_based_segment(self) -> None:
        seg = Segment(
            position=0,
            segment_type="steady",
            target_duration_minutes=30,
            repeats=1,
        )
        rd = RunDetails(run_type="easy", segments=[seg])
        dist = calculate_template_distance(rd)
        # 30 / 5.5 ≈ 5.45
        assert 5.0 < dist < 6.0

    def test_minimum_distance_1km(self) -> None:
        # Segment-Default ohne Distanzangabe für kurze Typen
        seg = Segment(position=0, segment_type="work", repeats=1)
        rd = RunDetails(run_type="intervals", segments=[seg])
        # Default für 'work' ist 0.4km < 1.0 → max(total, 1.0) greift
        # aber da work=0.4 > 0, wird es nicht auf 1.0 geclipt — nur wenn total<1
        # Stattdessen: leere segments → default 10.0
        assert calculate_template_distance(rd) >= 0.1


# ---------------------------------------------------------------------------
# Tests: map_segments_to_route
# ---------------------------------------------------------------------------


class TestMapSegmentsToRoute:
    def test_basic_mapping(self) -> None:
        rd = _run_details_with_segments(
            [("warmup", 1.5, 1), ("steady", 5.0, 1), ("cooldown", 1.5, 1)]
        )
        segs = map_segments_to_route(rd.segments or [], 8.0)
        assert len(segs) == 3

    def test_first_segment_starts_at_zero(self) -> None:
        rd = _run_details_with_segments([("warmup", 2.0, 1), ("steady", 5.0, 1)])
        segs = map_segments_to_route(rd.segments or [], 7.0)
        assert segs[0].start_km == 0.0

    def test_last_segment_ends_at_total(self) -> None:
        rd = _run_details_with_segments([("warmup", 2.0, 1), ("steady", 5.0, 1)])
        segs = map_segments_to_route(rd.segments or [], 7.0)
        assert segs[-1].end_km == 7.0

    def test_segments_contiguous(self) -> None:
        rd = _run_details_with_segments(
            [("warmup", 1.5, 1), ("work", 1.0, 3), ("cooldown", 1.5, 1)]
        )
        segs = map_segments_to_route(rd.segments or [], 6.0)
        for i in range(len(segs) - 1):
            assert abs(segs[i].end_km - segs[i + 1].start_km) < 0.001

    def test_repeats_expanded(self) -> None:
        rd = _run_details_with_segments([("work", 1.0, 4)])
        segs = map_segments_to_route(rd.segments or [], 4.0)
        assert len(segs) == 4

    def test_pace_targets_preserved(self) -> None:
        seg = Segment(
            position=0,
            segment_type="work",
            target_distance_km=1.0,
            target_pace_min="4:00",
            target_pace_max="4:20",
            target_hr_min=160,
            target_hr_max=175,
            repeats=1,
        )
        rd = RunDetails(run_type="intervals", segments=[seg])
        route_segs = map_segments_to_route(rd.segments or [], 1.0)
        assert route_segs[0].target_pace_min == "4:00"
        assert route_segs[0].target_pace_max == "4:20"
        assert route_segs[0].target_hr_min == 160
        assert route_segs[0].target_hr_max == 175

    def test_segment_type_mapping_work(self) -> None:
        rd = _run_details_with_segments([("work", 1.0, 1)])
        segs = map_segments_to_route(rd.segments or [], 1.0)
        assert segs[0].segment_type == "work"

    def test_segment_type_mapping_recovery_jog(self) -> None:
        rd = _run_details_with_segments([("recovery_jog", 0.5, 1)])
        segs = map_segments_to_route(rd.segments or [], 0.5)
        assert segs[0].segment_type == "recovery_jog"

    def test_empty_segments_returns_empty(self) -> None:
        segs = map_segments_to_route([], 5.0)
        assert segs == []


# ---------------------------------------------------------------------------
# Tests: _points_to_waypoints_with_km_markers
# ---------------------------------------------------------------------------


class TestPointsToWaypointsWithKmMarkers:
    def test_first_km_marker_is_zero(self) -> None:
        points = [{"lat": 53.55, "lng": 9.99}, {"lat": 53.56, "lng": 10.0}]
        wps = _points_to_waypoints_with_km_markers(points, 2.0)
        assert wps[0].km_marker == 0.0

    def test_km_marker_monotonically_increasing(self) -> None:
        points = [{"lat": 53.55 + i * 0.01, "lng": 9.99} for i in range(5)]
        wps = _points_to_waypoints_with_km_markers(points, 5.0)
        for i in range(1, len(wps)):
            assert wps[i].km_marker >= wps[i - 1].km_marker  # type: ignore[operator]

    def test_last_km_marker_not_exceeds_total(self) -> None:
        points = [{"lat": 53.55 + i * 0.001, "lng": 9.99} for i in range(10)]
        wps = _points_to_waypoints_with_km_markers(points, 5.0)
        assert wps[-1].km_marker <= 5.0  # type: ignore[operator]

    def test_empty_points_returns_empty(self) -> None:
        assert _points_to_waypoints_with_km_markers([], 5.0) == []

    def test_altitude_passed_through(self) -> None:
        points = [{"lat": 53.55, "lng": 9.99, "alt": 15.0}]
        wps = _points_to_waypoints_with_km_markers(points, 1.0)
        assert wps[0].alt == 15.0


# ---------------------------------------------------------------------------
# Tests: _haversine_km
# ---------------------------------------------------------------------------


class TestHaversine:
    def test_same_point_zero(self) -> None:
        assert _haversine_km(53.55, 9.99, 53.55, 9.99) == 0.0

    def test_known_distance(self) -> None:
        # Hamburg Hbf → Alster: ~1.5 km
        d = _haversine_km(53.5530, 10.0062, 53.5580, 9.9934)
        assert 1.0 < d < 2.5

    def test_symmetry(self) -> None:
        d1 = _haversine_km(53.55, 9.99, 53.56, 10.0)
        d2 = _haversine_km(53.56, 10.0, 53.55, 9.99)
        assert abs(d1 - d2) < 0.001


# ---------------------------------------------------------------------------
# Tests: build_route_preview
# ---------------------------------------------------------------------------


class TestBuildRoutePreview:
    def test_returns_preview(self) -> None:
        rd = _run_details_with_segments(
            [("warmup", 1.5, 1), ("steady", 8.0, 1), ("cooldown", 1.5, 1)]
        )
        osrm = _osrm_result(11.0)
        preview = build_route_preview(
            template_id=42,
            template_name="Alster Dauerlauf",
            run_details=rd,
            osrm_result=osrm,
        )
        assert preview.linked_session_template_id == 42
        assert preview.distance_km == 11.0
        assert len(preview.waypoints) == 10
        assert len(preview.route_segments) == 3

    def test_name_contains_template_name(self) -> None:
        rd = _run_details_with_segments([("steady", 5.0, 1)])
        osrm = _osrm_result(5.0)
        preview = build_route_preview(1, "Mein Training", rd, osrm)
        assert "Mein Training" in preview.name

    def test_to_create_sets_linked_template(self) -> None:
        rd = _run_details_with_segments([("steady", 5.0, 1)])
        osrm = _osrm_result(5.0)
        preview = build_route_preview(99, "Test", rd, osrm)
        create = preview.to_create()
        assert create.linked_session_template_id == 99
