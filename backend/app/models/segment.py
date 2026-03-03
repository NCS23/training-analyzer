"""Unified Segment Model for planned and actual run segments.

Single model that can express both Soll (planned) and Ist (actual) data,
enabling template-based planning and Soll/Ist comparison.

Part of Epic #133 (Einheitliches Segment-Modell).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

from app.models.taxonomy import SEGMENT_TYPE_MIGRATION, SEGMENT_TYPE_REGEX

if TYPE_CHECKING:
    from app.models.session import LapResponse
    from app.models.weekly_plan import RunInterval


class Segment(BaseModel):
    """Einheitliches Modell fuer geplante und tatsaechliche Lauf-Abschnitte.

    Soll-Felder (target_*) werden bei Templates und Wochenplan gefuellt.
    Ist-Felder (actual_*) werden nach Session-Upload gefuellt.
    Bei Soll/Ist-Vergleich sind beide Seiten vorhanden.
    """

    # Identitaet
    position: int = 0
    segment_type: str = Field(..., pattern=SEGMENT_TYPE_REGEX)

    # Planung (Soll) — gefuellt bei Templates + Wochenplan
    target_duration_minutes: Optional[float] = Field(default=None, gt=0, le=180)
    target_distance_km: Optional[float] = Field(default=None, gt=0, le=100)
    target_pace_min: Optional[str] = Field(default=None, max_length=10)
    target_pace_max: Optional[str] = Field(default=None, max_length=10)
    target_hr_min: Optional[int] = Field(default=None, ge=60, le=220)
    target_hr_max: Optional[int] = Field(default=None, ge=60, le=220)
    repeats: int = Field(default=1, ge=1, le=50)

    # Anreicherung — Freitext-Notizen und optionale Uebungsreferenz
    notes: Optional[str] = Field(default=None, max_length=500)
    exercise_name: Optional[str] = Field(default=None, max_length=100)

    # Ist-Daten — gefuellt nach Session-Upload
    actual_duration_seconds: Optional[float] = None
    actual_distance_km: Optional[float] = None
    actual_pace_formatted: Optional[str] = None
    actual_hr_avg: Optional[int] = None
    actual_hr_max: Optional[int] = None
    actual_hr_min: Optional[int] = None
    actual_cadence_spm: Optional[int] = None

    # Timing (fuer UI-Visualisierung, nur bei Ist)
    start_seconds: Optional[float] = None
    end_seconds: Optional[float] = None

    # Klassifizierung (nur bei Ist)
    suggested_type: Optional[str] = None
    confidence: Optional[str] = None
    user_override: Optional[str] = None

    def expand(self) -> list[Segment]:
        """Expandiert repeats zu einzelnen Segmenten (fuer Soll/Ist-Matching).

        Ein Segment mit repeats=4 wird zu 4 Work-Segmenten + 3 Recovery-Jog-Segmenten.
        Segmente mit repeats=1 werden unveraendert zurueckgegeben.
        """
        if self.repeats <= 1:
            return [self.model_copy(update={"repeats": 1})]

        result: list[Segment] = []
        for i in range(self.repeats):
            result.append(
                self.model_copy(
                    update={
                        "position": self.position + i * 2,
                        "repeats": 1,
                    }
                )
            )
            if i < self.repeats - 1:
                result.append(
                    Segment(
                        position=self.position + i * 2 + 1,
                        segment_type="recovery_jog",
                        target_duration_minutes=None,
                    )
                )
        return result


# --- Konvertierungsfunktionen ---


def run_interval_to_segment(
    interval: RunInterval,
    position: int = 0,
) -> Segment:
    """Konvertiert RunInterval zu Segment (nur Soll-Felder)."""
    return Segment(
        position=position,
        segment_type=interval.type,
        target_duration_minutes=interval.duration_minutes,
        target_pace_min=interval.target_pace_min,
        target_pace_max=interval.target_pace_max,
        target_hr_min=interval.target_hr_min,
        target_hr_max=interval.target_hr_max,
        repeats=interval.repeats,
    )


def lap_to_segment(lap: LapResponse) -> Segment:
    """Konvertiert LapResponse zu Segment (nur Ist-Felder)."""
    # Resolve effective segment type (user_override > suggested_type)
    raw_type = lap.user_override or lap.suggested_type
    resolved_type = SEGMENT_TYPE_MIGRATION.get(raw_type, raw_type) if raw_type else "steady"

    return Segment(
        position=lap.lap_number - 1,  # LapResponse is 1-indexed, Segment is 0-indexed
        segment_type=resolved_type,
        actual_duration_seconds=float(lap.duration_seconds),
        actual_distance_km=lap.distance_km,
        actual_pace_formatted=lap.pace_formatted,
        actual_hr_avg=lap.avg_hr_bpm,
        actual_hr_max=lap.max_hr_bpm,
        actual_hr_min=lap.min_hr_bpm,
        actual_cadence_spm=lap.avg_cadence_spm,
        start_seconds=lap.start_seconds,
        end_seconds=lap.end_seconds,
        suggested_type=lap.suggested_type,
        confidence=lap.confidence,
        user_override=lap.user_override,
    )


def segment_to_lap_response(segment: Segment, lap_number: int = 1) -> LapResponse:
    """Konvertiert Segment zu LapResponse (fuer bestehende API-Konsumenten)."""
    from app.models.session import LapResponse as LapResponseCls

    duration_sec = int(segment.actual_duration_seconds) if segment.actual_duration_seconds else 0

    minutes = duration_sec // 60
    seconds = duration_sec % 60
    duration_formatted = f"{minutes}:{seconds:02d}"

    pace_min_per_km: Optional[float] = None
    if segment.actual_distance_km and segment.actual_distance_km > 0 and duration_sec > 0:
        pace_min_per_km = round((duration_sec / 60) / segment.actual_distance_km, 2)

    return LapResponseCls(
        lap_number=lap_number,
        duration_seconds=duration_sec,
        duration_formatted=duration_formatted,
        distance_km=segment.actual_distance_km,
        pace_min_per_km=pace_min_per_km,
        pace_formatted=segment.actual_pace_formatted,
        avg_hr_bpm=segment.actual_hr_avg,
        max_hr_bpm=segment.actual_hr_max,
        min_hr_bpm=segment.actual_hr_min,
        avg_cadence_spm=segment.actual_cadence_spm,
        suggested_type=segment.suggested_type,
        confidence=segment.confidence,
        user_override=segment.user_override,
        start_seconds=segment.start_seconds,
        end_seconds=segment.end_seconds,
    )


def intervals_to_segments(intervals: list[RunInterval]) -> list[Segment]:
    """Konvertiert eine Liste von RunIntervals zu Segments mit korrekten Positionen."""
    segments: list[Segment] = []
    for pos, interval in enumerate(intervals):
        segments.append(run_interval_to_segment(interval, position=pos))
    return segments


def laps_to_segments(laps: list[LapResponse]) -> list[Segment]:
    """Konvertiert eine Liste von LapResponses zu Segments."""
    return [lap_to_segment(lap) for lap in laps]


def segments_to_intervals(segments: list[Segment]) -> list[RunInterval]:
    """Konvertiert Segments zurueck zu RunIntervals (Backward-Compat).

    Bestimmt duration_minutes aus target_duration_minutes (Soll) oder
    actual_duration_seconds (Ist), mit Fallback auf 1.0 Minute.
    """
    from app.models.weekly_plan import RunInterval as RunIntervalCls

    result = []
    for seg in segments:
        duration_min = seg.target_duration_minutes
        if duration_min is None and seg.actual_duration_seconds:
            duration_min = round(seg.actual_duration_seconds / 60, 1)
        if duration_min is None or duration_min <= 0:
            duration_min = 1.0
        duration_min = min(duration_min, 180.0)

        result.append(
            RunIntervalCls(
                type=seg.segment_type,
                duration_minutes=duration_min,
                target_pace_min=seg.target_pace_min,
                target_pace_max=seg.target_pace_max,
                target_hr_min=seg.target_hr_min,
                target_hr_max=seg.target_hr_max,
                repeats=seg.repeats,
            )
        )
    return result


def laps_to_template_segments(laps: list[LapResponse]) -> list[Segment]:
    """Konvertiert Laps zu Template-Segmenten mit Ist-als-Soll-Ableitung.

    Wird beim Erstellen von Templates aus Sessions verwendet.
    Ist-Daten (actual_*) werden als Soll-Referenz (target_*) uebernommen.
    """
    segments = laps_to_segments(laps)
    result: list[Segment] = []
    for seg in segments:
        updates: dict[str, object] = {}
        if seg.actual_duration_seconds and 0 < seg.actual_duration_seconds / 60 <= 180:
            updates["target_duration_minutes"] = round(seg.actual_duration_seconds / 60, 1)
        if seg.actual_distance_km and 0 < seg.actual_distance_km <= 100:
            updates["target_distance_km"] = round(seg.actual_distance_km, 2)
        if seg.actual_pace_formatted:
            updates["target_pace_min"] = seg.actual_pace_formatted
        result.append(seg.model_copy(update=updates) if updates else seg)
    return result
