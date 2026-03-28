"""OSRM (Open Source Routing Machine) Client für Laufrouten (#520).

Unterstützt:
- Route: Waypoints → gesnappte Route auf Wegen
- Nearest: Nächsten Punkt auf einem Weg finden
- Rundkurs-Generierung: Startpunkt + Distanz → Rundstrecke
"""

from __future__ import annotations

import logging
import math
from typing import Optional

from app.core.config import settings
from app.infrastructure.external.http_client import ExternalAPIClient

logger = logging.getLogger(__name__)

# Profil für Fußgänger/Läufer
PROFILE = "foot"


class OSRMClient:
    """Async OSRM API Client für Laufrouten."""

    def __init__(self) -> None:
        self.client = ExternalAPIClient(
            base_url=settings.osrm_base_url,
            timeout=settings.osrm_timeout,
        )

    async def route(
        self,
        waypoints: list[dict],
        overview: str = "full",
    ) -> Optional[dict]:
        """Berechne Route zwischen Waypoints.

        Args:
            waypoints: Liste von {lat, lng} Dicts (min. 2).
            overview: "full" (alle Punkte), "simplified", "false".

        Returns:
            Dict mit geometry (GeoJSON), distance (m), duration (s), waypoints.
            None bei Fehler.
        """
        if len(waypoints) < 2:
            return None

        coords = ";".join(f"{wp['lng']},{wp['lat']}" for wp in waypoints)
        path = f"/route/v1/{PROFILE}/{coords}"

        data = await self.client.get(
            path,
            params={
                "overview": overview,
                "geometries": "geojson",
                "steps": "false",
            },
        )

        if not data or data.get("code") != "Ok":
            logger.warning("OSRM route failed: %s", data.get("code") if data else "no response")
            return None

        route_data = data["routes"][0]
        geometry = route_data["geometry"]

        # GeoJSON → unsere Waypoint-Struktur [{lat, lng}]
        route_points = [
            {"lat": round(coord[1], 6), "lng": round(coord[0], 6)}
            for coord in geometry["coordinates"]
        ]

        return {
            "points": route_points,
            "distance_m": route_data["distance"],
            "duration_s": route_data["duration"],
            "snapped_waypoints": [
                {
                    "lat": round(wp["location"][1], 6),
                    "lng": round(wp["location"][0], 6),
                }
                for wp in data.get("waypoints", [])
            ],
        }

    async def nearest(self, lat: float, lng: float) -> Optional[dict]:
        """Finde nächsten Punkt auf einem Weg.

        Returns:
            Dict mit {lat, lng, distance_m, name} oder None.
        """
        path = f"/nearest/v1/{PROFILE}/{lng},{lat}"
        data = await self.client.get(path, params={"number": "1"})

        if not data or data.get("code") != "Ok" or not data.get("waypoints"):
            return None

        wp = data["waypoints"][0]
        return {
            "lat": round(wp["location"][1], 6),
            "lng": round(wp["location"][0], 6),
            "distance_m": wp.get("distance", 0),
            "name": wp.get("name", ""),
        }

    async def generate_round_trip(
        self,
        start_lat: float,
        start_lng: float,
        target_distance_km: float,
        num_alternatives: int = 3,
    ) -> list[dict]:
        """Generiere Rundkurse ab Startpunkt mit Zieldistanz.

        Erzeugt Intermediate Waypoints in verschiedenen Richtungen und
        routet über OSRM zurück zum Start.

        Args:
            start_lat: Breitengrad des Startpunkts.
            start_lng: Längengrad des Startpunkts.
            target_distance_km: Gewünschte Gesamtdistanz.
            num_alternatives: Anzahl Routenvorschläge (max 5).

        Returns:
            Liste von Route-Dicts, sortiert nach Distanz-Abweichung.
        """
        num_alternatives = min(num_alternatives, 5)
        results: list[dict] = []

        # Radius für Intermediate Waypoints (~1/4 der Gesamtdistanz)
        radius_km = target_distance_km / 4.0

        for i in range(num_alternatives):
            # Richtung variieren (gleichmäßig verteilt + leichter Offset)
            angle_deg = (360.0 / num_alternatives) * i + 15.0
            angle_rad = math.radians(angle_deg)

            # Intermediate Waypoint berechnen (Luftlinie)
            mid = _offset_point(start_lat, start_lng, radius_km, angle_rad)

            # 3-Punkt-Route: Start → Mid → Start
            waypoints = [
                {"lat": start_lat, "lng": start_lng},
                {"lat": mid["lat"], "lng": mid["lng"]},
                {"lat": start_lat, "lng": start_lng},
            ]

            route = await self.route(waypoints)
            if not route:
                continue

            actual_km = route["distance_m"] / 1000.0
            deviation = abs(actual_km - target_distance_km) / target_distance_km

            results.append(
                {
                    "points": route["points"],
                    "distance_km": round(actual_km, 2),
                    "duration_s": route["duration_s"],
                    "target_distance_km": target_distance_km,
                    "deviation_percent": round(deviation * 100, 1),
                    "direction_deg": round(angle_deg, 0),
                }
            )

        # Sortiere nach geringster Abweichung
        results.sort(key=lambda r: abs(r["distance_km"] - target_distance_km))
        return results

    async def close(self) -> None:
        await self.client.close()


def _offset_point(lat: float, lng: float, distance_km: float, bearing_rad: float) -> dict:
    """Berechne einen Punkt in gegebener Distanz und Richtung (Haversine)."""
    earth_radius_km = 6371.0
    lat_rad = math.radians(lat)
    lng_rad = math.radians(lng)
    d = distance_km / earth_radius_km

    new_lat = math.asin(
        math.sin(lat_rad) * math.cos(d) + math.cos(lat_rad) * math.sin(d) * math.cos(bearing_rad)
    )
    new_lng = lng_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(d) * math.cos(lat_rad),
        math.cos(d) - math.sin(lat_rad) * math.sin(new_lat),
    )

    return {
        "lat": round(math.degrees(new_lat), 6),
        "lng": round(math.degrees(new_lng), 6),
    }
