"""GPX-Datei parsen und pro-km Höhenprofil berechnen."""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET

from app.models.pacing import ElevationSegment

# GPX XML Namespaces
_GPX_NS = {
    "": "http://www.topografix.com/GPX/1/1",
    "gpx10": "http://www.topografix.com/GPX/1/0",
}


def parse_gpx_elevation(gpx_content: bytes) -> list[ElevationSegment]:
    """Parst eine GPX-Datei und berechnet pro-km Höhengewinn/-verlust.

    Returns:
        Liste von ElevationSegment, ein Eintrag pro Kilometer.
    """
    points = _extract_trackpoints(gpx_content)
    if len(points) < 2:
        raise ValueError("GPX-Datei enthält zu wenige Trackpunkte")

    return _calculate_km_segments(points)


def _extract_trackpoints(
    gpx_content: bytes,
) -> list[tuple[float, float, float]]:
    """Extrahiert (lat, lon, elevation) Tupel aus GPX-Trackpunkten."""
    root = ET.fromstring(gpx_content)  # noqa: S314
    points: list[tuple[float, float, float]] = []

    # GPX 1.1 und 1.0 Namespaces probieren
    for ns_prefix in ["", "gpx10"]:
        ns = _GPX_NS[ns_prefix]
        prefix = f"{{{ns}}}" if ns else ""

        for trkpt in root.iter(f"{prefix}trkpt"):
            lat = float(trkpt.get("lat", "0"))
            lon = float(trkpt.get("lon", "0"))
            ele_elem = trkpt.find(f"{prefix}ele")
            ele = float(ele_elem.text) if ele_elem is not None and ele_elem.text else 0.0
            points.append((lat, lon, ele))

        if points:
            break

    return points


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Berechnet die Distanz zwischen zwei GPS-Punkten in Metern."""
    r = 6_371_000  # Erdradius in Metern
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _calculate_km_segments(
    points: list[tuple[float, float, float]],
) -> list[ElevationSegment]:
    """Berechnet pro-km Höhengewinn und -verlust aus Trackpunkten."""
    segments: list[ElevationSegment] = []
    cum_dist = 0.0
    km_gain = 0.0
    km_loss = 0.0
    km_num = 1

    for i in range(1, len(points)):
        lat1, lon1, ele1 = points[i - 1]
        lat2, lon2, ele2 = points[i]

        dist = _haversine_m(lat1, lon1, lat2, lon2)
        ele_diff = ele2 - ele1

        # Rauschen filtern: nur Änderungen > 1m zählen
        if ele_diff > 1.0:
            km_gain += ele_diff
        elif ele_diff < -1.0:
            km_loss += abs(ele_diff)

        cum_dist += dist

        # Kilometer-Grenze erreicht
        while cum_dist >= 1000.0:
            segments.append(
                ElevationSegment(
                    km=km_num,
                    gain_m=round(km_gain, 1),
                    loss_m=round(km_loss, 1),
                )
            )
            km_num += 1
            cum_dist -= 1000.0
            km_gain = 0.0
            km_loss = 0.0

    # Letzten Abschnitt hinzufügen (wenn > 50m übrig)
    if cum_dist > 50.0:
        segments.append(
            ElevationSegment(
                km=km_num,
                gain_m=round(km_gain, 1),
                loss_m=round(km_loss, 1),
            )
        )

    return segments
