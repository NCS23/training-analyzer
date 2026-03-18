"""FIT Workout File Export Service.

Konvertiert Session-Templates (RunDetails mit Segmenten) in das Garmin FIT
Workout-Format fuer den Import in HealthFit / Apple Watch / Garmin-Uhren.

Teil von Issue #38 (E07-S02: Workout als FIT exportieren).
"""

from __future__ import annotations

from fit_tool.fit_file_builder import FitFileBuilder  # type: ignore[import-untyped]
from fit_tool.profile.messages.file_id_message import FileIdMessage  # type: ignore[import-untyped]
from fit_tool.profile.messages.workout_message import WorkoutMessage  # type: ignore[import-untyped]
from fit_tool.profile.messages.workout_step_message import (  # type: ignore[import-untyped]
    WorkoutStepMessage,
)
from fit_tool.profile.profile_type import (  # type: ignore[import-untyped]
    FileType,
    Intensity,
    Manufacturer,
    Sport,
    WorkoutStepDuration,
    WorkoutStepTarget,
)

from app.models.segment import Segment

# Segment-Type → FIT Intensity Mapping
SEGMENT_TO_INTENSITY: dict[str, Intensity] = {
    "warmup": Intensity.WARMUP,
    "cooldown": Intensity.COOLDOWN,
    "work": Intensity.ACTIVE,
    "steady": Intensity.ACTIVE,
    "strides": Intensity.ACTIVE,
    "drills": Intensity.ACTIVE,
    "pace_building": Intensity.ACTIVE,
    "tempo_block": Intensity.ACTIVE,
    "recovery_jog": Intensity.RECOVERY,
    "rest": Intensity.REST,
}

# fit-tool Einheiten-Konstanten (empirisch verifiziert)
_MS_PER_MIN = 60_000.0  # Millisekunden pro Minute
_DIST_PER_KM = 100.0  # fit-tool duration_distance: 100 Einheiten = 1km
_MPS_SCALE = 1000  # fit-tool Speed-Skalierung (m/s × 1000)
_HR_OFFSET = 100  # FIT Custom HR Offset (BPM + 100)


def pace_to_speed_mps(pace_str: str) -> float:
    """Konvertiert Pace-String 'M:SS' (min/km) zu Geschwindigkeit in m/s.

    Beispiel: '5:30' → 1000 / 330 ≈ 3.03 m/s
    """
    parts = pace_str.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Ungueltiges Pace-Format: '{pace_str}' (erwartet 'M:SS')")

    minutes = int(parts[0])
    seconds = int(parts[1])
    total_seconds = minutes * 60 + seconds

    if total_seconds <= 0:
        raise ValueError(f"Pace muss groesser als 0 sein: '{pace_str}'")

    return 1000.0 / total_seconds


def _build_workout_step(
    segment: Segment,
    message_index: int,
) -> WorkoutStepMessage:
    """Konvertiert ein einzelnes Segment zu einem FIT WorkoutStepMessage."""
    step = WorkoutStepMessage()
    step.message_index = message_index
    step.workout_step_name = segment.notes or segment.segment_type
    step.intensity = SEGMENT_TO_INTENSITY.get(segment.segment_type, Intensity.ACTIVE)

    # Duration: Zeit > Distanz > Open
    if segment.target_duration_minutes:
        step.duration_type = WorkoutStepDuration.TIME
        step.duration_time = segment.target_duration_minutes * _MS_PER_MIN
    elif segment.target_distance_km:
        step.duration_type = WorkoutStepDuration.DISTANCE
        step.duration_distance = segment.target_distance_km * _DIST_PER_KM
    else:
        step.duration_type = WorkoutStepDuration.OPEN

    # Target: Pace > HR > Open
    if segment.target_pace_min or segment.target_pace_max:
        step.target_type = WorkoutStepTarget.SPEED
        # Invertiert: schnellere Pace (niedrigerer Wert) = hoeherer Speed
        if segment.target_pace_max:  # langsamere Pace → niedrigerer Speed = low
            step.custom_target_speed_low = int(
                pace_to_speed_mps(segment.target_pace_max) * _MPS_SCALE
            )
        if segment.target_pace_min:  # schnellere Pace → hoeherer Speed = high
            step.custom_target_speed_high = int(
                pace_to_speed_mps(segment.target_pace_min) * _MPS_SCALE
            )
    elif segment.target_hr_min or segment.target_hr_max:
        step.target_type = WorkoutStepTarget.HEART_RATE
        if segment.target_hr_min:
            step.custom_target_heart_rate_low = segment.target_hr_min + _HR_OFFSET
        if segment.target_hr_max:
            step.custom_target_heart_rate_high = segment.target_hr_max + _HR_OFFSET
    else:
        step.target_type = WorkoutStepTarget.OPEN

    return step


def _build_repeat_step(
    message_index: int,
    repeat_from_step: int,
    repeat_count: int,
) -> WorkoutStepMessage:
    """Erstellt einen FIT Repeat-Step (Wiederholungsblock)."""
    step = WorkoutStepMessage()
    step.message_index = message_index
    step.duration_type = WorkoutStepDuration.REPEAT_UNTIL_STEPS_CMPLT
    step.duration_step = repeat_from_step
    step.target_repeat_steps = repeat_count
    return step


def segments_to_fit_steps(segments: list[Segment]) -> list[WorkoutStepMessage]:
    """Konvertiert Template-Segmente zu FIT WorkoutSteps.

    Segmente mit repeats > 1 nutzen den nativen FIT-Repeat-Mechanismus:
    1. Work-Step emittieren
    2. Recovery-Step (OPEN duration) emittieren
    3. Repeat-Step der auf 1+2 verweist

    Segmente mit repeats == 1 werden direkt konvertiert.
    """
    steps: list[WorkoutStepMessage] = []
    step_index = 0

    for segment in segments:
        if segment.repeats > 1:
            # Work-Step
            work_step = _build_workout_step(segment, message_index=step_index)
            steps.append(work_step)
            repeat_from = step_index
            step_index += 1

            # Recovery-Step (Open, damit Sportler Pause selbst bestimmt)
            recovery = WorkoutStepMessage()
            recovery.message_index = step_index
            recovery.workout_step_name = "Erholung"
            recovery.intensity = Intensity.RECOVERY
            recovery.duration_type = WorkoutStepDuration.OPEN
            recovery.target_type = WorkoutStepTarget.OPEN
            steps.append(recovery)
            step_index += 1

            # Repeat-Step
            repeat_step = _build_repeat_step(
                message_index=step_index,
                repeat_from_step=repeat_from,
                repeat_count=segment.repeats,
            )
            steps.append(repeat_step)
            step_index += 1
        else:
            steps.append(_build_workout_step(segment, message_index=step_index))
            step_index += 1

    return steps


def export_template_to_fit(
    template_name: str,
    segments: list[Segment],
) -> bytes:
    """Generiert eine vollstaendige FIT-Workout-Datei aus Template-Segmenten.

    Args:
        template_name: Name des Workouts (erscheint auf der Uhr).
        segments: Liste von Segmenten aus RunDetails.

    Returns:
        Binaere FIT-Datei als bytes.

    Raises:
        ValueError: Wenn keine Segmente vorhanden sind.
    """
    if not segments:
        raise ValueError("Keine Segmente fuer den FIT-Export vorhanden.")

    fit_steps = segments_to_fit_steps(segments)

    builder = FitFileBuilder(auto_define=True, min_string_size=50)

    # File ID
    file_id = FileIdMessage()
    file_id.type = FileType.WORKOUT
    file_id.manufacturer = Manufacturer.DEVELOPMENT.value
    builder.add(file_id)

    # Workout Header
    workout = WorkoutMessage()
    workout.workout_name = template_name[:50]  # FIT max name length
    workout.sport = Sport.RUNNING
    workout.num_valid_steps = len(fit_steps)
    builder.add(workout)

    # Steps
    for step in fit_steps:
        builder.add(step)

    fit_file = builder.build()
    return fit_file.to_bytes()
