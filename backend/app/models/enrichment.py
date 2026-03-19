"""Pydantic Schemas fuer Session-Enrichment (externe APIs)."""

from pydantic import BaseModel


class WeatherData(BaseModel):
    """Wetterdaten fuer eine Session (Open-Meteo)."""

    temperature_c: float
    humidity_pct: float
    wind_speed_kmh: float
    precipitation_mm: float
    weather_code: int  # WMO-Code
    weather_label: str  # Deutsch: "Klar", "Bewölkt", etc.


class AirQualityData(BaseModel):
    """Luftqualitaet und UV-Index (Open-Meteo)."""

    european_aqi: int
    pm2_5: float
    pm10: float
    uv_index: float
    aqi_label: str  # "Gut", "Mäßig", etc.
    uv_label: str  # "Niedrig", "Hoch", etc.


# --- WMO Weather Code Mapping ---

WMO_LABELS: dict[int, str] = {
    0: "Klar",
    1: "Überwiegend klar",
    2: "Teilweise bewölkt",
    3: "Bewölkt",
    45: "Nebel",
    48: "Nebel mit Reif",
    51: "Leichter Nieselregen",
    53: "Mäßiger Nieselregen",
    55: "Starker Nieselregen",
    56: "Gefrierender Nieselregen",
    57: "Starker gefrierender Nieselregen",
    61: "Leichter Regen",
    63: "Mäßiger Regen",
    65: "Starker Regen",
    66: "Gefrierender Regen",
    67: "Starker gefrierender Regen",
    71: "Leichter Schneefall",
    73: "Mäßiger Schneefall",
    75: "Starker Schneefall",
    77: "Schneegriesel",
    80: "Leichte Regenschauer",
    81: "Mäßige Regenschauer",
    82: "Starke Regenschauer",
    85: "Leichte Schneeschauer",
    86: "Starke Schneeschauer",
    95: "Gewitter",
    96: "Gewitter mit leichtem Hagel",
    99: "Gewitter mit starkem Hagel",
}


def wmo_to_label(code: int) -> str:
    """WMO-Code in deutschen Wetter-Label umwandeln."""
    return WMO_LABELS.get(code, f"Code {code}")


# --- AQI Label Mapping ---


def aqi_to_label(aqi: int) -> str:
    """European AQI in deutsches Label umwandeln."""
    if aqi <= 20:
        return "Sehr gut"
    if aqi <= 40:
        return "Gut"
    if aqi <= 60:
        return "Mäßig"
    if aqi <= 80:
        return "Schlecht"
    if aqi <= 100:
        return "Sehr schlecht"
    return "Gefährlich"


def uv_to_label(uv: float) -> str:
    """UV-Index in deutsches Label umwandeln."""
    if uv <= 2:
        return "Niedrig"
    if uv <= 5:
        return "Mäßig"
    if uv <= 7:
        return "Hoch"
    if uv <= 10:
        return "Sehr hoch"
    return "Extrem"
