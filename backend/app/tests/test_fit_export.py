"""Tests fuer den FIT Workout Export Service (Issue #38)."""

import pytest

# fit-tool imports fuer Assertions
from fit_tool.profile.profile_type import (  # type: ignore[import-untyped]
    Intensity,
    WorkoutStepDuration,
    WorkoutStepTarget,
)

from app.models.segment import Segment
from app.services.fit_export import (
    SEGMENT_TO_INTENSITY,
    _build_repeat_step,
    _build_workout_step,
    export_template_to_fit,
    pace_to_speed_mps,
    segments_to_fit_steps,
)

# --- pace_to_speed_mps ---


class TestPaceToSpeedMps:
    def test_standard_pace(self) -> None:
        # 5:00 min/km = 1000m / 300s = 3.333 m/s
        speed = pace_to_speed_mps("5:00")
        assert abs(speed - 3.333) < 0.01

    def test_slow_pace(self) -> None:
        # 6:00 min/km = 1000m / 360s = 2.778 m/s
        speed = pace_to_speed_mps("6:00")
        assert abs(speed - 2.778) < 0.01

    def test_fast_pace(self) -> None:
        # 4:00 min/km = 1000m / 240s = 4.167 m/s
        speed = pace_to_speed_mps("4:00")
        assert abs(speed - 4.167) < 0.01

    def test_pace_with_seconds(self) -> None:
        # 5:30 min/km = 1000m / 330s ≈ 3.030 m/s
        speed = pace_to_speed_mps("5:30")
        assert abs(speed - 3.030) < 0.01

    def test_invalid_format_raises(self) -> None:
        with pytest.raises(ValueError, match="Ungueltiges Pace-Format"):
            pace_to_speed_mps("530")

    def test_zero_pace_raises(self) -> None:
        with pytest.raises(ValueError, match="groesser als 0"):
            pace_to_speed_mps("0:00")


# --- _build_workout_step ---


class TestBuildWorkoutStep:
    def test_warmup_with_time(self) -> None:
        seg = Segment(position=0, segment_type="warmup", target_duration_minutes=10)
        step = _build_workout_step(seg, message_index=0)

        assert step.intensity == Intensity.WARMUP.value
        assert step.duration_type == WorkoutStepDuration.TIME.value
        assert step.duration_time == 600_000.0  # 10min in ms
        assert step.target_type == WorkoutStepTarget.OPEN.value

    def test_work_with_distance(self) -> None:
        seg = Segment(position=0, segment_type="work", target_distance_km=1.0)
        step = _build_workout_step(seg, message_index=0)

        assert step.intensity == Intensity.ACTIVE.value
        assert step.duration_type == WorkoutStepDuration.DISTANCE.value
        assert step.duration_distance == 100.0  # 1km in fit-tool Einheiten

    def test_cooldown_open_duration(self) -> None:
        seg = Segment(position=0, segment_type="cooldown")
        step = _build_workout_step(seg, message_index=0)

        assert step.intensity == Intensity.COOLDOWN.value
        assert step.duration_type == WorkoutStepDuration.OPEN.value

    def test_pace_target(self) -> None:
        seg = Segment(
            position=0,
            segment_type="work",
            target_distance_km=1.0,
            target_pace_min="5:00",
            target_pace_max="5:30",
        )
        step = _build_workout_step(seg, message_index=0)

        assert step.target_type == WorkoutStepTarget.SPEED.value
        # 5:30 (langsamer) → niedrigerer Speed → low
        assert step.custom_target_speed_low == int(pace_to_speed_mps("5:30") * 1000)
        # 5:00 (schneller) → hoeherer Speed → high
        assert step.custom_target_speed_high == int(pace_to_speed_mps("5:00") * 1000)

    def test_hr_target(self) -> None:
        seg = Segment(
            position=0,
            segment_type="steady",
            target_duration_minutes=30,
            target_hr_min=140,
            target_hr_max=160,
        )
        step = _build_workout_step(seg, message_index=0)

        assert step.target_type == WorkoutStepTarget.HEART_RATE.value
        assert step.custom_target_heart_rate_low == 240  # 140 + 100
        assert step.custom_target_heart_rate_high == 260  # 160 + 100

    def test_pace_takes_priority_over_hr(self) -> None:
        seg = Segment(
            position=0,
            segment_type="work",
            target_distance_km=1.0,
            target_pace_min="4:30",
            target_hr_min=150,
            target_hr_max=170,
        )
        step = _build_workout_step(seg, message_index=0)
        assert step.target_type == WorkoutStepTarget.SPEED.value

    def test_time_takes_priority_over_distance(self) -> None:
        seg = Segment(
            position=0,
            segment_type="work",
            target_duration_minutes=5,
            target_distance_km=1.0,
        )
        step = _build_workout_step(seg, message_index=0)
        assert step.duration_type == WorkoutStepDuration.TIME.value

    def test_recovery_jog_intensity(self) -> None:
        seg = Segment(position=0, segment_type="recovery_jog")
        step = _build_workout_step(seg, message_index=0)
        assert step.intensity == Intensity.RECOVERY.value

    def test_rest_intensity(self) -> None:
        seg = Segment(position=0, segment_type="rest")
        step = _build_workout_step(seg, message_index=0)
        assert step.intensity == Intensity.REST.value

    def test_message_index_set(self) -> None:
        seg = Segment(position=0, segment_type="warmup", target_duration_minutes=5)
        step = _build_workout_step(seg, message_index=7)
        assert step.message_index == 7

    def test_step_name_from_notes(self) -> None:
        seg = Segment(
            position=0,
            segment_type="work",
            target_distance_km=1.0,
            notes="Schnelle 1km",
        )
        step = _build_workout_step(seg, message_index=0)
        assert step.workout_step_name == "Schnelle 1km"

    def test_step_name_fallback_to_type(self) -> None:
        seg = Segment(position=0, segment_type="warmup", target_duration_minutes=10)
        step = _build_workout_step(seg, message_index=0)
        assert step.workout_step_name == "warmup"


# --- segments_to_fit_steps ---


class TestSegmentsToFitSteps:
    def test_simple_workout(self) -> None:
        segments = [
            Segment(position=0, segment_type="warmup", target_duration_minutes=10),
            Segment(position=1, segment_type="steady", target_duration_minutes=30),
            Segment(position=2, segment_type="cooldown", target_duration_minutes=5),
        ]
        steps = segments_to_fit_steps(segments)
        assert len(steps) == 3
        assert steps[0].intensity == Intensity.WARMUP.value
        assert steps[1].intensity == Intensity.ACTIVE.value
        assert steps[2].intensity == Intensity.COOLDOWN.value

    def test_repeats_generate_three_steps(self) -> None:
        """repeats=4 → work + recovery + repeat = 3 FIT steps."""
        segments = [
            Segment(
                position=0,
                segment_type="work",
                target_distance_km=1.0,
                repeats=4,
            ),
        ]
        steps = segments_to_fit_steps(segments)
        assert len(steps) == 3

        # Work step
        assert steps[0].intensity == Intensity.ACTIVE.value
        assert steps[0].duration_type == WorkoutStepDuration.DISTANCE.value
        assert steps[0].message_index == 0

        # Recovery step (open)
        assert steps[1].intensity == Intensity.RECOVERY.value
        assert steps[1].duration_type == WorkoutStepDuration.OPEN.value
        assert steps[1].message_index == 1

        # Repeat step
        assert steps[2].duration_type == WorkoutStepDuration.REPEAT_UNTIL_STEPS_CMPLT.value
        assert steps[2].duration_step == 0  # verweist auf work step
        assert steps[2].target_repeat_steps == 4
        assert steps[2].message_index == 2

    def test_full_interval_workout(self) -> None:
        """Warmup + 5x1km Intervalle + Cooldown."""
        segments = [
            Segment(position=0, segment_type="warmup", target_duration_minutes=10),
            Segment(
                position=1,
                segment_type="work",
                target_distance_km=1.0,
                target_pace_min="4:30",
                target_pace_max="4:50",
                repeats=5,
            ),
            Segment(position=2, segment_type="cooldown", target_duration_minutes=5),
        ]
        steps = segments_to_fit_steps(segments)

        # warmup(0) + work(1) + recovery(2) + repeat(3) + cooldown(4) = 5
        assert len(steps) == 5
        assert steps[0].intensity == Intensity.WARMUP.value
        assert steps[1].target_type == WorkoutStepTarget.SPEED.value
        assert steps[3].target_repeat_steps == 5
        assert steps[4].intensity == Intensity.COOLDOWN.value

    def test_message_indices_sequential(self) -> None:
        segments = [
            Segment(position=0, segment_type="warmup", target_duration_minutes=5),
            Segment(position=1, segment_type="work", target_distance_km=0.8, repeats=3),
            Segment(position=2, segment_type="cooldown", target_duration_minutes=5),
        ]
        steps = segments_to_fit_steps(segments)
        for i, step in enumerate(steps):
            assert step.message_index == i


# --- _build_repeat_step ---


class TestBuildRepeatStep:
    def test_repeat_step_fields(self) -> None:
        step = _build_repeat_step(message_index=5, repeat_from_step=2, repeat_count=6)
        assert step.message_index == 5
        assert step.duration_type == WorkoutStepDuration.REPEAT_UNTIL_STEPS_CMPLT.value
        assert step.duration_step == 2
        assert step.target_repeat_steps == 6


# --- export_template_to_fit ---


class TestExportTemplateToFit:
    def test_produces_bytes(self) -> None:
        segments = [
            Segment(position=0, segment_type="warmup", target_duration_minutes=10),
            Segment(position=1, segment_type="steady", target_duration_minutes=20),
            Segment(position=2, segment_type="cooldown", target_duration_minutes=5),
        ]
        data = export_template_to_fit("Easy Run", segments)
        assert isinstance(data, bytes)
        assert len(data) > 50  # FIT header allein ist ~14 bytes

    def test_empty_segments_raises(self) -> None:
        with pytest.raises(ValueError, match="Keine Segmente"):
            export_template_to_fit("Leer", [])

    def test_interval_workout_produces_valid_fit(self) -> None:
        segments = [
            Segment(position=0, segment_type="warmup", target_duration_minutes=10),
            Segment(
                position=1,
                segment_type="work",
                target_distance_km=1.0,
                target_pace_min="4:30",
                target_pace_max="5:00",
                repeats=5,
            ),
            Segment(position=2, segment_type="cooldown", target_duration_minutes=5),
        ]
        data = export_template_to_fit("5x1km Intervalle", segments)
        assert isinstance(data, bytes)
        assert len(data) > 100

    def test_name_truncated(self) -> None:
        long_name = "A" * 100
        segments = [Segment(position=0, segment_type="steady", target_duration_minutes=30)]
        # Soll nicht crashen
        data = export_template_to_fit(long_name, segments)
        assert isinstance(data, bytes)


# --- Mapping Coverage ---


class TestSegmentToIntensityMapping:
    def test_all_segment_types_mapped(self) -> None:
        """Alle kanonischen Segment-Types muessen gemappt sein."""
        from app.models.taxonomy import SEGMENT_TYPES

        for seg_type in SEGMENT_TYPES:
            assert seg_type in SEGMENT_TO_INTENSITY, (
                f"Segment-Type '{seg_type}' fehlt in SEGMENT_TO_INTENSITY"
            )
