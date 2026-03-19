"""Open-Meteo Elevation API Client — Hoehendaten fuer GPS-Punkte."""

import logging

from app.core.config import settings
from app.infrastructure.external.http_client import ExternalAPIClient

logger = logging.getLogger(__name__)

BATCH_SIZE = 100


class OpenMeteoElevationClient:
    """Hoehendaten via Open-Meteo Elevation API (Copernicus DEM, kostenlos)."""

    def __init__(self) -> None:
        self.client = ExternalAPIClient(
            base_url="https://api.open-meteo.com/v1",
            timeout=settings.open_meteo_timeout,
        )

    async def get_elevations(
        self,
        points: list[dict],
    ) -> list[float] | None:
        """Hoehen fuer GPS-Punkte in Batches von 100 abrufen."""
        if not points:
            return None

        all_elevations: list[float] = []
        for i in range(0, len(points), BATCH_SIZE):
            batch = points[i : i + BATCH_SIZE]
            lats = [str(p["lat"]) for p in batch]
            lons = [str(p["lng"]) for p in batch]

            data = await self.client.get(
                "/elevation",
                params={
                    "latitude": ",".join(lats),
                    "longitude": ",".join(lons),
                },
            )
            if not data or "elevation" not in data:
                return None

            all_elevations.extend(data["elevation"])

        return all_elevations

    async def fill_missing_elevation(self, gps_track: dict) -> bool:
        """Fehlende alt-Felder in GPS-Punkten ergaenzen. Gibt True zurück wenn korrigiert."""
        points = gps_track.get("points", [])
        if not points:
            return False

        # Prüfe ob Elevation fehlt
        missing = [p for p in points if p.get("alt") is None]
        if not missing:
            return False

        # Bei vielen Punkten samplen und interpolieren
        if len(points) > BATCH_SIZE:
            return await self._fill_sampled(points, gps_track)

        elevations = await self.get_elevations(points)
        if not elevations:
            return False

        for point, elev in zip(points, elevations):
            point["alt"] = round(elev, 1)

        self._recalculate_ascent_descent(gps_track)
        return True

    async def _fill_sampled(self, points: list[dict], gps_track: dict) -> bool:
        """Fuer grosse Tracks: jeden N-ten Punkt samplen, Rest interpolieren."""
        step = max(1, len(points) // BATCH_SIZE)
        sampled_indices = list(range(0, len(points), step))
        # Letzten Punkt immer einbeziehen
        if sampled_indices[-1] != len(points) - 1:
            sampled_indices.append(len(points) - 1)

        sampled_points = [points[i] for i in sampled_indices]
        elevations = await self.get_elevations(sampled_points)
        if not elevations:
            return False

        # Sampled-Werte setzen
        for idx, elev in zip(sampled_indices, elevations):
            points[idx]["alt"] = round(elev, 1)

        # Zwischen Samples linear interpolieren
        for i in range(len(sampled_indices) - 1):
            start_idx = sampled_indices[i]
            end_idx = sampled_indices[i + 1]
            start_elev = points[start_idx]["alt"]
            end_elev = points[end_idx]["alt"]
            span = end_idx - start_idx

            for j in range(1, span):
                fraction = j / span
                interp = start_elev + (end_elev - start_elev) * fraction
                points[start_idx + j]["alt"] = round(interp, 1)

        self._recalculate_ascent_descent(gps_track)
        return True

    def _recalculate_ascent_descent(self, gps_track: dict) -> None:
        """Ascent/Descent aus aktualisierten alt-Werten neu berechnen."""
        points = gps_track.get("points", [])
        ascent = 0.0
        descent = 0.0
        prev_alt = None

        for p in points:
            alt = p.get("alt")
            if alt is not None and prev_alt is not None:
                diff = alt - prev_alt
                if diff > 0:
                    ascent += diff
                else:
                    descent += abs(diff)
            prev_alt = alt

        gps_track["total_ascent_m"] = round(ascent, 1)
        gps_track["total_descent_m"] = round(descent, 1)
