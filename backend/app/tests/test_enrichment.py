"""Tests fuer Session Enrichment (externe APIs)."""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.infrastructure.external.nominatim import NominatimClient
from app.infrastructure.external.open_meteo_air_quality import OpenMeteoAirQualityClient
from app.infrastructure.external.open_meteo_elevation import OpenMeteoElevationClient
from app.infrastructure.external.open_meteo_weather import OpenMeteoWeatherClient
from app.models.enrichment import aqi_to_label, uv_to_label, wmo_to_label

# --- Unit Tests: Label Mappings ---


class TestWMOLabels:
    def test_clear_sky(self) -> None:
        assert wmo_to_label(0) == "Klar"

    def test_rain(self) -> None:
        assert wmo_to_label(61) == "Leichter Regen"

    def test_thunderstorm(self) -> None:
        assert wmo_to_label(95) == "Gewitter"

    def test_unknown_code(self) -> None:
        assert wmo_to_label(999) == "Code 999"


class TestAQILabels:
    def test_very_good(self) -> None:
        assert aqi_to_label(15) == "Sehr gut"

    def test_good(self) -> None:
        assert aqi_to_label(35) == "Gut"

    def test_moderate(self) -> None:
        assert aqi_to_label(55) == "Mäßig"

    def test_poor(self) -> None:
        assert aqi_to_label(75) == "Schlecht"

    def test_dangerous(self) -> None:
        assert aqi_to_label(120) == "Gefährlich"


class TestUVLabels:
    def test_low(self) -> None:
        assert uv_to_label(1.5) == "Niedrig"

    def test_moderate(self) -> None:
        assert uv_to_label(4.0) == "Mäßig"

    def test_high(self) -> None:
        assert uv_to_label(7.0) == "Hoch"

    def test_extreme(self) -> None:
        assert uv_to_label(12.0) == "Extrem"


# --- Weather Client Tests ---


MOCK_WEATHER_RESPONSE = {
    "hourly": {
        "time": [f"2026-03-19T{h:02d}:00" for h in range(24)],
        "temperature_2m": [5.0 + i * 0.5 for i in range(24)],
        "relative_humidity_2m": [80.0 - i for i in range(24)],
        "wind_speed_10m": [10.0 + i * 0.2 for i in range(24)],
        "precipitation": [0.0] * 24,
        "weather_code": [0] * 10 + [2] * 4 + [61] * 5 + [0] * 5,
    }
}


class TestOpenMeteoWeather:
    @pytest.mark.asyncio
    async def test_get_historical(self) -> None:
        client = OpenMeteoWeatherClient()
        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_WEATHER_RESPONSE
            result = await client.get_historical(53.55, 9.99, datetime(2026, 3, 19, 10, 0))

        assert result is not None
        assert result.temperature_c == 10.0  # 5.0 + 10 * 0.5
        assert result.weather_code == 2  # Index 10 → code 2
        assert result.weather_label == "Teilweise bewölkt"

    @pytest.mark.asyncio
    async def test_get_historical_returns_none_on_error(self) -> None:
        client = OpenMeteoWeatherClient()
        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            result = await client.get_historical(53.55, 9.99, datetime(2026, 3, 19, 10, 0))

        assert result is None


# --- Nominatim Client Tests ---


MOCK_NOMINATIM_RESPONSE = {
    "address": {
        "park": "Stadtpark",
        "suburb": "Winterhude",
        "city": "Hamburg",
        "state": "Hamburg",
        "country": "Deutschland",
    },
    "display_name": "Stadtpark, Winterhude, Hamburg, Deutschland",
}


class TestNominatim:
    @pytest.mark.asyncio
    async def test_reverse_geocode(self) -> None:
        client = NominatimClient()
        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_NOMINATIM_RESPONSE
            result = await client.reverse_geocode(53.596, 10.023)

        assert result == "Stadtpark, Hamburg"

    @pytest.mark.asyncio
    async def test_reverse_geocode_city_only(self) -> None:
        client = NominatimClient()
        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {
                "address": {"city": "München", "country": "Deutschland"},
                "display_name": "München, Deutschland",
            }
            result = await client.reverse_geocode(48.137, 11.575)

        assert result == "München"

    @pytest.mark.asyncio
    async def test_reverse_geocode_returns_none_on_error(self) -> None:
        client = NominatimClient()
        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            result = await client.reverse_geocode(53.55, 9.99)

        assert result is None


# --- Air Quality Client Tests ---


MOCK_AQ_RESPONSE = {
    "hourly": {
        "time": [f"2026-03-19T{h:02d}:00" for h in range(24)],
        "european_aqi": [25] * 24,
        "pm2_5": [12.5] * 24,
        "pm10": [18.0] * 24,
        "uv_index": [3.5] * 24,
    }
}


class TestOpenMeteoAirQuality:
    @pytest.mark.asyncio
    async def test_get_air_quality(self) -> None:
        client = OpenMeteoAirQualityClient()
        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = MOCK_AQ_RESPONSE
            result = await client.get_air_quality(53.55, 9.99, datetime(2026, 3, 19, 10, 0))

        assert result is not None
        assert result.european_aqi == 25
        assert result.aqi_label == "Gut"
        assert result.uv_index == 3.5
        assert result.uv_label == "Mäßig"


# --- Elevation Client Tests ---


class TestOpenMeteoElevation:
    @pytest.mark.asyncio
    async def test_get_elevations(self) -> None:
        client = OpenMeteoElevationClient()
        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"elevation": [50.0, 55.0, 60.0]}
            result = await client.get_elevations(
                [
                    {"lat": 53.55, "lng": 9.99},
                    {"lat": 53.56, "lng": 9.98},
                    {"lat": 53.57, "lng": 9.97},
                ]
            )

        assert result == [50.0, 55.0, 60.0]

    @pytest.mark.asyncio
    async def test_fill_missing_elevation(self) -> None:
        client = OpenMeteoElevationClient()
        points: list[dict[str, float]] = [
            {"lat": 53.55, "lng": 9.99, "seconds": 0},
            {"lat": 53.56, "lng": 9.98, "seconds": 60},
            {"lat": 53.57, "lng": 9.97, "seconds": 120},
        ]
        gps_track: dict[str, object] = {
            "points": points,
            "total_ascent_m": 0,
            "total_descent_m": 0,
        }
        with patch.object(client.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = {"elevation": [50.0, 55.0, 52.0]}
            result = await client.fill_missing_elevation(gps_track)

        assert result is True
        assert points[0]["alt"] == 50.0
        assert points[1]["alt"] == 55.0
        assert points[2]["alt"] == 52.0
        assert gps_track["total_ascent_m"] == 5.0
        assert gps_track["total_descent_m"] == 3.0

    @pytest.mark.asyncio
    async def test_fill_skips_existing_elevation(self) -> None:
        client = OpenMeteoElevationClient()
        gps_track = {
            "points": [
                {"lat": 53.55, "lng": 9.99, "alt": 50.0, "seconds": 0},
                {"lat": 53.56, "lng": 9.98, "alt": 55.0, "seconds": 60},
            ],
        }
        result = await client.fill_missing_elevation(gps_track)
        assert result is False  # Keine fehlenden Elevation-Daten
