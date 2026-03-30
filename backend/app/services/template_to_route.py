"""Auto-Route aus Session Template (#571).

Berechnet Gesamtdistanz aus Template-Segmenten, generiert passende
Rundstrecke via OSRM und verteilt Segmente proportional auf die Route.

Kern-Use-Case von Epic #508: Template → Route mit Trainingsstruktur.
"""

from __future__ import annotations

import math
from typing import Optional

from pydantic import BaseModel, Field

from app.models.segment import Segment
from app.models.training_route import RouteSegment, TrainingRouteCreate, Waypoint
from app.models.weekly_plan import RunDetails

# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class RouteFromTemplateRequest(BaseModel):
    """Input: Startpunkt + optionale Routing-Parameter."""

    start_lat: float = Field(..., ge=-90, le=90)
    start_lng: float = Field(..., ge=-180, le=180)
    num_alternatives: int = Field(default=1, ge=1, le=3)


class RouteFromTemplatePreview(BaseModel):
    """Vorberechnete Route-Daten (noch nicht gespeichert)."""

    name: str
    distance_km: float
    waypoints: list[Waypoint]
    route_segments: list[RouteSegment]
    linked_session_template_id: int
    pacing_strategy: str = "even"

    def to_create(self) -> TrainingRouteCreate:
        """Konvertiert zu TrainingRouteCreate für den Endpoint."""
        return TrainingRouteCreate(
            name=self.name,
            distance_km=self.distance_km,
            elevation_gain_m=0.0,
            elevation_loss_m=0.0,
            waypoints=self.waypoints,
            route_segments=self.route_segments,
            linked_session_template_id=self.linked_session_template_id,
            pacing_strategy=self.pacing_strategy,
        )


# ---------------------------------------------------------------------------
# Distanzberechnung aus Segmenten
# ---------------------------------------------------------------------------

# Standard-Distanzen für Segmente ohne explizite Distanzangabe (in km)
_DEFAULT_SEGMENT_DISTANCES: dict[str, float] = {
    "warmup": 1.5,
    "cooldown": 1.5,
    "steady": 5.0,
    "work": 0.4,
    "recovery": 0.2,
    "threshold": 2.0,
    "vo2max": 0.5,
    "long_run": 10.0,
    "race": 5.0,
}

# Fallback für unbekannte Segment-Typen
_DEFAULT_FALLBACK_KM = 1.0

# Abbildung Segment-Typ (aus Segment-Modell) → RouteSegment-Typ (aus TrainingRoute)
# RouteSegment akzeptiert dieselben Typen wie Segment (SEGMENT_TYPE_REGEX)
_SEGMENT_TYPE_MAP: dict[str, str] = {
    "warmup": "warmup",
    "cooldown": "cooldown",
    "steady": "steady",
    "work": "work",
    "recovery_jog": "recovery_jog",
    "rest": "rest",
    "strides": "work",
    "drills": "drills",
    "pace_building": "steady",
    "tempo_block": "steady",
}

# Bekannte gültige Route-Segment-Typen (aus taxonomy.SEGMENT_TYPES)
_VALID_ROUTE_SEGMENT_TYPES = frozenset(
    {"warmup", "cooldown", "steady", "work", "recovery_jog", "rest", "strides", "drills"}
)


def calculate_template_distance(run_details: RunDetails) -> float:
    """Berechnet Gesamtdistanz aus den Segmenten eines RunDetails.

    Priorität:
    1. target_distance_km des Segments (wenn vorhanden, × repeats)
    2. Schätzung aus target_duration_minutes + Default-Pace (~5:30 min/km)
    3. Default-Distanz pro Segment-Typ
    """
    if not run_details.segments:
        # Fallback: duration-basiert
        if run_details.target_duration_minutes:
            return round(run_details.target_duration_minutes / 5.5, 1)
        return 10.0

    total = 0.0
    for seg in run_details.segments:
        km = _segment_distance(seg)
        total += km * seg.repeats

    return round(max(total, 1.0), 2)


def _segment_distance(seg: Segment) -> float:
    """Distanz eines einzelnen Segments (ohne repeats)."""
    if seg.target_distance_km:
        return seg.target_distance_km

    if seg.target_duration_minutes:
        # Schätzung: ~5:30 min/km → ~10.9 km/h
        return round(seg.target_duration_minutes / 5.5, 2)

    return _DEFAULT_SEGMENT_DISTANCES.get(seg.segment_type, _DEFAULT_FALLBACK_KM)


# ---------------------------------------------------------------------------
# Segment-Mapping: Template-Segmente → RouteSegmente
# ---------------------------------------------------------------------------


def map_segments_to_route(
    segments: list[Segment],
    total_distance_km: float,
) -> list[RouteSegment]:
    """Verteilt Template-Segmente proportional auf die Route.

    Berechnet start_km/end_km pro Segment basierend auf ihrer
    relativen Distanz zur Gesamtdistanz.
    """
    # Segmente expandieren (repeats berücksichtigen)
    expanded: list[tuple[Segment, float]] = []
    for seg in segments:
        seg_km = _segment_distance(seg)
        for _ in range(seg.repeats):
            expanded.append((seg, seg_km))

    if not expanded:
        return []

    # Normalisieren auf total_distance_km
    raw_total = sum(km for _, km in expanded)
    scale = total_distance_km / raw_total if raw_total > 0 else 1.0

    route_segments: list[RouteSegment] = []
    cursor = 0.0

    for i, (seg, raw_km) in enumerate(expanded):
        seg_km = round(raw_km * scale, 3)
        start_km = round(cursor, 3)
        end_km = round(cursor + seg_km, 3)

        # Letztes Segment exakt auf total_distance_km setzen (Rundungsfehler)
        if i == len(expanded) - 1:
            end_km = round(total_distance_km, 3)

        if end_km <= start_km:
            end_km = round(start_km + 0.1, 3)

        route_type = _SEGMENT_TYPE_MAP.get(seg.segment_type, seg.segment_type)
        if route_type not in _VALID_ROUTE_SEGMENT_TYPES:
            route_type = "steady"

        route_segments.append(
            RouteSegment(
                segment_type=route_type,
                start_km=start_km,
                end_km=end_km,
                target_pace_min=seg.target_pace_min,
                target_pace_max=seg.target_pace_max,
                target_hr_min=seg.target_hr_min,
                target_hr_max=seg.target_hr_max,
                notes=seg.notes,
            )
        )
        cursor = end_km

    return route_segments


# ---------------------------------------------------------------------------
# Route-Preview aus OSRM-Ergebnis bauen
# ---------------------------------------------------------------------------


def build_route_preview(
    template_id: int,
    template_name: str,
    run_details: RunDetails,
    osrm_result: dict,
) -> RouteFromTemplatePreview:
    """Baut RouteFromTemplatePreview aus OSRM-Ergebnis + Template-Daten.

    Args:
        template_id: ID des Session Templates.
        template_name: Name des Templates (für Routenname).
        run_details: RunDetails mit Segmenten + Pacing-Zielen.
        osrm_result: Ergebnis von OSRMClient.generate_round_trip()[0].
    """
    distance_km = round(osrm_result["distance_km"], 2)

    raw_points = osrm_result["points"]
    waypoints = _points_to_waypoints_with_km_markers(raw_points, distance_km)

    segments = run_details.segments or []
    route_segments = map_segments_to_route(segments, distance_km)

    return RouteFromTemplatePreview(
        name=f"Route: {template_name}",
        distance_km=distance_km,
        waypoints=waypoints,
        route_segments=route_segments,
        linked_session_template_id=template_id,
    )


def _points_to_waypoints_with_km_markers(
    points: list[dict],
    total_distance_km: float,
) -> list[Waypoint]:
    """Konvertiert OSRM-Punkte zu Waypoints mit km_marker.

    Berechnet kumulative Distanz (Haversine) für km_marker.
    """
    if not points:
        return []

    waypoints: list[Waypoint] = []
    cumulative_km = 0.0

    for i, pt in enumerate(points):
        if i > 0:
            prev = points[i - 1]
            cumulative_km += _haversine_km(prev["lat"], prev["lng"], pt["lat"], pt["lng"])

        waypoints.append(
            Waypoint(
                lat=pt["lat"],
                lng=pt["lng"],
                alt=pt.get("alt"),
                km_marker=round(min(cumulative_km, total_distance_km), 3),
            )
        )

    return waypoints


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine-Distanz zwischen zwei GPS-Punkten in km."""
    r = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(dλ / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Hilfsfunktion für den Endpoint
# ---------------------------------------------------------------------------


def template_name_for_route(
    template_name: str,
    run_type: Optional[str] = None,
) -> str:
    """Erzeugt einen Routennamen aus dem Template-Namen."""
    if run_type:
        _run_type_labels = {
            "long_run": "Langer Lauf",
            "interval": "Intervall",
            "tempo": "Tempo",
            "recovery": "Regeneration",
            "race": "Wettkampf",
            "fartlek": "Fahrtspiel",
        }
        label = _run_type_labels.get(run_type, "")
        if label:
            return f"{label}: {template_name}"
    return f"Route: {template_name}"
