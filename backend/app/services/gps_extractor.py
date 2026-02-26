"""GPS Track Extraction from FIT file records."""

import math
from typing import Optional


# FIT semicircles to degrees conversion factor
SEMICIRCLES_TO_DEGREES = 180.0 / (2**31)


def extract_gps_track(records: list[dict]) -> Optional[dict]:
    """Extract GPS track from FIT record messages.

    Args:
        records: List of record dicts from FIT file (second-by-second data).

    Returns:
        Dict with points, start_location, end_location, total_ascent, total_descent
        or None if no GPS data found.
    """
    points: list[dict] = []
    start_ts = None

    for record in records:
        lat_raw = record.get("position_lat")
        lng_raw = record.get("position_long")

        if lat_raw is None or lng_raw is None:
            continue

        # Convert semicircles to degrees if needed
        lat = _to_degrees(lat_raw)
        lng = _to_degrees(lng_raw)

        if lat is None or lng is None:
            continue

        # Skip obviously invalid coordinates
        if abs(lat) > 90 or abs(lng) > 180:
            continue

        alt = record.get("enhanced_altitude") or record.get("altitude")
        ts = record.get("timestamp")
        hr = record.get("heart_rate")

        if start_ts is None and ts:
            start_ts = ts

        elapsed = 0
        if ts and start_ts:
            elapsed = int((ts - start_ts).total_seconds())

        point: dict = {
            "lat": round(lat, 6),
            "lng": round(lng, 6),
            "seconds": elapsed,
        }

        if alt is not None:
            point["alt"] = round(float(alt), 1)
        if hr is not None:
            point["hr"] = int(hr)

        points.append(point)

    if not points:
        return None

    # Simplify if too many points
    if len(points) > 10000:
        points = _douglas_peucker(points, epsilon=0.00005)

    # Start/end locations
    start = {"lat": points[0]["lat"], "lng": points[0]["lng"]}
    end = {"lat": points[-1]["lat"], "lng": points[-1]["lng"]}

    # Elevation stats
    total_ascent, total_descent = _calculate_elevation(points)

    return {
        "points": points,
        "start_location": start,
        "end_location": end,
        "total_points": len(points),
        "total_ascent_m": total_ascent,
        "total_descent_m": total_descent,
    }


def _to_degrees(value) -> Optional[float]:
    """Convert FIT coordinate value to degrees.

    FIT files store coordinates as semicircles (int32).
    Some parsers already convert to float degrees.
    """
    if value is None:
        return None

    if isinstance(value, (int,)):
        # Semicircles (large integer)
        if abs(value) > 180:
            return value * SEMICIRCLES_TO_DEGREES
        return float(value)

    if isinstance(value, float):
        # Already in degrees if within valid range
        if abs(value) <= 180:
            return value
        # Otherwise, semicircles as float
        return value * SEMICIRCLES_TO_DEGREES

    return None


def _calculate_elevation(points: list[dict]) -> tuple[Optional[float], Optional[float]]:
    """Calculate total ascent and descent from elevation data.

    Downsamples to 10-second intervals to filter GPS altitude noise,
    then applies a 1m threshold. This is the standard approach used
    by Strava and other platforms for per-second GPS data.
    """
    alts = [p["alt"] for p in points if "alt" in p]
    if len(alts) < 2:
        return None, None

    # Downsample to ~10s intervals to smooth noise
    step = max(1, min(10, len(alts) // 20))
    sampled = alts[::step]
    if sampled[-1] != alts[-1]:
        sampled.append(alts[-1])

    ascent = 0.0
    descent = 0.0

    for i in range(1, len(sampled)):
        diff = sampled[i] - sampled[i - 1]
        if diff > 1.0:
            ascent += diff
        elif diff < -1.0:
            descent += abs(diff)

    return round(ascent, 0), round(descent, 0)


def _douglas_peucker(points: list[dict], epsilon: float) -> list[dict]:
    """Simplify GPS track using Douglas-Peucker algorithm."""
    if len(points) <= 2:
        return points

    # Find point with max distance from line between first and last
    max_dist = 0.0
    max_idx = 0

    start = points[0]
    end = points[-1]

    for i in range(1, len(points) - 1):
        dist = _point_line_distance(points[i], start, end)
        if dist > max_dist:
            max_dist = dist
            max_idx = i

    if max_dist > epsilon:
        left = _douglas_peucker(points[: max_idx + 1], epsilon)
        right = _douglas_peucker(points[max_idx:], epsilon)
        return left[:-1] + right
    else:
        return [points[0], points[-1]]


def _point_line_distance(point: dict, start: dict, end: dict) -> float:
    """Calculate perpendicular distance from point to line (lat/lng)."""
    dx = end["lng"] - start["lng"]
    dy = end["lat"] - start["lat"]

    if dx == 0 and dy == 0:
        return math.sqrt(
            (point["lng"] - start["lng"]) ** 2 + (point["lat"] - start["lat"]) ** 2
        )

    t = ((point["lng"] - start["lng"]) * dx + (point["lat"] - start["lat"]) * dy) / (
        dx * dx + dy * dy
    )
    t = max(0, min(1, t))

    proj_lng = start["lng"] + t * dx
    proj_lat = start["lat"] + t * dy

    return math.sqrt((point["lng"] - proj_lng) ** 2 + (point["lat"] - proj_lat) ** 2)
