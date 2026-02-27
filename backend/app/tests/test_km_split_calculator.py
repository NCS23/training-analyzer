"""Tests fuer km_split_calculator — boundary coordinates + corrected pace."""

from app.services.km_split_calculator import calculate_km_splits


def _make_straight_track(km: float, points_per_km: int = 100) -> dict:
    """Generate a straight-line GPS track of given length.

    Points go north along lng=13.405, starting at lat=52.52.
    Each degree of latitude is ~111,320 m.
    """
    total_points = max(2, int(km * points_per_km))
    lat_per_m = 1.0 / 111320.0
    total_m = km * 1000
    speed_ms = 3.0  # 3 m/s ≈ 5:33 /km

    points = []
    for i in range(total_points):
        frac = i / (total_points - 1)
        dist_m = frac * total_m
        points.append(
            {
                "lat": 52.52 + dist_m * lat_per_m,
                "lng": 13.405,
                "seconds": dist_m / speed_ms,
                "hr": 150,
                "alt": 50.0,
            }
        )
    return {"points": points}


def _make_uphill_track(km: float, total_gain_m: float, points_per_km: int = 100) -> dict:
    """Generate an uphill GPS track with steady elevation gain."""
    total_points = max(2, int(km * points_per_km))
    lat_per_m = 1.0 / 111320.0
    total_m = km * 1000
    speed_ms = 3.0  # 3 m/s ≈ 5:33 /km

    points = []
    for i in range(total_points):
        frac = i / (total_points - 1)
        dist_m = frac * total_m
        alt = 50.0 + frac * total_gain_m
        points.append(
            {
                "lat": 52.52 + dist_m * lat_per_m,
                "lng": 13.405,
                "seconds": dist_m / speed_ms,
                "hr": 150,
                "alt": alt,
            }
        )
    return {"points": points}


class TestBoundaryCoordinates:
    """Km splits include interpolated boundary lat/lng."""

    def test_boundary_fields_present(self) -> None:
        """Each split has boundary_lat and boundary_lng."""
        track = _make_straight_track(3.5)
        splits = calculate_km_splits(track)

        assert len(splits) >= 3
        for s in splits:
            assert "boundary_lat" in s
            assert "boundary_lng" in s
            assert s["boundary_lat"] is not None
            assert s["boundary_lng"] is not None

    def test_boundary_lat_increases_northward(self) -> None:
        """Boundaries are ordered north along the track."""
        track = _make_straight_track(5.0)
        splits = calculate_km_splits(track)

        lats = [s["boundary_lat"] for s in splits]
        for i in range(1, len(lats)):
            assert lats[i] > lats[i - 1], f"Split {i}: lat should increase"

    def test_boundary_between_points(self) -> None:
        """Boundary lat is between the start and end of the track (within rounding)."""
        track = _make_straight_track(2.5)
        splits = calculate_km_splits(track)

        start_lat = track["points"][0]["lat"]
        end_lat = track["points"][-1]["lat"]
        epsilon = 1e-5  # rounding tolerance

        for s in splits:
            assert start_lat - epsilon <= s["boundary_lat"] <= end_lat + epsilon

    def test_partial_split_uses_last_point(self) -> None:
        """Final partial split has boundary at last GPS point."""
        track = _make_straight_track(2.3)
        splits = calculate_km_splits(track)

        last_split = splits[-1]
        assert last_split["is_partial"] is True

        last_point = track["points"][-1]
        assert abs(last_split["boundary_lat"] - last_point["lat"]) < 1e-5
        assert abs(last_split["boundary_lng"] - last_point["lng"]) < 1e-5

    def test_boundary_lng_constant_straight_track(self) -> None:
        """On a north-only track, all boundary lngs equal the track lng."""
        track = _make_straight_track(3.0)
        splits = calculate_km_splits(track)

        for s in splits:
            assert abs(s["boundary_lng"] - 13.405) < 1e-5

    def test_few_points_still_work(self) -> None:
        """Two points spanning > 1km produce at least one split."""
        track = {
            "points": [
                {"lat": 52.52, "lng": 13.405, "seconds": 0, "hr": 150, "alt": 50},
                {"lat": 52.54, "lng": 13.405, "seconds": 700, "hr": 155, "alt": 55},
            ]
        }
        splits = calculate_km_splits(track)
        assert len(splits) >= 1
        assert splits[0]["boundary_lat"] is not None


class TestCorrectedPace:
    """Elevation-corrected pace (GAP) tests."""

    def test_flat_track_no_correction(self) -> None:
        """Flat track should have no corrected pace (None)."""
        track = _make_straight_track(3.0)
        splits = calculate_km_splits(track)

        for s in splits:
            # Flat: no elevation gain/loss above threshold → no correction
            assert s["pace_corrected_min_per_km"] is None
            assert s["pace_corrected_formatted"] is None

    def test_uphill_corrected_is_faster(self) -> None:
        """Uphill splits: corrected pace should be faster than actual pace."""
        track = _make_uphill_track(3.0, total_gain_m=150.0)
        splits = calculate_km_splits(track)

        # At least one split should have corrected pace
        corrected_splits = [s for s in splits if s["pace_corrected_min_per_km"] is not None]
        assert len(corrected_splits) > 0

        for s in corrected_splits:
            assert s["pace_corrected_min_per_km"] < s["pace_min_per_km"], (
                f"Corrected pace {s['pace_corrected_min_per_km']} "
                f"should be faster than actual {s['pace_min_per_km']}"
            )

    def test_corrected_pace_has_formatted(self) -> None:
        """Corrected pace should have formatted string when present."""
        track = _make_uphill_track(3.0, total_gain_m=150.0)
        splits = calculate_km_splits(track)

        for s in splits:
            if s["pace_corrected_min_per_km"] is not None:
                assert s["pace_corrected_formatted"] is not None
                assert ":" in s["pace_corrected_formatted"]

    def test_corrected_pace_reasonable(self) -> None:
        """Corrected pace should stay within 1-30 min/km range."""
        track = _make_uphill_track(3.0, total_gain_m=300.0)
        splits = calculate_km_splits(track)

        for s in splits:
            if s["pace_corrected_min_per_km"] is not None:
                assert 1.0 <= s["pace_corrected_min_per_km"] <= 30.0
