"""Convert an existing session GPS track into a TrainingRoute (#513).

Reuses gps_extractor._douglas_peucker for simplification and
km_split_calculator.haversine_meters for distance calculation.
"""

from __future__ import annotations

import json
from typing import Optional

from app.infrastructure.database.models import WorkoutModel
from app.models.training_route import RouteSegment, Waypoint
from app.services.gps_extractor import _calculate_elevation, _douglas_peucker
from app.services.km_split_calculator import haversine_meters

# Target: ~500 waypoints for a typical route (good detail, manageable size)
SIMPLIFICATION_EPSILON = 0.00003


def session_to_route_data(
    workout: WorkoutModel,
    name: Optional[str] = None,
) -> dict:
    """Extract route data from a session with GPS track.

    Args:
        workout: WorkoutModel with gps_track_json.
        name: Optional custom name. Defaults to location + date.

    Returns:
        Dict ready for TrainingRouteCreate.

    Raises:
        ValueError: If session has no GPS data.
    """
    if not workout.gps_track_json:
        msg = "Session hat keine GPS-Daten"
        raise ValueError(msg)

    track = json.loads(str(workout.gps_track_json))
    points: list[dict] = track.get("points", [])

    if len(points) < 2:
        msg = "GPS-Track hat weniger als 2 Punkte"
        raise ValueError(msg)

    # Simplify track
    simplified = _douglas_peucker(points, epsilon=SIMPLIFICATION_EPSILON)
    if len(simplified) < 2:
        simplified = [points[0], points[-1]]

    # Build waypoints with km_markers
    waypoints = _build_waypoints(simplified)

    # Calculate total distance
    distance_km = _total_distance_km(simplified)

    # Elevation
    ascent, descent = _calculate_elevation(simplified)

    # Default name
    if not name:
        loc = str(workout.location_name) if workout.location_name else "Route"
        date_str = workout.date.strftime("%d.%m.%Y") if workout.date else ""
        name = f"{loc} — {date_str}".strip(" —")

    # Surface from session
    surface: Optional[dict[str, float]] = None
    if workout.surface_json:
        surface = json.loads(str(workout.surface_json))

    # Laps → RouteSegments (optional)
    route_segments = _laps_to_route_segments(workout)

    return {
        "name": name,
        "distance_km": round(distance_km, 2),
        "elevation_gain_m": ascent or 0,
        "elevation_loss_m": descent or 0,
        "location_name": str(workout.location_name) if workout.location_name else None,
        "surface": surface,
        "waypoints": [wp.model_dump() for wp in waypoints],
        "route_segments": (
            [seg.model_dump() for seg in route_segments] if route_segments else None
        ),
    }


def _build_waypoints(points: list[dict]) -> list[Waypoint]:
    """Build Waypoint list with cumulative km_markers."""
    waypoints: list[Waypoint] = []
    cumulative_km = 0.0

    for i, p in enumerate(points):
        if i > 0:
            dist_m = haversine_meters(
                points[i - 1]["lat"],
                points[i - 1]["lng"],
                p["lat"],
                p["lng"],
            )
            cumulative_km += dist_m / 1000.0

        waypoints.append(
            Waypoint(
                lat=p["lat"],
                lng=p["lng"],
                alt=p.get("alt"),
                km_marker=round(cumulative_km, 3),
            )
        )

    return waypoints


def _total_distance_km(points: list[dict]) -> float:
    """Calculate total distance in km from GPS points."""
    total_m = 0.0
    for i in range(1, len(points)):
        total_m += haversine_meters(
            points[i - 1]["lat"],
            points[i - 1]["lng"],
            points[i]["lat"],
            points[i]["lng"],
        )
    return total_m / 1000.0


def _laps_to_route_segments(
    workout: WorkoutModel,
) -> Optional[list[RouteSegment]]:
    """Convert session laps to route segments if available."""
    if not workout.laps_json:
        return None

    laps = json.loads(str(workout.laps_json))
    if not laps:
        return None

    segments: list[RouteSegment] = []
    current_km = 0.0

    for lap in laps:
        lap_dist = lap.get("distance_km")
        if not lap_dist or lap_dist <= 0:
            continue

        end_km = current_km + lap_dist

        # Segment type from classifier
        seg_type = lap.get("suggested_type") or lap.get("user_override") or "steady"

        # Validate segment type — fallback to steady
        valid_types = {
            "warmup",
            "cooldown",
            "steady",
            "work",
            "recovery_jog",
            "rest",
            "strides",
            "drills",
        }
        if seg_type not in valid_types:
            seg_type = "steady"

        segment = RouteSegment(
            segment_type=seg_type,
            start_km=round(current_km, 2),
            end_km=round(end_km, 2),
            target_pace_min=lap.get("pace_formatted"),
            target_hr_min=lap.get("avg_hr_bpm"),
            target_hr_max=lap.get("max_hr_bpm"),
        )
        segments.append(segment)
        current_km = end_km

    return segments if segments else None
