"""Open-Meteo Weather API Client — historisches Wetter + Forecast."""

import logging
from datetime import datetime

from app.core.config import settings
from app.infrastructure.external.http_client import ExternalAPIClient
from app.models.enrichment import WeatherData, wmo_to_label

logger = logging.getLogger(__name__)


class OpenMeteoWeatherClient:
    """Wetterdaten von Open-Meteo (kostenlos, kein API-Key)."""

    HOURLY_PARAMS = "temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation,weather_code"

    def __init__(self) -> None:
        self.client = ExternalAPIClient(
            base_url="https://api.open-meteo.com/v1",
            timeout=settings.open_meteo_timeout,
        )

    async def get_historical(self, lat: float, lon: float, dt: datetime) -> WeatherData | None:
        """Historisches Wetter — Archive-API mit Forecast-Fallback (letzte ~5 Tage)."""
        date_str = dt.strftime("%Y-%m-%d")
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": self.HOURLY_PARAMS,
            "start_date": date_str,
            "end_date": date_str,
            "timezone": "auto",
        }
        # Archive-API zuerst (hat Daten ab ~5 Tage Verzögerung)
        data = await self.client.get("/archive", params=params)
        result = self._extract_closest_hour(data, dt)
        if result:
            return result

        # Fallback: Forecast-API deckt letzte ~2 Wochen + 7 Tage Zukunft ab
        data = await self.client.get("/forecast", params=params)
        return self._extract_closest_hour(data, dt)

    async def get_forecast(self, lat: float, lon: float, dt: datetime) -> WeatherData | None:
        """Wetter-Forecast fuer geplante Sessions."""
        date_str = dt.strftime("%Y-%m-%d")
        data = await self.client.get(
            "/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": self.HOURLY_PARAMS,
                "start_date": date_str,
                "end_date": date_str,
                "timezone": "auto",
            },
        )
        return self._extract_closest_hour(data, dt)

    def _extract_closest_hour(self, data: dict | None, dt: datetime) -> WeatherData | None:
        """Extrahiert den naechstliegenden Stundenwert."""
        if not data or "hourly" not in data:
            return None

        hourly = data["hourly"]
        times = hourly.get("time", [])
        if not times:
            return None

        # Finde naechste Stunde zum Session-Zeitpunkt
        target_hour = dt.hour
        idx = min(target_hour, len(times) - 1)

        try:
            weather_code = int(hourly["weather_code"][idx] or 0)
            return WeatherData(
                temperature_c=float(hourly["temperature_2m"][idx] or 0),
                humidity_pct=float(hourly["relative_humidity_2m"][idx] or 0),
                wind_speed_kmh=float(hourly["wind_speed_10m"][idx] or 0),
                precipitation_mm=float(hourly["precipitation"][idx] or 0),
                weather_code=weather_code,
                weather_label=wmo_to_label(weather_code),
            )
        except (IndexError, TypeError, ValueError) as e:
            logger.warning("Fehler beim Parsen der Wetterdaten: %s", e)
            return None
