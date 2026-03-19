"""Nominatim Reverse Geocoding Client — Routennamen aus Koordinaten."""

import logging

from app.core.config import settings
from app.infrastructure.external.http_client import ExternalAPIClient

logger = logging.getLogger(__name__)


class NominatimClient:
    """Reverse Geocoding via OpenStreetMap Nominatim (kostenlos, 1 req/s)."""

    def __init__(self) -> None:
        self.client = ExternalAPIClient(
            base_url="https://nominatim.openstreetmap.org",
            timeout=settings.open_meteo_timeout,
            rate_limit_delay=settings.nominatim_rate_limit_ms / 1000,
            user_agent=settings.nominatim_user_agent,
        )

    async def reverse_geocode(self, lat: float, lon: float) -> str | None:
        """Koordinaten in Ortsnamen umwandeln (z.B. 'Alsterpark, Hamburg')."""
        data = await self.client.get(
            "/reverse",
            params={
                "lat": lat,
                "lon": lon,
                "format": "json",
                "zoom": 14,
                "accept-language": "de",
            },
        )
        if not data or "address" not in data:
            return None

        return self._build_location_name(data["address"], data.get("display_name", ""))

    def _build_location_name(self, address: dict, display_name: str) -> str:
        """Baut einen kurzen Ortsnamen aus der Nominatim-Adresse."""
        # Spezifischen Ort finden (Park, Wald, Stadtteil)
        place = None
        for key in ("leisure", "park", "wood", "suburb", "neighbourhood", "hamlet"):
            if key in address:
                place = address[key]
                break

        # Stadt/Gemeinde
        city = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
        )

        if place and city:
            return f"{place}, {city}"
        if city:
            return city
        if place:
            return place

        # Fallback: display_name kürzen
        return display_name[:100].rsplit(",", 1)[0] if display_name else ""
