"""Soll/Ist Segment-Matching Service (Issue #138).

Matcht geplante Segmente mit tatsaechlichen Laps und berechnet Deltas.
"""

from __future__ import annotations

from itertools import zip_longest

from app.models.segment import (
    ComparisonResponse,
    MatchedSegment,
    Segment,
    SegmentDelta,
)


def pace_str_to_seconds(pace: str | None) -> int | None:
    """Konvertiert Pace-String '5:30' zu Sekunden (330)."""
    if not pace:
        return None
    try:
        parts = pace.strip().split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except (ValueError, IndexError):
        return None


def _seconds_to_pace_str(seconds: int) -> str:
    """Konvertiert Sekunden zu Pace-String mit Vorzeichen ('+0:12' / '-0:05')."""
    sign = "+" if seconds >= 0 else "-"
    abs_sec = abs(seconds)
    minutes = abs_sec // 60
    secs = abs_sec % 60
    return f"{sign}{minutes}:{secs:02d}"


def _range_delta(actual: int, lo: int | None, hi: int | None) -> int | None:
    """Berechnet Abweichung eines Wertes von einer Range.

    Innerhalb [lo, hi] → 0. Darunter → negativ. Darüber → positiv.
    Falls nur eine Grenze gesetzt ist, wird direkte Differenz berechnet.
    """
    if lo is not None and hi is not None:
        if actual < lo:
            return actual - lo
        if actual > hi:
            return actual - hi
        return 0
    if lo is not None:
        return actual - lo
    if hi is not None:
        return actual - hi
    return None


def _pace_delta(planned: Segment, actual: Segment) -> tuple[int | None, str | None]:
    """Berechnet Pace-Delta (Sekunden + formatiert)."""
    actual_sec = pace_str_to_seconds(actual.actual_pace_formatted)
    if actual_sec is None:
        return None, None

    target_min = pace_str_to_seconds(planned.target_pace_min)
    target_max = pace_str_to_seconds(planned.target_pace_max)
    delta = _range_delta(actual_sec, target_min, target_max)

    if delta is None:
        return None, None
    return delta, _seconds_to_pace_str(delta)


def _hr_delta(planned: Segment, actual: Segment) -> int | None:
    """Berechnet HR-Delta (Schläge)."""
    if actual.actual_hr_avg is None:
        return None
    return _range_delta(actual.actual_hr_avg, planned.target_hr_min, planned.target_hr_max)


def _compute_delta(planned: Segment, actual: Segment) -> SegmentDelta:
    """Berechnet Deltas zwischen Soll- und Ist-Segment."""
    pace_delta_sec, pace_delta_fmt = _pace_delta(planned, actual)

    dur_delta: float | None = None
    if actual.actual_duration_seconds is not None and planned.target_duration_minutes is not None:
        dur_delta = round(actual.actual_duration_seconds - planned.target_duration_minutes * 60, 1)

    dist_delta: float | None = None
    if actual.actual_distance_km is not None and planned.target_distance_km is not None:
        dist_delta = round(actual.actual_distance_km - planned.target_distance_km, 3)

    return SegmentDelta(
        pace_delta_seconds=pace_delta_sec,
        pace_delta_formatted=pace_delta_fmt,
        hr_avg_delta=_hr_delta(planned, actual),
        duration_delta_seconds=dur_delta,
        distance_delta_km=dist_delta,
    )


def match_segments(
    planned: list[Segment],
    actual: list[Segment],
) -> list[MatchedSegment]:
    """Matcht geplante Segmente mit Ist-Segmenten positionsbasiert.

    Geplante Segmente werden zuerst expandiert (repeats aufloesen).
    """
    expanded = []
    for seg in planned:
        expanded.extend(seg.expand())

    result: list[MatchedSegment] = []
    for i, (p, a) in enumerate(zip_longest(expanded, actual)):
        if p is not None and a is not None:
            result.append(
                MatchedSegment(
                    position=i,
                    segment_type=a.segment_type,
                    match_quality="matched",
                    planned=p,
                    actual=a,
                    delta=_compute_delta(p, a),
                )
            )
        elif p is not None:
            result.append(
                MatchedSegment(
                    position=i,
                    segment_type=p.segment_type,
                    match_quality="unmatched_planned",
                    planned=p,
                )
            )
        elif a is not None:
            result.append(
                MatchedSegment(
                    position=i,
                    segment_type=a.segment_type,
                    match_quality="unmatched_actual",
                    actual=a,
                )
            )

    return result


def build_comparison(
    planned_segments: list[Segment],
    actual_segments: list[Segment],
    planned_entry_id: int,
    planned_run_type: str | None = None,
) -> ComparisonResponse:
    """Erstellt eine vollstaendige ComparisonResponse."""
    expanded_count = sum(len(seg.expand()) for seg in planned_segments)
    matched = match_segments(planned_segments, actual_segments)

    return ComparisonResponse(
        planned_entry_id=planned_entry_id,
        planned_run_type=planned_run_type,
        segments=matched,
        has_mismatch=expanded_count != len(actual_segments),
        planned_count=expanded_count,
        actual_count=len(actual_segments),
    )
