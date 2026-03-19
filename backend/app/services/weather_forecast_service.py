"""Wetter-Forecast fuer den Wochenplan (7-Tage Open-Meteo Daily)."""

import json
import logging
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.database.models import WorkoutModel
from app.infrastructure.external.http_client import ExternalAPIClient
from app.models.enrichment import aqi_to_label, wmo_to_label
from app.models.weekly_plan import DayWeatherForecast

logger = logging.getLogger(__name__)


class WeatherForecastService:
    """7-Tage Wetter-Forecast fuer den Wochenplan."""

    def __init__(self) -> None:
        self.weather_client = ExternalAPIClient(
            base_url="https://api.open-meteo.com/v1",
            timeout=settings.open_meteo_timeout,
        )
        self.aq_client = ExternalAPIClient(
            base_url="https://air-quality-api.open-meteo.com/v1",
            timeout=settings.open_meteo_timeout,
        )

    async def get_week_forecast(
        self, week_start: date, db: AsyncSession
    ) -> dict[int, DayWeatherForecast]:
        """Holt 7-Tage Forecast. Gibt dict[day_of_week, forecast] zurueck."""
        if not settings.enrichment_enabled:
            return {}

        lat, lon = await self._get_training_location(db)
        if lat is None or lon is None:
            return {}

        week_end = week_start + timedelta(days=6)
        start_str = week_start.isoformat()
        end_str = week_end.isoformat()

        # Wetter + AQI parallel wäre besser, aber sequentiell ist einfacher
        weather_data = await self.weather_client.get(
            "/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "daily": (
                    "temperature_2m_min,temperature_2m_max,"
                    "weather_code,precipitation_sum,wind_speed_10m_max"
                ),
                "start_date": start_str,
                "end_date": end_str,
                "timezone": "auto",
            },
        )

        aq_data = await self.aq_client.get(
            "/air-quality",
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "european_aqi",
                "start_date": start_str,
                "end_date": end_str,
                "timezone": "auto",
            },
        )

        return self._parse_forecasts(weather_data, aq_data, week_start)

    def _parse_forecasts(
        self,
        weather_data: dict | None,
        aq_data: dict | None,
        week_start: date,
    ) -> dict[int, DayWeatherForecast]:
        """Parsed API-Responses in DayWeatherForecast pro Tag."""
        result: dict[int, DayWeatherForecast] = {}

        if not weather_data or "daily" not in weather_data:
            return result

        daily = weather_data["daily"]
        dates = daily.get("time", [])

        # AQI: Tages-Durchschnitt aus stündlichen Werten
        daily_aqi = self._aggregate_daily_aqi(aq_data, len(dates))

        for i, date_str in enumerate(dates):
            try:
                day_date = date.fromisoformat(date_str)
                day_of_week = (day_date - week_start).days

                if day_of_week < 0 or day_of_week > 6:
                    continue

                code = int(daily["weather_code"][i] or 0)
                aqi_val = daily_aqi.get(i)

                result[day_of_week] = DayWeatherForecast(
                    temperature_min=float(daily["temperature_2m_min"][i] or 0),
                    temperature_max=float(daily["temperature_2m_max"][i] or 0),
                    weather_label=wmo_to_label(code),
                    weather_code=code,
                    precipitation_mm=float(daily["precipitation_sum"][i] or 0),
                    wind_speed_max_kmh=float(daily["wind_speed_10m_max"][i] or 0),
                    aqi=aqi_val,
                    aqi_label=aqi_to_label(aqi_val) if aqi_val else None,
                )
            except (IndexError, TypeError, ValueError) as e:
                logger.warning("Fehler beim Parsen des Forecasts fuer Tag %d: %s", i, e)

        return result

    def _aggregate_daily_aqi(self, aq_data: dict | None, num_days: int) -> dict[int, int]:
        """Berechnet Tages-Durchschnitt AQI aus stündlichen Werten."""
        if not aq_data or "hourly" not in aq_data:
            return {}

        hourly_aqi = aq_data["hourly"].get("european_aqi", [])
        result: dict[int, int] = {}

        for day_idx in range(num_days):
            start_h = day_idx * 24
            end_h = start_h + 24
            day_values = [v for v in hourly_aqi[start_h:end_h] if v is not None]
            if day_values:
                result[day_idx] = round(sum(day_values) / len(day_values))

        return result

    async def _get_training_location(self, db: AsyncSession) -> tuple[float | None, float | None]:
        """Ermittelt die übliche Trainings-Location aus den letzten Sessions."""
        # Letzte Session mit GPS-Daten und Location nehmen
        result = await db.execute(
            select(WorkoutModel)
            .where(
                WorkoutModel.has_gps.is_(True),
                WorkoutModel.location_name.isnot(None),
                WorkoutModel.gps_track_json.isnot(None),
            )
            .order_by(WorkoutModel.date.desc())
            .limit(1)
        )
        workout = result.scalar_one_or_none()
        if not workout or not workout.gps_track_json:
            return None, None

        try:
            track = json.loads(str(workout.gps_track_json))
            points = track.get("points", [])
            if points:
                mid = points[len(points) // 2]
                return mid.get("lat"), mid.get("lng")
            start = track.get("start_location")
            if start:
                return start.get("lat"), start.get("lng")
        except json.JSONDecodeError:
            pass

        return None, None


weather_forecast_service = WeatherForecastService()
