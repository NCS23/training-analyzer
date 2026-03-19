"""FIT Workout File Export Service.

Konvertiert Session-Templates (RunDetails mit Segmenten) in das Garmin FIT
Workout-Format fuer den Import in HealthFit / Apple Watch / Garmin-Uhren.

Teil von Issue #38 (E07-S02: Workout als FIT exportieren).
Bugfix #343: target_value=0, Repeat-Struktur, Step-Namen, Warmup/Cooldown OPEN.
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

# Segment-Types die immer target_type=OPEN bekommen (kein Pace/HR-Zwang)
_OPEN_TARGET_TYPES = frozenset({"warmup", "cooldown"})

# Segment-Types die als Recovery in Repeat-Bloecken erkannt werden
_RECOVERY_TYPES = frozenset({"recovery_jog", "rest"})

# Deutsche Step-Namen fuer lesbare Anzeige in HealthFit / Apple Watch
_SEGMENT_DISPLAY_NAMES: dict[str, str] = {
    "warmup": "Einlaufen",
    "cooldown": "Auslaufen",
    "steady": "Dauerlauf",
    "work": "Intervall",
    "recovery_jog": "Trabpause",
    "rest": "Gehpause",
    "strides": "Steigerungen",
    "drills": "Lauf-ABC",
    "pace_building": "Temposteigerung",
    "tempo_block": "Tempoblock",
}

# fit-tool Einheiten-Konstanten (empirisch verifiziert)
_MS_PER_MIN = 60_000.0  # Millisekunden pro Minute
_DIST_PER_KM = 100.0  # fit-tool duration_distance: 100 Einheiten = 1km
_MPS_SCALE = 1000  # fit-tool Speed-Skalierung (m/s x 1000)
_HR_OFFSET = 100  # FIT Custom HR Offset (BPM + 100)


def pace_to_speed_mps(pace_str: str) -> float:
    """Konvertiert Pace-String 'M:SS' (min/km) zu Geschwindigkeit in m/s.

    Beispiel: '5:30' -> 1000 / 330 ~ 3.03 m/s
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


def _generate_step_name(segment: Segment) -> str:
    """Generiert einen lesbaren deutschen Step-Namen fuer HealthFit-Anzeige.

    Priorisiert notes > generierter Name mit Ziel-Info > Segment-Type.
    """
    if segment.notes:
        return segment.notes[:50]

    base = _SEGMENT_DISPLAY_NAMES.get(segment.segment_type, segment.segment_type)

    # Ziel-Info fuer Work/Steady/Strides anhaengen
    if segment.segment_type in ("work", "steady", "strides", "tempo_block", "pace_building"):
        suffix_parts: list[str] = []

        if segment.target_distance_km:
            dist = segment.target_distance_km
            suffix_parts.append(f"{dist:g}km" if dist != int(dist) else f"{int(dist)}km")
        elif segment.target_duration_minutes:
            mins = segment.target_duration_minutes
            suffix_parts.append(f"{int(mins)}min" if mins == int(mins) else f"{mins}min")

        if segment.target_pace_min and segment.target_pace_max:
            suffix_parts.append(f"@ {segment.target_pace_min}-{segment.target_pace_max}")
        elif segment.target_pace_min:
            suffix_parts.append(f"@ {segment.target_pace_min}")

        if suffix_parts:
            base = f"{base} {' '.join(suffix_parts)}"

    return base[:50]


def _set_target(step: WorkoutStepMessage, segment: Segment) -> None:
    """Setzt Target-Felder auf dem WorkoutStep.

    WICHTIG: target_value = 0 MUSS gesetzt werden fuer Custom-Range-Targets,
    sonst ignoriert HealthFit die custom_target_*-Werte komplett.

    Warmup/Cooldown bekommen immer OPEN (Standard-Konvention).
    Prioritaet: Pace > HR > Open.
    """
    # Warmup/Cooldown immer OPEN (kein Pace/HR-Zwang)
    if segment.segment_type in _OPEN_TARGET_TYPES:
        step.target_type = WorkoutStepTarget.OPEN
        step.target_value = 0
        return

    # Pace-Target (Speed)
    if segment.target_pace_min or segment.target_pace_max:
        step.target_type = WorkoutStepTarget.SPEED
        step.target_value = 0  # 0 = Custom Range (PFLICHT!)
        # Invertiert: schnellere Pace (niedrigerer Wert) = hoeherer Speed
        if segment.target_pace_max:  # langsamere Pace -> niedrigerer Speed = low
            step.custom_target_speed_low = int(
                pace_to_speed_mps(segment.target_pace_max) * _MPS_SCALE
            )
        if segment.target_pace_min:  # schnellere Pace -> hoeherer Speed = high
            step.custom_target_speed_high = int(
                pace_to_speed_mps(segment.target_pace_min) * _MPS_SCALE
            )
        return

    # HR-Target
    if segment.target_hr_min or segment.target_hr_max:
        step.target_type = WorkoutStepTarget.HEART_RATE
        step.target_value = 0  # 0 = Custom Range (PFLICHT!)
        if segment.target_hr_min:
            step.custom_target_heart_rate_low = segment.target_hr_min + _HR_OFFSET
        if segment.target_hr_max:
            step.custom_target_heart_rate_high = segment.target_hr_max + _HR_OFFSET
        return

    # Kein Target → OPEN
    step.target_type = WorkoutStepTarget.OPEN
    step.target_value = 0


def _build_workout_step(
    segment: Segment,
    message_index: int,
) -> WorkoutStepMessage:
    """Konvertiert ein einzelnes Segment zu einem FIT WorkoutStepMessage."""
    step = WorkoutStepMessage()
    step.message_index = message_index
    step.workout_step_name = _generate_step_name(segment)
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

    # Target (mit target_value=0 fuer Custom Ranges)
    _set_target(step, segment)

    return step


def _build_recovery_step(
    message_index: int,
    recovery_segment: Segment | None = None,
) -> WorkoutStepMessage:
    """Erstellt einen Recovery-Step fuer Repeat-Bloecke.

    Verwendet Daten aus dem Recovery-Segment wenn vorhanden,
    sonst OPEN Duration + OPEN Target als Fallback.
    """
    if recovery_segment:
        return _build_workout_step(recovery_segment, message_index)

    # Fallback: Auto-generierter Recovery-Step
    step = WorkoutStepMessage()
    step.message_index = message_index
    step.workout_step_name = "Trabpause"
    step.intensity = Intensity.RECOVERY
    step.duration_type = WorkoutStepDuration.OPEN
    step.target_type = WorkoutStepTarget.OPEN
    step.target_value = 0
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

    Repeat-Logik:
    - Segment mit repeats > 1 erzeugt einen Repeat-Block:
      [Work-Step, Recovery-Step, Repeat-Step]
    - Wenn das naechste Segment ein Recovery-Typ ist (recovery_jog/rest),
      wird es als Recovery innerhalb des Repeat-Blocks verwendet und
      im Hauptloop uebersprungen.
    - Sonst wird ein Auto-Recovery (OPEN) eingefuegt.

    Segmente mit repeats == 1 werden direkt konvertiert.
    """
    steps: list[WorkoutStepMessage] = []
    step_index = 0
    seg_index = 0

    while seg_index < len(segments):
        segment = segments[seg_index]

        if segment.repeats > 1:
            # Work-Step
            work_step = _build_workout_step(segment, message_index=step_index)
            steps.append(work_step)
            repeat_from = step_index
            step_index += 1

            # Recovery-Step: naechstes Segment als Recovery nutzen wenn moeglich
            next_seg = segments[seg_index + 1] if seg_index + 1 < len(segments) else None
            if next_seg and next_seg.segment_type in _RECOVERY_TYPES:
                recovery_step = _build_recovery_step(step_index, recovery_segment=next_seg)
                seg_index += 1  # Recovery-Segment im Hauptloop ueberspringen
            else:
                recovery_step = _build_recovery_step(step_index)

            steps.append(recovery_step)
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

        seg_index += 1

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
