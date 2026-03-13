"""Tests für Soll/Ist Segment-Matching (Issue #138)."""

import pytest

from app.models.segment import Segment
from app.services.segment_matcher import (
    _range_delta,
    build_comparison,
    match_segments,
    pace_str_to_seconds,
)

# --- pace_str_to_seconds ---


class TestPaceStrToSeconds:
    def test_valid(self) -> None:
        assert pace_str_to_seconds("5:30") == 330

    def test_zero_seconds(self) -> None:
        assert pace_str_to_seconds("6:00") == 360

    def test_none(self) -> None:
        assert pace_str_to_seconds(None) is None

    def test_empty(self) -> None:
        assert pace_str_to_seconds("") is None

    def test_invalid(self) -> None:
        assert pace_str_to_seconds("abc") is None

    def test_whitespace(self) -> None:
        assert pace_str_to_seconds(" 5:30 ") == 330


# --- _range_delta ---


class TestRangeDelta:
    def test_within_range(self) -> None:
        assert _range_delta(150, 140, 160) == 0

    def test_below_range(self) -> None:
        assert _range_delta(130, 140, 160) == -10

    def test_above_range(self) -> None:
        assert _range_delta(170, 140, 160) == 10

    def test_at_lower_boundary(self) -> None:
        assert _range_delta(140, 140, 160) == 0

    def test_at_upper_boundary(self) -> None:
        assert _range_delta(160, 140, 160) == 0

    def test_only_lo(self) -> None:
        assert _range_delta(150, 140, None) == 10

    def test_only_hi(self) -> None:
        assert _range_delta(150, None, 160) == -10

    def test_no_bounds(self) -> None:
        assert _range_delta(150, None, None) is None


# --- match_segments ---


def _planned(
    segment_type: str = "steady",
    pace_min: str | None = None,
    pace_max: str | None = None,
    hr_min: int | None = None,
    hr_max: int | None = None,
    duration_min: float | None = None,
    distance_km: float | None = None,
    repeats: int = 1,
) -> Segment:
    return Segment(
        position=0,
        segment_type=segment_type,
        target_pace_min=pace_min,
        target_pace_max=pace_max,
        target_hr_min=hr_min,
        target_hr_max=hr_max,
        target_duration_minutes=duration_min,
        target_distance_km=distance_km,
        repeats=repeats,
    )


def _actual(
    segment_type: str = "steady",
    pace: str | None = None,
    hr_avg: int | None = None,
    duration_sec: float | None = None,
    distance_km: float | None = None,
) -> Segment:
    return Segment(
        position=0,
        segment_type=segment_type,
        actual_pace_formatted=pace,
        actual_hr_avg=hr_avg,
        actual_duration_seconds=duration_sec,
        actual_distance_km=distance_km,
    )


class TestMatchSegments:
    def test_equal_count_all_matched(self) -> None:
        planned = [_planned(segment_type="warmup"), _planned(), _planned(segment_type="cooldown")]
        actual = [_actual(segment_type="warmup"), _actual(), _actual(segment_type="cooldown")]
        result = match_segments(planned, actual)

        assert len(result) == 3
        assert all(m.match_quality == "matched" for m in result)
        assert all(m.planned is not None and m.actual is not None for m in result)

    def test_more_actual_unmatched(self) -> None:
        planned = [_planned()]
        actual = [_actual(), _actual(), _actual()]
        result = match_segments(planned, actual)

        assert len(result) == 3
        assert result[0].match_quality == "matched"
        assert result[1].match_quality == "unmatched_actual"
        assert result[2].match_quality == "unmatched_actual"

    def test_more_planned_unmatched(self) -> None:
        planned = [_planned(), _planned(), _planned()]
        actual = [_actual()]
        result = match_segments(planned, actual)

        assert len(result) == 3
        assert result[0].match_quality == "matched"
        assert result[1].match_quality == "unmatched_planned"
        assert result[2].match_quality == "unmatched_planned"

    def test_empty_both(self) -> None:
        assert match_segments([], []) == []

    def test_empty_planned(self) -> None:
        result = match_segments([], [_actual()])
        assert len(result) == 1
        assert result[0].match_quality == "unmatched_actual"

    def test_empty_actual(self) -> None:
        result = match_segments([_planned()], [])
        assert len(result) == 1
        assert result[0].match_quality == "unmatched_planned"

    def test_repeats_expanded(self) -> None:
        """repeats=4 wird zu 4 Work + 3 Recovery = 7 Segmente expandiert."""
        planned = [_planned(segment_type="work", repeats=4)]
        actual = [_actual() for _ in range(7)]
        result = match_segments(planned, actual)

        assert len(result) == 7
        assert all(m.match_quality == "matched" for m in result)

    def test_segment_type_from_actual_on_match(self) -> None:
        """Bei matched pair kommt segment_type vom actual."""
        planned = [_planned(segment_type="steady")]
        actual = [_actual(segment_type="work")]
        result = match_segments(planned, actual)

        assert result[0].segment_type == "work"


# --- Delta-Berechnung ---


class TestDeltaComputation:
    def test_pace_within_range_zero_delta(self) -> None:
        planned = [_planned(pace_min="5:00", pace_max="5:30")]
        actual = [_actual(pace="5:15")]
        result = match_segments(planned, actual)

        assert result[0].delta is not None
        assert result[0].delta.pace_delta_seconds == 0
        assert result[0].delta.pace_delta_formatted == "+0:00"

    def test_pace_slower_than_max(self) -> None:
        planned = [_planned(pace_min="5:00", pace_max="5:30")]
        actual = [_actual(pace="5:42")]  # 12 Sekunden zu langsam
        result = match_segments(planned, actual)

        assert result[0].delta is not None
        assert result[0].delta.pace_delta_seconds == 12
        assert result[0].delta.pace_delta_formatted == "+0:12"

    def test_pace_faster_than_min(self) -> None:
        planned = [_planned(pace_min="5:00", pace_max="5:30")]
        actual = [_actual(pace="4:55")]  # 5 Sekunden schneller
        result = match_segments(planned, actual)

        assert result[0].delta is not None
        assert result[0].delta.pace_delta_seconds == -5
        assert result[0].delta.pace_delta_formatted == "-0:05"

    def test_pace_no_target(self) -> None:
        planned = [_planned()]
        actual = [_actual(pace="5:15")]
        result = match_segments(planned, actual)

        assert result[0].delta is not None
        assert result[0].delta.pace_delta_seconds is None

    def test_hr_within_range(self) -> None:
        planned = [_planned(hr_min=140, hr_max=160)]
        actual = [_actual(hr_avg=150)]
        result = match_segments(planned, actual)

        assert result[0].delta is not None
        assert result[0].delta.hr_avg_delta == 0

    def test_hr_above_range(self) -> None:
        planned = [_planned(hr_min=140, hr_max=160)]
        actual = [_actual(hr_avg=170)]
        result = match_segments(planned, actual)

        assert result[0].delta is not None
        assert result[0].delta.hr_avg_delta == 10

    def test_hr_below_range(self) -> None:
        planned = [_planned(hr_min=140, hr_max=160)]
        actual = [_actual(hr_avg=130)]
        result = match_segments(planned, actual)

        assert result[0].delta is not None
        assert result[0].delta.hr_avg_delta == -10

    def test_duration_delta(self) -> None:
        planned = [_planned(duration_min=10.0)]  # 10 Minuten = 600s
        actual = [_actual(duration_sec=630.0)]  # 30s länger
        result = match_segments(planned, actual)

        assert result[0].delta is not None
        assert result[0].delta.duration_delta_seconds == 30.0

    def test_distance_delta(self) -> None:
        planned = [_planned(distance_km=5.0)]
        actual = [_actual(distance_km=5.123)]
        result = match_segments(planned, actual)

        assert result[0].delta is not None
        assert result[0].delta.distance_delta_km == 0.123

    def test_no_actual_data_no_deltas(self) -> None:
        planned = [_planned(pace_min="5:00", hr_min=140, duration_min=10.0)]
        actual = [_actual()]
        result = match_segments(planned, actual)

        delta = result[0].delta
        assert delta is not None
        assert delta.pace_delta_seconds is None
        assert delta.hr_avg_delta is None
        assert delta.duration_delta_seconds is None

    def test_unmatched_no_delta(self) -> None:
        planned = [_planned()]
        result = match_segments(planned, [])

        assert result[0].delta is None


# --- build_comparison ---


class TestBuildComparison:
    def test_basic(self) -> None:
        planned = [_planned(), _planned(segment_type="cooldown")]
        actual = [_actual(), _actual(segment_type="cooldown")]
        resp = build_comparison(planned, actual, planned_entry_id=42, planned_run_type="easy")

        assert resp.planned_entry_id == 42
        assert resp.planned_run_type == "easy"
        assert resp.planned_count == 2
        assert resp.actual_count == 2
        assert resp.has_mismatch is False
        assert len(resp.segments) == 2

    def test_mismatch_detected(self) -> None:
        planned = [_planned()]
        actual = [_actual(), _actual()]
        resp = build_comparison(planned, actual, planned_entry_id=1)

        assert resp.has_mismatch is True
        assert resp.planned_count == 1
        assert resp.actual_count == 2

    @pytest.mark.parametrize(
        ("repeats", "actual_count", "expected_mismatch"),
        [
            (3, 5, False),  # 3 work + 2 recovery = 5
            (3, 4, True),  # mismatch
            (1, 1, False),  # no expansion
        ],
    )
    def test_repeats_expansion_count(
        self, repeats: int, actual_count: int, expected_mismatch: bool
    ) -> None:
        planned = [_planned(segment_type="work", repeats=repeats)]
        actual = [_actual() for _ in range(actual_count)]
        resp = build_comparison(planned, actual, planned_entry_id=1)

        expected_expanded = repeats + max(0, repeats - 1)  # work + recovery
        assert resp.planned_count == expected_expanded
        assert resp.has_mismatch is expected_mismatch
