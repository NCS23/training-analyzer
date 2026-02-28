"""Tests fuer km_split_calculator — boundary coordinates + corrected pace."""

from app.services.km_split_calculator import calculate_km_splits, calculate_session_gap


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


def _make_downhill_track(km: float, total_loss_m: float, points_per_km: int = 100) -> dict:
    """Generate a downhill GPS track with steady elevation loss."""
    total_points = max(2, int(km * points_per_km))
    lat_per_m = 1.0 / 111320.0
    total_m = km * 1000
    speed_ms = 3.0

    points = []
    for i in range(total_points):
        frac = i / (total_points - 1)
        dist_m = frac * total_m
        alt = 200.0 - frac * total_loss_m
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


class TestConfigurableFactors:
    """Elevation correction factors can be customized."""

    def test_higher_gain_factor_faster_correction(self) -> None:
        """Higher gain factor → bigger correction → faster corrected pace."""
        track = _make_uphill_track(3.0, total_gain_m=150.0)
        splits_default = calculate_km_splits(track)
        splits_high = calculate_km_splits(track, gain_factor=20.0)

        default_corrected = [
            s["pace_corrected_min_per_km"]
            for s in splits_default
            if s["pace_corrected_min_per_km"] is not None
        ]
        high_corrected = [
            s["pace_corrected_min_per_km"]
            for s in splits_high
            if s["pace_corrected_min_per_km"] is not None
        ]

        assert len(default_corrected) > 0
        assert len(high_corrected) > 0
        # Higher gain factor means more time subtracted → faster corrected pace
        for d, h in zip(default_corrected, high_corrected):
            assert h < d, f"High factor {h} should be faster than default {d}"

    def test_zero_gain_factor_no_gain_correction(self) -> None:
        """With gain_factor=0, uphill has no correction effect."""
        track = _make_uphill_track(3.0, total_gain_m=150.0)
        splits = calculate_km_splits(track, gain_factor=0.0, loss_factor=0.0)

        # With both factors at 0, correction is 0, but gain/loss is still non-zero
        # so corrected pace equals actual pace
        for s in splits:
            if s["pace_corrected_min_per_km"] is not None:
                assert abs(s["pace_corrected_min_per_km"] - s["pace_min_per_km"]) < 0.01

    def test_custom_loss_factor(self) -> None:
        """Custom loss_factor parameter is respected on a downhill track."""
        track = _make_downhill_track(3.0, total_loss_m=150.0)
        splits_low = calculate_km_splits(track, loss_factor=0.0)
        splits_high = calculate_km_splits(track, loss_factor=15.0)

        low_corrected = [
            s["pace_corrected_min_per_km"]
            for s in splits_low
            if s["pace_corrected_min_per_km"] is not None
        ]
        high_corrected = [
            s["pace_corrected_min_per_km"]
            for s in splits_high
            if s["pace_corrected_min_per_km"] is not None
        ]

        # Downhill: higher loss factor means more time added back → slower GAP
        assert len(high_corrected) > 0
        for low, high in zip(low_corrected, high_corrected):
            assert high > low, f"High loss factor {high} should be slower than low {low}"

    def test_default_factors_match_original_behavior(self) -> None:
        """Passing None factors produces same results as no factors."""
        track = _make_uphill_track(3.0, total_gain_m=150.0)
        splits_none = calculate_km_splits(track)
        splits_explicit = calculate_km_splits(track, gain_factor=10.0, loss_factor=5.0)

        for a, b in zip(splits_none, splits_explicit):
            assert a["pace_corrected_min_per_km"] == b["pace_corrected_min_per_km"]


class TestSessionGAP:
    """Session-level Grade Adjusted Pace calculation."""

    def test_session_gap_flat_track(self) -> None:
        """Flat track has no session GAP (all corrected paces are None)."""
        track = _make_straight_track(3.0)
        splits = calculate_km_splits(track)
        gap = calculate_session_gap(splits)
        assert gap is None

    def test_session_gap_uphill(self) -> None:
        """Uphill track has session GAP faster than actual pace."""
        track = _make_uphill_track(5.0, total_gain_m=250.0)
        splits = calculate_km_splits(track)
        gap = calculate_session_gap(splits)

        assert gap is not None
        # GAP should be faster than the actual pace of ~5:33
        assert gap < 5.6

    def test_session_gap_reasonable(self) -> None:
        """Session GAP stays within 1-30 min/km."""
        track = _make_uphill_track(5.0, total_gain_m=250.0)
        splits = calculate_km_splits(track)
        gap = calculate_session_gap(splits)

        assert gap is not None
        assert 1.0 <= gap <= 30.0

    def test_session_gap_empty_splits(self) -> None:
        """Empty splits list returns None."""
        gap = calculate_session_gap([])
        assert gap is None

    def test_session_gap_with_custom_factors(self) -> None:
        """Session GAP changes with different elevation factors."""
        track = _make_uphill_track(5.0, total_gain_m=250.0)

        splits_default = calculate_km_splits(track)
        splits_high = calculate_km_splits(track, gain_factor=20.0)

        gap_default = calculate_session_gap(splits_default)
        gap_high = calculate_session_gap(splits_high)

        assert gap_default is not None
        assert gap_high is not None
        assert gap_high < gap_default  # Higher factor → more correction → faster GAP
