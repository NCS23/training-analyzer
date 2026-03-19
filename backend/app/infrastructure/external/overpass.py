"""Overpass API Client — Untergrund/Surface entlang von GPS-Routen."""

import logging
from collections import Counter

from app.infrastructure.external.http_client import ExternalAPIClient

logger = logging.getLogger(__name__)

# Deutsche Labels fuer OSM surface-Tags
SURFACE_LABELS: dict[str, str] = {
    "asphalt": "Asphalt",
    "concrete": "Beton",
    "paving_stones": "Pflaster",
    "cobblestone": "Kopfsteinpflaster",
    "sett": "Pflaster",
    "gravel": "Schotter",
    "fine_gravel": "Feiner Schotter",
    "compacted": "Verdichtet",
    "dirt": "Erde",
    "earth": "Erde",
    "mud": "Matsch",
    "sand": "Sand",
    "grass": "Gras",
    "wood": "Holz",
    "metal": "Metall",
    "tartan": "Tartan",
    "rubber": "Gummi",
}


def _label(surface: str) -> str:
    """Konvertiert OSM surface-Tag in deutschen Label."""
    return SURFACE_LABELS.get(surface.lower(), surface.capitalize())


class OverpassClient:
    """Untergrund-Analyse via OpenStreetMap Overpass API."""

    def __init__(self) -> None:
        self.client = ExternalAPIClient(
            base_url="https://overpass-api.de/api",
            timeout=30.0,
            rate_limit_delay=1.0,
        )

    async def get_surface_along_route(
        self, points: list[dict], sample_count: int = 20
    ) -> dict[str, float] | None:
        """Ermittelt Untergrund-Verteilung entlang einer GPS-Route.

        Sampelt sample_count Punkte, fragt fuer jeden den naechsten Weg ab,
        und aggregiert die surface-Tags.

        Returns dict wie {"Asphalt": 70.0, "Schotter": 20.0, "Gras": 10.0}
        (Prozent) oder None bei Fehler.
        """
        if not points or len(points) < 2:
            return None

        # Punkte gleichmaessig samplen
        step = max(1, len(points) // sample_count)
        sampled = [points[i] for i in range(0, len(points), step)][:sample_count]

        # Overpass-Query: Finde den naechsten Weg (highway) fuer jeden Punkt
        # und extrahiere das surface-Tag
        surfaces: list[str] = []
        for pt in sampled:
            surface = await self._query_surface_at(pt["lat"], pt["lng"])
            if surface:
                surfaces.append(surface)

        if not surfaces:
            return None

        # Verteilung berechnen
        counter = Counter(surfaces)
        total = sum(counter.values())
        return {
            _label(surface): round(count / total * 100, 1)
            for surface, count in counter.most_common()
        }

    async def _query_surface_at(self, lat: float, lon: float) -> str | None:
        """Fragt den Untergrund am naechsten Weg bei lat/lon ab."""
        # Overpass QL: Finde Wege (highway=*) im 20m Umkreis, sortiert nach Naehe
        query = f'[out:json][timeout:5];way["highway"](around:20,{lat},{lon});out tags 1;'
        data = await self.client.get(
            "/interpreter",
            params={"data": query},
        )
        if not data or "elements" not in data:
            return None

        elements = data["elements"]
        if not elements:
            return None

        # Ersten Treffer nehmen (naechster Weg)
        tags = elements[0].get("tags", {})
        return tags.get("surface")


overpass_client = OverpassClient()
