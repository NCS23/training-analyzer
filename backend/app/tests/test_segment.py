"""Tests for the unified Segment model (#133)."""

import pytest

from app.models.segment import (
    Segment,
    intervals_to_segments,
    lap_to_segment,
    laps_to_segments,
    laps_to_template_segments,
    run_interval_to_segment,
    segment_to_lap_response,
    segments_to_intervals,
)
from app.models.session import LapResponse
from app.models.weekly_plan import RunDetails, RunInterval


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


class TestSegmentsToIntervals:
    """Test Segment → RunInterval conversion (backward-compat)."""

    def test_soll_segment_uses_target_duration(self) -> None:
        seg = Segment(
            position=0,
            segment_type="work",
            target_duration_minutes=3.0,
            target_pace_min="4:30",
            target_pace_max="4:45",
            target_hr_min=160,
            target_hr_max=175,
            repeats=4,
        )
        intervals = segments_to_intervals([seg])
        assert len(intervals) == 1
        iv = intervals[0]
        assert iv.type == "work"
        assert iv.duration_minutes == 3.0
        assert iv.target_pace_min == "4:30"
        assert iv.target_pace_max == "4:45"
        assert iv.target_hr_min == 160
        assert iv.target_hr_max == 175
        assert iv.repeats == 4

    def test_ist_segment_uses_actual_duration(self) -> None:
        seg = Segment(
            position=0,
            segment_type="steady",
            actual_duration_seconds=600.0,
            actual_pace_formatted="5:24",
        )
        intervals = segments_to_intervals([seg])
        assert len(intervals) == 1
        assert intervals[0].duration_minutes == 10.0  # 600s / 60

    def test_no_duration_fallback(self) -> None:
        seg = Segment(position=0, segment_type="recovery_jog")
        intervals = segments_to_intervals([seg])
        assert intervals[0].duration_minutes == 1.0  # fallback

    def test_duration_capped_at_180(self) -> None:
        seg = Segment(
            position=0,
            segment_type="steady",
            actual_duration_seconds=12000.0,  # 200 minutes
        )
        intervals = segments_to_intervals([seg])
        assert intervals[0].duration_minutes == 180.0

    def test_empty_list(self) -> None:
        assert segments_to_intervals([]) == []

    def test_multiple_segments(self) -> None:
        segments = [
            Segment(position=0, segment_type="warmup", target_duration_minutes=10.0),
            Segment(position=1, segment_type="work", target_duration_minutes=3.0, repeats=4),
            Segment(position=2, segment_type="cooldown", target_duration_minutes=10.0),
        ]
        intervals = segments_to_intervals(segments)
        assert len(intervals) == 3
        assert intervals[0].type == "warmup"
        assert intervals[1].type == "work"
        assert intervals[1].repeats == 4
        assert intervals[2].type == "cooldown"


class TestLapsToTemplateSegments:
    """Test Laps → Template Segments with Ist→Soll derivation."""

    def test_derives_target_from_actual(self) -> None:
        laps = [
            LapResponse(
                lap_number=1,
                duration_seconds=600,
                duration_formatted="10:00",
                pace_formatted="5:30",
                suggested_type="warmup",
            ),
        ]
        segments = laps_to_template_segments(laps)
        assert len(segments) == 1
        seg = segments[0]
        # Ist-Daten vorhanden
        assert seg.actual_duration_seconds == 600.0
        assert seg.actual_pace_formatted == "5:30"
        # Soll-Daten aus Ist abgeleitet
        assert seg.target_duration_minutes == 10.0  # 600s / 60
        assert seg.target_pace_min == "5:30"

    def test_zero_duration_no_target(self) -> None:
        laps = [
            LapResponse(
                lap_number=1,
                duration_seconds=0,
                duration_formatted="0:00",
            ),
        ]
        segments = laps_to_template_segments(laps)
        assert segments[0].target_duration_minutes is None  # 0/60 = 0 → not > 0

    def test_long_duration_no_target(self) -> None:
        laps = [
            LapResponse(
                lap_number=1,
                duration_seconds=11000,  # ~183 min > 180
                duration_formatted="183:20",
            ),
        ]
        segments = laps_to_template_segments(laps)
        assert segments[0].target_duration_minutes is None  # > 180 → excluded

    def test_no_pace_no_target_pace(self) -> None:
        laps = [
            LapResponse(
                lap_number=1,
                duration_seconds=300,
                duration_formatted="5:00",
                suggested_type="steady",
            ),
        ]
        segments = laps_to_template_segments(laps)
        assert segments[0].target_pace_min is None

    def test_preserves_ist_data(self) -> None:
        laps = [
            LapResponse(
                lap_number=2,
                duration_seconds=180,
                duration_formatted="3:00",
                distance_km=0.85,
                pace_formatted="3:32",
                avg_hr_bpm=172,
                max_hr_bpm=178,
                min_hr_bpm=165,
                avg_cadence_spm=184,
                suggested_type="work",
                confidence="high",
                start_seconds=600.0,
                end_seconds=780.0,
            ),
        ]
        segments = laps_to_template_segments(laps)
        seg = segments[0]
        assert seg.actual_duration_seconds == 180.0
        assert seg.actual_distance_km == 0.85
        assert seg.actual_hr_avg == 172
        assert seg.suggested_type == "work"
        assert seg.confidence == "high"


class TestRunDetailsValidators:
    """Test RunDetails model validators for segments↔intervals sync."""

    def test_only_intervals_populates_segments(self) -> None:
        rd = RunDetails(
            run_type="easy",
            intervals=[
                RunInterval(type="warmup", duration_minutes=10.0),
                RunInterval(type="steady", duration_minutes=30.0),
            ],
        )
        assert rd.segments is not None
        assert len(rd.segments) == 2
        assert rd.segments[0].segment_type == "warmup"
        assert rd.segments[1].segment_type == "steady"

    def test_only_segments_populates_intervals(self) -> None:
        rd = RunDetails(
            run_type="tempo",
            segments=[
                Segment(position=0, segment_type="warmup", target_duration_minutes=10.0),
                Segment(
                    position=1,
                    segment_type="work",
                    target_duration_minutes=20.0,
                    target_pace_min="4:30",
                ),
            ],
        )
        assert rd.intervals is not None
        assert len(rd.intervals) == 2
        assert rd.intervals[0].type == "warmup"
        assert rd.intervals[0].duration_minutes == 10.0
        assert rd.intervals[1].type == "work"
        assert rd.intervals[1].target_pace_min == "4:30"

    def test_both_present_no_override(self) -> None:
        intervals = [RunInterval(type="warmup", duration_minutes=10.0)]
        segments = [Segment(position=0, segment_type="steady", target_duration_minutes=5.0)]
        rd = RunDetails(
            run_type="easy",
            intervals=intervals,
            segments=segments,
        )
        # Neither overridden
        assert rd.intervals is not None
        assert rd.segments is not None
        assert rd.intervals[0].type == "warmup"
        assert rd.segments[0].segment_type == "steady"

    def test_neither_present_creates_default_segment(self) -> None:
        """Empty RunDetails gets a default 'steady' segment via _ensure_segments."""
        rd = RunDetails(run_type="easy")
        assert rd.segments is not None
        assert len(rd.segments) == 1
        assert rd.segments[0].segment_type == "steady"
        # Intervals are auto-derived from the default segment
        assert rd.intervals is not None


class TestEnsureSegmentsValidator:
    """Test _ensure_segments and _compute_top_level_from_segments validators (#162)."""

    def test_top_level_creates_segment(self) -> None:
        """Top-level fields are migrated to a 'steady' segment."""
        rd = RunDetails(
            run_type="easy",
            target_duration_minutes=45,
            target_pace_min="5:30",
            target_pace_max="6:00",
            target_hr_min=130,
            target_hr_max=150,
        )
        assert rd.segments is not None
        assert len(rd.segments) == 1
        seg = rd.segments[0]
        assert seg.segment_type == "steady"
        assert seg.target_duration_minutes == 45.0
        assert seg.target_pace_min == "5:30"
        assert seg.target_pace_max == "6:00"
        assert seg.target_hr_min == 130
        assert seg.target_hr_max == 150

    def test_explicit_segments_preserved(self) -> None:
        """Explicitly set segments are not overwritten."""
        rd = RunDetails(
            run_type="intervals",
            segments=[
                Segment(position=0, segment_type="warmup", target_duration_minutes=10.0),
                Segment(position=1, segment_type="work", target_duration_minutes=3.0, repeats=4),
                Segment(position=2, segment_type="cooldown", target_duration_minutes=10.0),
            ],
        )
        assert rd.segments is not None
        assert len(rd.segments) == 3
        assert rd.segments[1].repeats == 4

    def test_compute_top_level_single_segment(self) -> None:
        """Single segment: top-level fields are copied from the segment."""
        rd = RunDetails(
            run_type="easy",
            segments=[
                Segment(
                    position=0,
                    segment_type="steady",
                    target_duration_minutes=50.0,
                    target_pace_min="5:30",
                    target_pace_max="6:00",
                    target_hr_min=130,
                    target_hr_max=150,
                ),
            ],
        )
        assert rd.target_duration_minutes == 50
        assert rd.target_pace_min == "5:30"
        assert rd.target_pace_max == "6:00"
        assert rd.target_hr_min == 130
        assert rd.target_hr_max == 150

    def test_compute_top_level_multi_segment_sums_duration(self) -> None:
        """Multiple segments: duration is summed (with repeats), pace/HR set to None."""
        rd = RunDetails(
            run_type="intervals",
            segments=[
                Segment(position=0, segment_type="warmup", target_duration_minutes=10.0),
                Segment(position=1, segment_type="work", target_duration_minutes=3.0, repeats=4),
                Segment(position=2, segment_type="cooldown", target_duration_minutes=10.0),
            ],
        )
        # 10 + (3×4) + 10 = 32
        assert rd.target_duration_minutes == 32
        assert rd.target_pace_min is None
        assert rd.target_pace_max is None
        assert rd.target_hr_min is None
        assert rd.target_hr_max is None

    def test_empty_run_details_gets_default_segment(self) -> None:
        """RunDetails without any data gets a minimal 'steady' segment."""
        rd = RunDetails(run_type="easy")
        assert rd.segments is not None
        assert len(rd.segments) == 1
        assert rd.segments[0].segment_type == "steady"
        assert rd.segments[0].target_duration_minutes is None

    def test_intervals_still_converted_to_segments(self) -> None:
        """Intervals are converted to segments first, then _ensure_segments is a no-op."""
        rd = RunDetails(
            run_type="intervals",
            intervals=[
                RunInterval(type="warmup", duration_minutes=10.0),
                RunInterval(type="work", duration_minutes=3.0, repeats=4),
            ],
        )
        assert rd.segments is not None
        assert len(rd.segments) == 2
        # Top-level duration computed from segments
        # 10 + (3×4) = 22
        assert rd.target_duration_minutes == 22

    def test_single_segment_below_5_min_clears_duration(self) -> None:
        """Duration below 5 minutes is cleared to None (respects RunDetails field constraint)."""
        rd = RunDetails(
            run_type="easy",
            segments=[
                Segment(position=0, segment_type="steady", target_duration_minutes=3.0),
            ],
        )
        # 3 min < 5 min threshold → target_duration_minutes set to None
        assert rd.target_duration_minutes is None
        # But segment still retains its original value
        assert rd.segments is not None
        assert rd.segments[0].target_duration_minutes == 3.0


class TestNewSegmentFields:
    """Test notes, exercise_name, target_distance_km fields (#140)."""

    # --- Defaults ---

    def test_new_fields_default_to_none(self) -> None:
        seg = Segment(position=0, segment_type="work")
        assert seg.notes is None
        assert seg.exercise_name is None
        assert seg.target_distance_km is None

    # --- notes ---

    def test_notes_valid(self) -> None:
        seg = Segment(position=0, segment_type="drills", notes="Knie hoch, Oberkörper aufrecht")
        assert seg.notes == "Knie hoch, Oberkörper aufrecht"

    def test_notes_max_length(self) -> None:
        seg = Segment(position=0, segment_type="work", notes="x" * 500)
        assert seg.notes is not None
        assert len(seg.notes) == 500

    def test_notes_too_long_rejected(self) -> None:
        with pytest.raises(ValueError):
            Segment(position=0, segment_type="work", notes="x" * 501)

    # --- exercise_name ---

    def test_exercise_name_valid(self) -> None:
        seg = Segment(position=0, segment_type="drills", exercise_name="Kniehebelauf")
        assert seg.exercise_name == "Kniehebelauf"

    def test_exercise_name_max_length(self) -> None:
        seg = Segment(position=0, segment_type="work", exercise_name="A" * 100)
        assert seg.exercise_name is not None
        assert len(seg.exercise_name) == 100

    def test_exercise_name_too_long_rejected(self) -> None:
        with pytest.raises(ValueError):
            Segment(position=0, segment_type="work", exercise_name="A" * 101)

    # --- target_distance_km ---

    def test_target_distance_km_valid(self) -> None:
        seg = Segment(position=0, segment_type="work", target_distance_km=0.4)
        assert seg.target_distance_km == 0.4

    def test_target_distance_km_zero_rejected(self) -> None:
        with pytest.raises(ValueError):
            Segment(position=0, segment_type="work", target_distance_km=0)

    def test_target_distance_km_negative_rejected(self) -> None:
        with pytest.raises(ValueError):
            Segment(position=0, segment_type="work", target_distance_km=-1.0)

    def test_target_distance_km_above_100_rejected(self) -> None:
        with pytest.raises(ValueError):
            Segment(position=0, segment_type="work", target_distance_km=101)

    def test_target_distance_km_max_boundary(self) -> None:
        seg = Segment(position=0, segment_type="steady", target_distance_km=100.0)
        assert seg.target_distance_km == 100.0

    # --- Combined fields ---

    def test_all_new_fields_together(self) -> None:
        seg = Segment(
            position=0,
            segment_type="drills",
            target_duration_minutes=2.0,
            target_distance_km=0.2,
            notes="Bergauf, dynamisch",
            exercise_name="Skippings",
        )
        assert seg.notes == "Bergauf, dynamisch"
        assert seg.exercise_name == "Skippings"
        assert seg.target_distance_km == 0.2
        assert seg.target_duration_minutes == 2.0


class TestLapsToTemplateSegmentsDistance:
    """Test that laps_to_template_segments derives target_distance_km (#140)."""

    def test_derives_target_distance_from_actual(self) -> None:
        laps = [
            LapResponse(
                lap_number=1,
                duration_seconds=180,
                duration_formatted="3:00",
                distance_km=0.85,
                pace_formatted="3:32",
                suggested_type="work",
            ),
        ]
        segments = laps_to_template_segments(laps)
        seg = segments[0]
        assert seg.target_distance_km == 0.85
        assert seg.target_duration_minutes == 3.0

    def test_no_distance_no_target_distance(self) -> None:
        laps = [
            LapResponse(
                lap_number=1,
                duration_seconds=300,
                duration_formatted="5:00",
                suggested_type="steady",
            ),
        ]
        segments = laps_to_template_segments(laps)
        assert segments[0].target_distance_km is None

    def test_zero_distance_no_target_distance(self) -> None:
        laps = [
            LapResponse(
                lap_number=1,
                duration_seconds=300,
                duration_formatted="5:00",
                distance_km=0.0,
                suggested_type="rest",
            ),
        ]
        segments = laps_to_template_segments(laps)
        assert segments[0].target_distance_km is None

    def test_over_100km_no_target_distance(self) -> None:
        laps = [
            LapResponse(
                lap_number=1,
                duration_seconds=36000,
                duration_formatted="600:00",
                distance_km=101.0,
                suggested_type="steady",
            ),
        ]
        segments = laps_to_template_segments(laps)
        assert segments[0].target_distance_km is None


class TestRunIntervalNewFields:
    """Test RunInterval with notes, exercise_name, distance_km (#141)."""

    def test_interval_with_distance_instead_of_duration(self) -> None:
        interval = RunInterval(type="work", distance_km=0.4, repeats=5)
        assert interval.duration_minutes is None
        assert interval.distance_km == 0.4
        assert interval.repeats == 5

    def test_interval_with_both_duration_and_distance(self) -> None:
        interval = RunInterval(type="work", duration_minutes=3.0, distance_km=0.8)
        assert interval.duration_minutes == 3.0
        assert interval.distance_km == 0.8

    def test_interval_without_duration_or_distance_fails(self) -> None:
        with pytest.raises(ValueError, match="duration_minutes oder distance_km"):
            RunInterval(type="work")

    def test_interval_with_notes(self) -> None:
        interval = RunInterval(type="work", duration_minutes=3.0, notes="bergauf")
        assert interval.notes == "bergauf"

    def test_interval_with_exercise_name(self) -> None:
        interval = RunInterval(
            type="drills",
            duration_minutes=1.0,
            exercise_name="Kniehebelauf",
            notes="Fokus auf Kniehub",
        )
        assert interval.exercise_name == "Kniehebelauf"
        assert interval.notes == "Fokus auf Kniehub"

    def test_conversion_roundtrip_with_new_fields(self) -> None:
        """RunInterval → Segment → RunInterval preserves new fields."""
        interval = RunInterval(
            type="drills",
            distance_km=0.05,
            notes="locker",
            exercise_name="Anfersen",
            repeats=2,
        )
        seg = run_interval_to_segment(interval, position=3)
        assert seg.segment_type == "drills"
        assert seg.target_distance_km == 0.05
        assert seg.target_duration_minutes is None
        assert seg.notes == "locker"
        assert seg.exercise_name == "Anfersen"
        assert seg.repeats == 2

        # Round-trip back
        intervals_back = segments_to_intervals([seg])
        assert len(intervals_back) == 1
        iv = intervals_back[0]
        assert iv.type == "drills"
        assert iv.distance_km == 0.05
        assert iv.duration_minutes is None
        assert iv.notes == "locker"
        assert iv.exercise_name == "Anfersen"

    def test_conversion_roundtrip_duration_only(self) -> None:
        """Duration-only interval roundtrips correctly."""
        interval = RunInterval(type="work", duration_minutes=3.0, notes="letzte 2 Vollgas")
        seg = run_interval_to_segment(interval)
        assert seg.target_duration_minutes == 3.0
        assert seg.target_distance_km is None
        assert seg.notes == "letzte 2 Vollgas"

        intervals_back = segments_to_intervals([seg])
        assert intervals_back[0].duration_minutes == 3.0
        assert intervals_back[0].distance_km is None
        assert intervals_back[0].notes == "letzte 2 Vollgas"

    def test_intervals_to_segments_preserves_new_fields(self) -> None:
        """intervals_to_segments maps notes, exercise_name, distance_km."""
        intervals = [
            RunInterval(type="warmup", duration_minutes=10),
            RunInterval(
                type="drills",
                distance_km=0.03,
                exercise_name="Skippings",
                notes="schnell",
                repeats=3,
            ),
            RunInterval(type="cooldown", duration_minutes=5),
        ]
        segments = intervals_to_segments(intervals)
        assert len(segments) == 3
        assert segments[1].exercise_name == "Skippings"
        assert segments[1].notes == "schnell"
        assert segments[1].target_distance_km == 0.03
        assert segments[1].target_duration_minutes is None

    def test_run_details_auto_derives_segments_with_new_fields(self) -> None:
        """RunDetails model_validator auto-creates segments from intervals."""
        rd = RunDetails(
            run_type="intervals",
            intervals=[
                RunInterval(type="warmup", duration_minutes=10),
                RunInterval(
                    type="work",
                    distance_km=0.4,
                    notes="400m Wiederholungen",
                    repeats=6,
                ),
            ],
        )
        assert rd.segments is not None
        assert len(rd.segments) == 2
        assert rd.segments[1].target_distance_km == 0.4
        assert rd.segments[1].notes == "400m Wiederholungen"
        assert rd.segments[1].repeats == 6
