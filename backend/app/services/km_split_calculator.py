"""Per-Kilometer Split Calculator from GPS track data."""

import math
from typing import Optional


def haversine_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance in meters between two GPS points (haversine formula)."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def calculate_km_splits(gps_track: dict) -> list[dict]:
    """Calculate per-kilometer splits from GPS track points.

    Each GPS point must have: lat, lng, seconds (elapsed).
    Optional fields: hr (heart rate), alt (altitude).
    """
    points = gps_track.get("points", [])
    if len(points) < 2:
        return []

    splits: list[dict] = []
    km_number = 1
    cumulative_distance = 0.0
    km_start_seconds = float(points[0]["seconds"])
    km_hr_values: list[int] = []
    km_alt_values: list[float] = []
    km_boundary = 1000.0  # Next boundary in meters

    prev = points[0]
    if prev.get("hr") is not None:
        km_hr_values.append(int(prev["hr"]))
    if prev.get("alt") is not None:
        km_alt_values.append(float(prev["alt"]))

    for i in range(1, len(points)):
        curr = points[i]
        seg_dist = haversine_meters(prev["lat"], prev["lng"], curr["lat"], curr["lng"])

        # Skip GPS glitches (> 500m between consecutive seconds)
        if seg_dist > 500 and curr["seconds"] - prev["seconds"] <= 2:
            prev = curr
            continue

        while cumulative_distance + seg_dist >= km_boundary:
            # Interpolate to exact km boundary
            remaining = km_boundary - cumulative_distance
            ratio = remaining / seg_dist if seg_dist > 0 else 1.0
            boundary_seconds = prev["seconds"] + ratio * (curr["seconds"] - prev["seconds"])
            boundary_lat = prev["lat"] + ratio * (curr["lat"] - prev["lat"])
            boundary_lng = prev["lng"] + ratio * (curr["lng"] - prev["lng"])

            duration_sec = max(1, int(round(boundary_seconds - km_start_seconds)))
            pace: Optional[float] = duration_sec / 60.0
            elev_gain, elev_loss = _calc_elevation(km_alt_values)

            splits.append(
                _build_split(
                    km_number,
                    1.0,
                    duration_sec,
                    pace,
                    km_hr_values,
                    elev_gain,
                    elev_loss,
                    is_partial=False,
                    boundary_lat=round(boundary_lat, 6),
                    boundary_lng=round(boundary_lng, 6),
                )
            )

            # Advance
            km_number += 1
            km_start_seconds = boundary_seconds
            cumulative_distance = km_boundary
            km_boundary += 1000.0
            km_hr_values = []
            km_alt_values = []

            # Recalculate remaining segment distance after boundary
            seg_dist = seg_dist - remaining
            remaining = 0.0

        cumulative_distance += seg_dist

        if curr.get("hr") is not None:
            km_hr_values.append(int(curr["hr"]))
        if curr.get("alt") is not None:
            km_alt_values.append(float(curr["alt"]))
        prev = curr

    # Final partial km (only if > 50m)
    remaining_m = cumulative_distance - (km_boundary - 1000.0)
    if remaining_m > 50:
        last_point = points[-1]
        duration_sec = max(1, int(round(last_point["seconds"] - km_start_seconds)))
        partial_km = remaining_m / 1000.0
        pace = (duration_sec / 60.0) / partial_km if partial_km > 0 else None
        elev_gain, elev_loss = _calc_elevation(km_alt_values)

        splits.append(
            _build_split(
                km_number,
                round(partial_km, 2),
                duration_sec,
                pace,
                km_hr_values,
                elev_gain,
                elev_loss,
                is_partial=True,
                boundary_lat=round(float(last_point["lat"]), 6),
                boundary_lng=round(float(last_point["lng"]), 6),
            )
        )

    return splits


def _build_split(
    km_number: int,
    distance_km: float,
    duration_sec: int,
    pace: Optional[float],
    hr_values: list[int],
    elev_gain: Optional[float],
    elev_loss: Optional[float],
    is_partial: bool,
    boundary_lat: Optional[float] = None,
    boundary_lng: Optional[float] = None,
) -> dict:
    """Build a single km split dict."""
    pace_formatted = None
    if pace is not None:
        mins = int(pace)
        secs = int(round((pace - mins) * 60))
        if secs == 60:
            mins += 1
            secs = 0
        pace_formatted = f"{mins}:{secs:02d}"

    dur_mins = duration_sec // 60
    dur_secs = duration_sec % 60

    return {
        "km_number": km_number,
        "distance_km": distance_km,
        "duration_seconds": duration_sec,
        "duration_formatted": f"{dur_mins}:{dur_secs:02d}",
        "pace_min_per_km": round(pace, 2) if pace else None,
        "pace_formatted": pace_formatted,
        "avg_hr_bpm": round(sum(hr_values) / len(hr_values)) if hr_values else None,
        "elevation_gain_m": elev_gain,
        "elevation_loss_m": elev_loss,
        "is_partial": is_partial,
        "boundary_lat": boundary_lat,
        "boundary_lng": boundary_lng,
    }


def _calc_elevation(alt_values: list[float]) -> tuple[Optional[float], Optional[float]]:
    """Calculate elevation gain and loss from altitude values.

    Uses a dead-band approach: accumulate small changes in one direction
    and only commit once the accumulated change exceeds the threshold.
    This handles per-second GPS data where individual deltas are tiny
    (e.g. 0.2m) but real elevation change accumulates over many points.
    """
    if len(alt_values) < 2:
        return None, None

    threshold = 2.0  # Minimum accumulated change to count
    gain = 0.0
    loss = 0.0
    ref_alt = alt_values[0]

    for alt in alt_values[1:]:
        diff = alt - ref_alt
        if diff >= threshold:
            gain += diff
            ref_alt = alt
        elif diff <= -threshold:
            loss += abs(diff)
            ref_alt = alt

    return round(gain, 1), round(loss, 1)
