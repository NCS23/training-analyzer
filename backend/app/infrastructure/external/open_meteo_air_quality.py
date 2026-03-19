"""Open-Meteo Air Quality API Client — Luftqualitaet + UV-Index."""

import logging
from datetime import datetime

from app.core.config import settings
from app.infrastructure.external.http_client import ExternalAPIClient
from app.models.enrichment import AirQualityData, aqi_to_label, uv_to_label

logger = logging.getLogger(__name__)


class OpenMeteoAirQualityClient:
    """Luftqualitaet und UV-Index von Open-Meteo (kostenlos, kein API-Key)."""

    def __init__(self) -> None:
        self.client = ExternalAPIClient(
            base_url="https://air-quality-api.open-meteo.com/v1",
            timeout=settings.open_meteo_timeout,
        )

    async def get_air_quality(self, lat: float, lon: float, dt: datetime) -> AirQualityData | None:
        """Luftqualitaet + UV-Index fuer Session-Zeitpunkt abrufen."""
        date_str = dt.strftime("%Y-%m-%d")
        data = await self.client.get(
            "/air-quality",
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "european_aqi,pm2_5,pm10,uv_index",
                "start_date": date_str,
                "end_date": date_str,
                "timezone": "auto",
            },
        )
        if not data or "hourly" not in data:
            return None

        hourly = data["hourly"]
        times = hourly.get("time", [])
        if not times:
            return None

        idx = min(dt.hour, len(times) - 1)

        try:
            aqi = int(hourly["european_aqi"][idx] or 0)
            uv = float(hourly["uv_index"][idx] or 0)
            return AirQualityData(
                european_aqi=aqi,
                pm2_5=float(hourly["pm2_5"][idx] or 0),
                pm10=float(hourly["pm10"][idx] or 0),
                uv_index=uv,
                aqi_label=aqi_to_label(aqi),
                uv_label=uv_to_label(uv),
            )
        except (IndexError, TypeError, ValueError) as e:
            logger.warning("Fehler beim Parsen der Luftqualitätsdaten: %s", e)
            return None
