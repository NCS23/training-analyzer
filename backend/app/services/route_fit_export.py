"""FIT Course Export für Trainingsrouten (#577).

Generiert FIT Course Files mit Waypoints, Distanz und Höhenprofil
für den Import in Garmin-Geräte und kompatible Apps.

FIT-Format: Garmin FIT Protocol 2.0
Bibliothek: fit-tool (bereits in pyproject.toml)
"""

from __future__ import annotations

import math
import re
from typing import Optional

from fit_tool.fit_file_builder import FitFileBuilder  # type: ignore[import-untyped]
from fit_tool.profile.messages.course_message import CourseMessage  # type: ignore[import-untyped]
from fit_tool.profile.messages.file_id_message import FileIdMessage  # type: ignore[import-untyped]
from fit_tool.profile.messages.lap_message import LapMessage  # type: ignore[import-untyped]
from fit_tool.profile.messages.record_message import RecordMessage  # type: ignore[import-untyped]
from fit_tool.profile.profile_type import (  # type: ignore[import-untyped]
    FileType,
    Manufacturer,
    Sport,
)

from app.models.training_route import Waypoint

# ---------------------------------------------------------------------------
# Öffentliche API
# ---------------------------------------------------------------------------


def generate_fit_course(
    route_name: str,
    waypoints: list[Waypoint],
    total_distance_km: float,
) -> bytes:
    """Erzeugt FIT Course File als Bytes.

    Struktur:
    - FileIdMessage (type=COURSE)
    - CourseMessage (name, sport=RUNNING)
    - LapMessage  (Gesamtroute als ein Lap)
    - RecordMessage pro Waypoint (position, distance, altitude)
    """
    builder = FitFileBuilder()
    _add_file_id(builder)
    _add_course(builder, route_name)
    _add_lap(builder, waypoints, total_distance_km)
    _add_records(builder, waypoints)
    return builder.build().to_bytes()


def safe_filename(name: str) -> str:
    """Erzeugt einen sicheren Dateinamen aus dem Routennamen."""
    safe = re.sub(r"[^\w\s\-äöüÄÖÜß]", "", name)
    safe = re.sub(r"\s+", "_", safe.strip())
    return safe[:100] or "route"


# ---------------------------------------------------------------------------
# FIT-Aufbau
# ---------------------------------------------------------------------------


def _add_file_id(builder: FitFileBuilder) -> None:
    file_id = FileIdMessage()
    file_id.type = FileType.COURSE
    file_id.manufacturer = Manufacturer.DEVELOPMENT.value
    builder.add(file_id)


def _add_course(builder: FitFileBuilder, name: str) -> None:
    course = CourseMessage()
    course.course_name = name
    course.sport = Sport.RUNNING
    builder.add(course)


def _add_lap(
    builder: FitFileBuilder,
    waypoints: list[Waypoint],
    total_distance_km: float,
) -> None:
    """Fügt einen Lap für die Gesamtroute hinzu."""
    lap = LapMessage()
    lap.total_distance = total_distance_km * 1000.0

    if waypoints:
        first, last = waypoints[0], waypoints[-1]
        lap.start_position_lat = first.lat
        lap.start_position_long = first.lng
        lap.end_position_lat = last.lat
        lap.end_position_long = last.lng

    builder.add(lap)


def _add_records(builder: FitFileBuilder, waypoints: list[Waypoint]) -> None:
    """Fügt RecordMessage pro Waypoint hinzu mit laufender Distanz."""
    cumulative_m = 0.0

    for i, wp in enumerate(waypoints):
        if i > 0:
            prev = waypoints[i - 1]
            cumulative_m += _haversine_m(prev.lat, prev.lng, wp.lat, wp.lng)

        rec = RecordMessage()
        rec.position_lat = wp.lat
        rec.position_long = wp.lng
        rec.distance = cumulative_m

        altitude = _resolve_altitude(wp, waypoints, i)
        if altitude is not None:
            rec.altitude = altitude

        builder.add(rec)


def _resolve_altitude(
    wp: Waypoint,
    waypoints: list[Waypoint],
    index: int,
) -> Optional[float]:
    """Gibt Höhe zurück — interpoliert fehlende Werte aus Nachbarn."""
    if wp.alt is not None:
        return float(wp.alt)

    # Suche nächsten bekannten Vorgänger und Nachfolger
    prev_alt: Optional[float] = None
    next_alt: Optional[float] = None
    prev_dist = 0
    next_dist = 0

    for j in range(index - 1, -1, -1):
        if waypoints[j].alt is not None:
            prev_alt = float(waypoints[j].alt)  # type: ignore[arg-type]
            prev_dist = index - j
            break

    for j in range(index + 1, len(waypoints)):
        if waypoints[j].alt is not None:
            next_alt = float(waypoints[j].alt)  # type: ignore[arg-type]
            next_dist = j - index
            break

    if prev_alt is not None and next_alt is not None:
        total = prev_dist + next_dist
        return prev_alt + (next_alt - prev_alt) * prev_dist / total
    if prev_alt is not None:
        return prev_alt
    if next_alt is not None:
        return next_alt
    return None


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Berechnet Distanz in Metern zwischen zwei GPS-Koordinaten."""
    r = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
