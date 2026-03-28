"""Pydantic Schemas fuer Pacing-Strategie Generator API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


class ElevationSegment(BaseModel):
    """Hoehenprofil-Daten fuer einen Kilometer."""

    km: int = Field(..., ge=1, description="Kilometer-Nummer (1-basiert)")
    gain_m: float = Field(0.0, ge=0, description="Hoehengewinn in Metern")
    loss_m: float = Field(0.0, ge=0, description="Hoehenverlust in Metern")


class PacingRequest(BaseModel):
    """Request-Schema: Pacing-Strategie generieren."""

    target_time_seconds: int = Field(..., gt=0, description="Zielzeit in Sekunden")
    distance_km: float = Field(..., gt=0, description="Distanz in Kilometern")
    strategy: Literal["even", "negative", "effort_based"] = Field(
        "even", description="Pacing-Strategie"
    )
    elevation_preset: Literal["flat", "rolling", "hilly"] | None = Field(
        None, description="Hoehenprofil-Preset (alternativ zu elevation_segments)"
    )
    elevation_segments: list[ElevationSegment] | None = Field(
        None, description="Manuelles Hoehenprofil pro km"
    )
    temperature_celsius: float | None = Field(None, description="Temperatur in Grad Celsius")
    wind_speed_kmh: float | None = Field(None, ge=0, description="Windgeschwindigkeit in km/h")
    humidity_percent: float | None = Field(
        None, ge=0, le=100, description="Luftfeuchtigkeit in Prozent"
    )
    goal_id: int | None = Field(
        None, description="Optional: Race-Goal-ID zum Vorladen von Distanz/Zielzeit"
    )


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class KmPacingSplit(BaseModel):
    """Pace-Empfehlung fuer einen Kilometer."""

    km: int
    distance_km: float = Field(description="1.0 fuer volle km, <1.0 fuer letzten Abschnitt")
    target_pace_sec_per_km: float
    target_pace_formatted: str  # "5:41"
    cumulative_seconds: int
    cumulative_formatted: str  # "1:14:23"
    elevation_gain_m: float = 0.0
    elevation_loss_m: float = 0.0
    adjustment_note: str | None = None  # z.B. "Bergauf +8s", "Hitze +6s/km"


class WeatherAdjustment(BaseModel):
    """Zusammenfassung der Wetter-Anpassungen."""

    temperature_celsius: float | None = None
    wind_speed_kmh: float | None = None
    humidity_percent: float | None = None
    penalty_sec_per_km: float = 0.0
    description: str = ""  # "Hitze (+6s/km), Gegenwind (+3s/km)"


class PacingResponse(BaseModel):
    """Response-Schema: Generierte Pacing-Strategie."""

    strategy: str
    strategy_label: str  # "Gleichmaessig", "Negative Splits", "Effort-Based"
    distance_km: float
    target_time_seconds: int
    target_time_formatted: str
    avg_pace_sec_per_km: float
    avg_pace_formatted: str
    splits: list[KmPacingSplit]
    weather_adjustment: WeatherAdjustment | None = None
    notes: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Weather Forecast
# ---------------------------------------------------------------------------


class WeatherForecastRequest(BaseModel):
    """Query-Parameter fuer Wetter-Abfrage."""

    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    date: str = Field(..., description="Datum im Format YYYY-MM-DD")


class RaceDayWeatherResponse(BaseModel):
    """Response-Schema: Wetter-Forecast fuer den Wettkampftag."""

    date: str
    temperature_min: float
    temperature_max: float
    temperature_avg: float
    wind_speed_max_kmh: float
    wind_direction_deg: float | None = None
    precipitation_mm: float
    humidity_percent: float | None = None
    weather_label: str


# ---------------------------------------------------------------------------
# KI-Empfehlung
# ---------------------------------------------------------------------------


class PacingRecommendationRequest(BaseModel):
    """Request-Schema: Evidenzbasierte Pacing-Strategie-Empfehlung."""

    race_name: str | None = Field(None, description="Name des Rennens (z.B. Berlin Halbmarathon)")
    distance_km: float = Field(..., gt=0, description="Distanz in Kilometern")
    target_time_seconds: int = Field(..., gt=0, description="Zielzeit in Sekunden")
    experience_level: Literal["beginner", "intermediate", "advanced"] = Field(
        ..., description="Erfahrungslevel"
    )
    temperature_celsius: float | None = Field(
        None, description="Erwartete Temperatur am Renntag in Grad Celsius"
    )
    elevation_preset: Literal["flat", "rolling", "hilly"] | None = Field(
        None, description="Manuell gewaehltes Hoehenprofil-Preset"
    )
    elevation_segments: list[ElevationSegment] | None = Field(
        None, description="Hoehenprofil aus GPX-Upload (pro km)"
    )


class PacingRecommendationResponse(BaseModel):
    """Response-Schema: Evidenzbasierte Empfehlung mit Begruendung."""

    strategy: Literal["even", "negative", "effort_based"]
    elevation_preset: Literal["flat", "rolling", "hilly"] | None
    reasoning: str = Field(description="Evidenzbasierte Begruendung der Empfehlung")


# ---------------------------------------------------------------------------
# Wochenplan-Integration (#518)
# ---------------------------------------------------------------------------


class PacingToWeeklyPlanRequest(BaseModel):
    """Request: Pacing-Strategie in den Wochenplan uebernehmen."""

    goal_id: int = Field(..., description="Race-Goal-ID (bestimmt das Renndatum)")
    pacing_request: PacingRequest


class PacingToWeeklyPlanResponse(BaseModel):
    """Response: Bestaetigung der Uebernahme in den Wochenplan."""

    entry_id: int = Field(description="ID der erstellten/aktualisierten PlannedSession")
    race_date: str = Field(description="Datum des Renntags (ISO)")
    message: str


# ---------------------------------------------------------------------------
# Gespeicherte Pacing-Strategien (#528)
# ---------------------------------------------------------------------------


class SavedPacingStrategyResponse(BaseModel):
    """Response: Gespeicherte Pacing-Strategie."""

    id: int
    goal_id: int
    strategy: str
    strategy_label: str
    distance_km: float
    target_time_seconds: int
    target_time_formatted: str
    avg_pace_sec_per_km: float
    avg_pace_formatted: str
    splits: list[KmPacingSplit]
    weather_adjustment: WeatherAdjustment | None = None
    elevation_preset: str | None = None
    notes: list[str] = Field(default_factory=list)
    created_at: str


class SavedPacingStrategyListResponse(BaseModel):
    """Response: Liste gespeicherter Pacing-Strategien fuer ein Ziel."""

    strategies: list[SavedPacingStrategyResponse]
