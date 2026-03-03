"""Tests for the unified Segment model (#133)."""

import pytest

from app.models.segment import (
    Segment,
    intervals_to_segments,
    lap_to_segment,
    laps_to_segments,
    run_interval_to_segment,
    segment_to_lap_response,
)
from app.models.session import LapResponse
from app.models.weekly_plan import RunInterval


class TestSegmentModel:
    """Test Segment Pydantic model construction and validation."""

    def test_create_soll_segment(self) -> None:
        seg = Segment(
            position=0,
            segment_type="work",
            target_duration_minutes=3.0,
            target_pace_min="4:30",
            target_pace_max="4:45",
            repeats=4,
        )
        assert seg.position == 0
        assert seg.segment_type == "work"
        assert seg.target_duration_minutes == 3.0
        assert seg.repeats == 4
        # Ist-Felder bleiben None
        assert seg.actual_duration_seconds is None
        assert seg.actual_hr_avg is None

    def test_create_ist_segment(self) -> None:
        seg = Segment(
            position=2,
            segment_type="steady",
            actual_duration_seconds=600.0,
            actual_distance_km=1.85,
            actual_pace_formatted="5:24",
            actual_hr_avg=155,
            actual_hr_max=162,
            actual_hr_min=148,
            actual_cadence_spm=178,
            start_seconds=120.0,
            end_seconds=720.0,
        )
        assert seg.actual_distance_km == 1.85
        assert seg.actual_hr_avg == 155
        assert seg.start_seconds == 120.0
        # Soll-Felder bleiben None
        assert seg.target_duration_minutes is None

    def test_invalid_segment_type_rejected(self) -> None:
        with pytest.raises(ValueError):
            Segment(position=0, segment_type="invalid_type")

    def test_all_canonical_segment_types(self) -> None:
        for st in [
            "warmup",
            "cooldown",
            "steady",
            "work",
            "recovery_jog",
            "rest",
            "strides",
            "drills",
        ]:
            seg = Segment(position=0, segment_type=st)
            assert seg.segment_type == st

    def test_default_repeats_is_one(self) -> None:
        seg = Segment(position=0, segment_type="work")
        assert seg.repeats == 1


class TestExpand:
    """Test Segment.expand() method."""

    def test_expand_single_repeat(self) -> None:
        seg = Segment(position=0, segment_type="steady", repeats=1)
        expanded = seg.expand()
        assert len(expanded) == 1
        assert expanded[0].segment_type == "steady"
        assert expanded[0].repeats == 1

    def test_expand_four_repeats(self) -> None:
        seg = Segment(
            position=0,
            segment_type="work",
            target_duration_minutes=3.0,
            target_pace_min="4:30",
            repeats=4,
        )
        expanded = seg.expand()
        # 4 work + 3 recovery_jog = 7
        assert len(expanded) == 7

        # Check work segments
        work_segs = [s for s in expanded if s.segment_type == "work"]
        assert len(work_segs) == 4
        for ws in work_segs:
            assert ws.repeats == 1
            assert ws.target_duration_minutes == 3.0
            assert ws.target_pace_min == "4:30"

        # Check recovery_jog segments
        recovery_segs = [s for s in expanded if s.segment_type == "recovery_jog"]
        assert len(recovery_segs) == 3

    def test_expand_two_repeats(self) -> None:
        seg = Segment(position=0, segment_type="work", repeats=2)
        expanded = seg.expand()
        # 2 work + 1 recovery = 3
        assert len(expanded) == 3
        assert expanded[0].segment_type == "work"
        assert expanded[1].segment_type == "recovery_jog"
        assert expanded[2].segment_type == "work"

    def test_expand_preserves_positions(self) -> None:
        seg = Segment(position=5, segment_type="work", repeats=3)
        expanded = seg.expand()
        positions = [s.position for s in expanded]
        assert positions == [5, 6, 7, 8, 9]


class TestRunIntervalToSegment:
    """Test RunInterval → Segment conversion."""

    def test_basic_conversion(self) -> None:
        interval = RunInterval(
            type="work",
            duration_minutes=3.0,
            target_pace_min="4:30",
            target_pace_max="4:45",
            target_hr_min=160,
            target_hr_max=175,
            repeats=4,
        )
        seg = run_interval_to_segment(interval, position=2)
        assert seg.position == 2
        assert seg.segment_type == "work"
        assert seg.target_duration_minutes == 3.0
        assert seg.target_pace_min == "4:30"
        assert seg.target_pace_max == "4:45"
        assert seg.target_hr_min == 160
        assert seg.target_hr_max == 175
        assert seg.repeats == 4

    def test_minimal_interval(self) -> None:
        interval = RunInterval(type="warmup", duration_minutes=10.0)
        seg = run_interval_to_segment(interval)
        assert seg.segment_type == "warmup"
        assert seg.target_duration_minutes == 10.0
        assert seg.target_pace_min is None
        assert seg.repeats == 1


class TestLapToSegment:
    """Test LapResponse → Segment conversion."""

    def test_basic_conversion(self) -> None:
        lap = LapResponse(
            lap_number=3,
            duration_seconds=180,
            duration_formatted="3:00",
            distance_km=0.85,
            pace_min_per_km=3.53,
            pace_formatted="3:32",
            avg_hr_bpm=172,
            max_hr_bpm=178,
            min_hr_bpm=165,
            avg_cadence_spm=184,
            suggested_type="work",
            confidence="high",
            user_override=None,
            start_seconds=600.0,
            end_seconds=780.0,
        )
        seg = lap_to_segment(lap)
        assert seg.position == 2  # 1-indexed → 0-indexed
        assert seg.segment_type == "work"
        assert seg.actual_duration_seconds == 180.0
        assert seg.actual_distance_km == 0.85
        assert seg.actual_pace_formatted == "3:32"
        assert seg.actual_hr_avg == 172
        assert seg.actual_hr_max == 178
        assert seg.actual_hr_min == 165
        assert seg.actual_cadence_spm == 184
        assert seg.start_seconds == 600.0
        assert seg.end_seconds == 780.0
        assert seg.suggested_type == "work"
        assert seg.confidence == "high"
        assert seg.user_override is None

    def test_user_override_takes_precedence(self) -> None:
        lap = LapResponse(
            lap_number=1,
            duration_seconds=300,
            duration_formatted="5:00",
            suggested_type="steady",
            user_override="warmup",
        )
        seg = lap_to_segment(lap)
        assert seg.segment_type == "warmup"
        assert seg.user_override == "warmup"

    def test_legacy_type_migration(self) -> None:
        """Legacy lap types should be migrated to canonical types."""
        lap = LapResponse(
            lap_number=1,
            duration_seconds=120,
            duration_formatted="2:00",
            suggested_type="interval",  # legacy → "work"
        )
        seg = lap_to_segment(lap)
        assert seg.segment_type == "work"

        lap2 = LapResponse(
            lap_number=2,
            duration_seconds=60,
            duration_formatted="1:00",
            suggested_type="pause",  # legacy → "rest"
        )
        seg2 = lap_to_segment(lap2)
        assert seg2.segment_type == "rest"

    def test_no_type_defaults_to_steady(self) -> None:
        lap = LapResponse(
            lap_number=1,
            duration_seconds=600,
            duration_formatted="10:00",
        )
        seg = lap_to_segment(lap)
        assert seg.segment_type == "steady"


class TestSegmentToLapResponse:
    """Test Segment → LapResponse conversion."""

    def test_roundtrip(self) -> None:
        """Lap → Segment → Lap should preserve key fields."""
        original = LapResponse(
            lap_number=2,
            duration_seconds=180,
            duration_formatted="3:00",
            distance_km=0.85,
            pace_min_per_km=3.53,
            pace_formatted="3:32",
            avg_hr_bpm=172,
            max_hr_bpm=178,
            min_hr_bpm=165,
            avg_cadence_spm=184,
            suggested_type="work",
            confidence="high",
            start_seconds=600.0,
            end_seconds=780.0,
        )
        seg = lap_to_segment(original)
        restored = segment_to_lap_response(seg, lap_number=2)

        assert restored.lap_number == 2
        assert restored.duration_seconds == 180
        assert restored.distance_km == 0.85
        assert restored.avg_hr_bpm == 172
        assert restored.max_hr_bpm == 178
        assert restored.min_hr_bpm == 165
        assert restored.avg_cadence_spm == 184
        assert restored.suggested_type == "work"
        assert restored.confidence == "high"
        assert restored.start_seconds == 600.0

    def test_soll_only_segment_produces_empty_lap(self) -> None:
        seg = Segment(
            position=0,
            segment_type="work",
            target_duration_minutes=3.0,
        )
        lap = segment_to_lap_response(seg)
        assert lap.lap_number == 1
        assert lap.duration_seconds == 0
        assert lap.distance_km is None
        assert lap.avg_hr_bpm is None


class TestBatchConversions:
    """Test intervals_to_segments and laps_to_segments."""

    def test_intervals_to_segments(self) -> None:
        intervals = [
            RunInterval(type="warmup", duration_minutes=10.0),
            RunInterval(type="work", duration_minutes=3.0, repeats=4),
            RunInterval(type="cooldown", duration_minutes=10.0),
        ]
        segments = intervals_to_segments(intervals)
        assert len(segments) == 3
        assert segments[0].position == 0
        assert segments[0].segment_type == "warmup"
        assert segments[1].position == 1
        assert segments[1].segment_type == "work"
        assert segments[1].repeats == 4
        assert segments[2].position == 2
        assert segments[2].segment_type == "cooldown"

    def test_laps_to_segments(self) -> None:
        laps = [
            LapResponse(
                lap_number=1,
                duration_seconds=600,
                duration_formatted="10:00",
                suggested_type="warmup",
            ),
            LapResponse(
                lap_number=2, duration_seconds=180, duration_formatted="3:00", suggested_type="work"
            ),
            LapResponse(
                lap_number=3, duration_seconds=90, duration_formatted="1:30", suggested_type="rest"
            ),
        ]
        segments = laps_to_segments(laps)
        assert len(segments) == 3
        assert segments[0].segment_type == "warmup"
        assert segments[1].segment_type == "work"
        assert segments[2].segment_type == "rest"

    def test_empty_lists(self) -> None:
        assert intervals_to_segments([]) == []
        assert laps_to_segments([]) == []
