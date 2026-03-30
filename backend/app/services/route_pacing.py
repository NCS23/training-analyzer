"""Pacing-Integration für Trainingsrouten (#548).

Verbindet die bestehende Pacing-Engine mit Routensegmenten:
Route + Segmente + Zielzeit → Pace-Ziele pro Segment unter
Berücksichtigung von Elevation, Strategie und optional Wetter.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, Field

from app.models.pacing import ElevationSegment, PacingRequest, PacingResponse
from app.models.training_route import RouteSegment, Waypoint
from app.services.pacing_strategy import generate_pacing_strategy

# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class RoutePacingRequest(BaseModel):
    """Input für die Route-Pacing-Berechnung."""

    target_time_seconds: int = Field(..., gt=0, description="Zielzeit in Sekunden")
    strategy: Literal["even", "negative", "effort_based"] = Field(
        default="even", description="Pacing-Strategie"
    )
    temperature_celsius: float | None = Field(default=None)
    wind_speed_kmh: float | None = Field(default=None, ge=0)
    humidity_percent: float | None = Field(default=None, ge=0, le=100)


class SegmentPacing(BaseModel):
    """Berechnete Pace-Ziele für ein Route-Segment."""

    segment_index: int
    segment_type: str
    start_km: float
    end_km: float
    distance_km: float
    elevation_gain_m: float
    elevation_loss_m: float
    target_pace_min: str = Field(description="Schnellste Pace (z.B. '4:50')")
    target_pace_max: str = Field(description="Langsamste Pace (z.B. '5:10')")
    target_time_seconds: int
    target_time_formatted: str
    avg_pace_sec_per_km: float
    notes: str | None = None


class RoutePacingResponse(BaseModel):
    """Ergebnis der Route-Pacing-Berechnung."""

    strategy: str
    strategy_label: str
    distance_km: float
    target_time_seconds: int
    target_time_formatted: str
    avg_pace_sec_per_km: float
    avg_pace_formatted: str
    segment_pacing: list[SegmentPacing]
    weather_notes: str | None = None
    general_notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Kern-Logik
# ---------------------------------------------------------------------------

# ±5 sec/km Toleranzband pro Segment
_PACE_BAND_SEC = 5.0


def calculate_route_pacing(
    distance_km: float,
    waypoints: list[Waypoint],
    segments: list[RouteSegment],
    request: RoutePacingRequest,
) -> RoutePacingResponse:
    """Berechnet Pace-Ziele für alle Segmente einer Route.

    1. Elevation pro km aus Waypoints extrahieren
    2. Pacing-Engine aufrufen (km-genaue Splits)
    3. Km-Splits auf Segmente mappen
    4. Pace-Ziele pro Segment aggregieren
    """
    elevation_segments = _extract_elevation_per_km(waypoints, distance_km)

    pacing_response = generate_pacing_strategy(
        PacingRequest(
            target_time_seconds=request.target_time_seconds,
            distance_km=distance_km,
            strategy=request.strategy,
            elevation_preset=None,
            elevation_segments=elevation_segments if elevation_segments else None,
            temperature_celsius=request.temperature_celsius,
            wind_speed_kmh=request.wind_speed_kmh,
            humidity_percent=request.humidity_percent,
            goal_id=None,
        )
    )

    segment_pacing = _map_splits_to_segments(segments, pacing_response)

    weather_notes = None
    if pacing_response.weather_adjustment:
        weather_notes = pacing_response.weather_adjustment.description

    return RoutePacingResponse(
        strategy=pacing_response.strategy,
        strategy_label=pacing_response.strategy_label,
        distance_km=pacing_response.distance_km,
        target_time_seconds=pacing_response.target_time_seconds,
        target_time_formatted=pacing_response.target_time_formatted,
        avg_pace_sec_per_km=pacing_response.avg_pace_sec_per_km,
        avg_pace_formatted=pacing_response.avg_pace_formatted,
        segment_pacing=segment_pacing,
        weather_notes=weather_notes,
        general_notes=pacing_response.notes,
    )


# ---------------------------------------------------------------------------
# Elevation aus Waypoints extrahieren
# ---------------------------------------------------------------------------


def _extract_elevation_per_km(
    waypoints: list[Waypoint], total_distance_km: float
) -> list[ElevationSegment]:
    """Berechnet Höhengewinn/-verlust pro km aus den Waypoints.

    Nutzt km_marker der Waypoints, um sie den richtigen km zuzuordnen.
    Fallback auf gleichmäßige Verteilung wenn keine km_marker vorhanden.
    """
    if len(waypoints) < 2:
        return []

    has_alt = all(wp.alt is not None for wp in waypoints)
    if not has_alt:
        return []

    has_km_markers = all(wp.km_marker is not None for wp in waypoints)

    num_km = max(1, math.ceil(total_distance_km))
    gains = [0.0] * num_km
    losses = [0.0] * num_km

    for i in range(1, len(waypoints)):
        prev = waypoints[i - 1]
        curr = waypoints[i]
        diff = (curr.alt or 0) - (prev.alt or 0)

        if has_km_markers:
            km_idx = min(int(curr.km_marker or 0), num_km - 1)
        else:
            fraction = i / (len(waypoints) - 1)
            km_idx = min(int(fraction * total_distance_km), num_km - 1)

        if diff > 0:
            gains[km_idx] += diff
        else:
            losses[km_idx] += abs(diff)

    return [
        ElevationSegment(
            km=k + 1,
            gain_m=round(gains[k], 1),
            loss_m=round(losses[k], 1),
        )
        for k in range(num_km)
    ]


# ---------------------------------------------------------------------------
# Km-Splits → Segment-Pacing
# ---------------------------------------------------------------------------


def _map_splits_to_segments(
    segments: list[RouteSegment],
    pacing: PacingResponse,
) -> list[SegmentPacing]:
    """Mappt km-genaue Pacing-Splits auf die Route-Segmente.

    Jedes Segment bekommt den gewichteten Durchschnitt der km-Splits,
    die in seinem Bereich [start_km, end_km) liegen.
    """
    result: list[SegmentPacing] = []

    for idx, seg in enumerate(segments):
        seg_dist = seg.end_km - seg.start_km
        if seg_dist <= 0:
            continue

        paces_in_segment: list[tuple[float, float]] = []
        seg_gain = 0.0
        seg_loss = 0.0

        for split in pacing.splits:
            split_start = split.km - split.distance_km
            split_end = float(split.km)

            overlap_start = max(seg.start_km, split_start)
            overlap_end = min(seg.end_km, split_end)
            overlap = overlap_end - overlap_start

            if overlap > 0.01:
                weight = overlap / seg_dist
                paces_in_segment.append((split.target_pace_sec_per_km, weight))
                seg_gain += split.elevation_gain_m * (overlap / split.distance_km)
                seg_loss += split.elevation_loss_m * (overlap / split.distance_km)

        if not paces_in_segment:
            avg_pace = pacing.avg_pace_sec_per_km
        else:
            avg_pace = sum(p * w for p, w in paces_in_segment)

        seg_time_sec = round(avg_pace * seg_dist)
        pace_min_sec = max(avg_pace - _PACE_BAND_SEC, 60.0)
        pace_max_sec = avg_pace + _PACE_BAND_SEC

        note = _segment_note(seg.segment_type, seg_gain, seg_loss)

        result.append(
            SegmentPacing(
                segment_index=idx,
                segment_type=seg.segment_type,
                start_km=seg.start_km,
                end_km=seg.end_km,
                distance_km=round(seg_dist, 2),
                elevation_gain_m=round(seg_gain, 1),
                elevation_loss_m=round(seg_loss, 1),
                target_pace_min=_format_pace(pace_min_sec),
                target_pace_max=_format_pace(pace_max_sec),
                target_time_seconds=seg_time_sec,
                target_time_formatted=_format_duration(seg_time_sec),
                avg_pace_sec_per_km=round(avg_pace, 1),
                notes=note,
            )
        )

    return result


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _segment_note(segment_type: str, gain: float, loss: float) -> str | None:
    """Erzeugt kontextbezogene Hinweise pro Segment."""
    notes: list[str] = []

    if gain > 20:
        notes.append(f"↑{gain:.0f}m Anstieg — Pace wird langsamer")
    if loss > 20:
        notes.append(f"↓{loss:.0f}m Gefälle — Pace wird schneller")

    if segment_type == "warmup":
        notes.append("Locker einlaufen, nicht zu schnell starten")
    elif segment_type == "cooldown":
        notes.append("Auslaufen, Tempo reduzieren")

    return "; ".join(notes) if notes else None


def _format_pace(pace_sec: float) -> str:
    """Formatiert Pace (sec/km) als M:SS."""
    pace_min = pace_sec / 60.0
    mins = int(pace_min)
    secs = int(round((pace_min - mins) * 60))
    if secs == 60:
        mins += 1
        secs = 0
    return f"{mins}:{secs:02d}"


def _format_duration(total_seconds: int) -> str:
    """Formatiert Dauer als H:MM:SS oder MM:SS."""
    hours = total_seconds // 3600
    mins = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if hours > 0:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"
