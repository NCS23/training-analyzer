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
            base_url="https://overpass.kumi.systems/api",
            timeout=30.0,
        )

    async def get_surface_along_route(
        self, points: list[dict], sample_count: int = 10
    ) -> dict[str, float] | None:
        """Ermittelt Untergrund-Verteilung entlang einer GPS-Route.

        Nutzt eine einzige Overpass-Query mit Bounding-Box statt
        einzelner Requests pro Sample-Punkt.

        Returns dict wie {"Asphalt": 70.0, "Schotter": 20.0, "Gras": 10.0}
        (Prozent) oder None bei Fehler.
        """
        if not points or len(points) < 2:
            return None

        # Punkte gleichmaessig samplen
        step = max(1, len(points) // sample_count)
        sampled = [points[i] for i in range(0, len(points), step)][:sample_count]

        # Eine einzige Overpass-Query: Alle Wege in der Bounding-Box der Route
        surfaces = await self._batch_query_surfaces(sampled)
        if not surfaces:
            return None

        counter = Counter(surfaces)
        total = sum(counter.values())
        return {
            _label(surface): round(count / total * 100, 1)
            for surface, count in counter.most_common()
        }

    async def _batch_query_surfaces(self, sampled_points: list[dict]) -> list[str]:
        """Eine einzige Overpass-Query fuer alle Sample-Punkte."""
        # Bau eine Union-Query: fuer jeden Punkt die naechsten Wege suchen
        around_parts = "\n".join(
            f'way["highway"](around:30,{pt["lat"]},{pt["lng"]});' for pt in sampled_points
        )
        query = f"[out:json][timeout:15];({around_parts});out tags;"

        data = await self.client.post_form(
            "/interpreter",
            data={"data": query},
        )
        if not data or "elements" not in data:
            return []

        # Sammle alle surface-Tags (Duplikate = haeufiger auf der Route)
        surfaces: list[str] = []
        seen_ids: set[int] = set()
        for element in data["elements"]:
            eid = element.get("id", 0)
            if eid in seen_ids:
                continue
            seen_ids.add(eid)
            surface = element.get("tags", {}).get("surface")
            if surface:
                surfaces.append(surface)

        return surfaces


overpass_client = OverpassClient()
