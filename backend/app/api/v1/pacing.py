"""Pacing-Strategie Generator API — km-genaue Pace-Empfehlungen."""

from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key_resolver import resolve_claude_api_key
from app.core.config import settings
from app.infrastructure.database.models import RaceGoalModel
from app.infrastructure.database.session import get_db
from app.infrastructure.external.http_client import ExternalAPIClient
from app.models.enrichment import wmo_to_label
from app.models.pacing import (
    PacingRecommendationRequest,
    PacingRecommendationResponse,
    PacingRequest,
    PacingResponse,
    RaceDayWeatherResponse,
)
from app.services.pacing_recommendation import get_pacing_recommendation
from app.services.pacing_strategy import generate_pacing_strategy

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pacing", tags=["pacing"])

# Open-Meteo Client (wiederverwendet das bestehende Pattern)
_weather_client = ExternalAPIClient(
    base_url="https://api.open-meteo.com/v1",
    timeout=settings.open_meteo_timeout,
)


@router.post("/generate", response_model=PacingResponse)
async def generate_pacing(
    body: PacingRequest,
    db: AsyncSession = Depends(get_db),
) -> PacingResponse:
    """Generiert eine Pacing-Strategie basierend auf Zielzeit, Hoehenprofil und Wetter."""
    # Wenn goal_id angegeben: Distanz und Zielzeit aus dem Goal laden
    if body.goal_id is not None:
        result = await db.execute(select(RaceGoalModel).where(RaceGoalModel.id == body.goal_id))
        goal = result.scalar_one_or_none()
        if goal is None:
            raise HTTPException(status_code=404, detail="Ziel nicht gefunden")
        body = body.model_copy(
            update={
                "distance_km": goal.distance_km,
                "target_time_seconds": goal.target_time_seconds,
            }
        )

    return generate_pacing_strategy(body)


@router.get("/weather-forecast", response_model=RaceDayWeatherResponse)
async def get_weather_forecast(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    forecast_date: str = Query(..., alias="date", description="YYYY-MM-DD"),
) -> RaceDayWeatherResponse:
    """Holt Wetter-Forecast fuer einen bestimmten Tag und Ort (Open-Meteo)."""
    try:
        target_date = date.fromisoformat(forecast_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Ungültiges Datum (YYYY-MM-DD)") from e

    days_ahead = (target_date - date.today()).days
    if days_ahead < 0:
        raise HTTPException(status_code=400, detail="Datum liegt in der Vergangenheit")
    if days_ahead > 16:
        raise HTTPException(
            status_code=400,
            detail="Vorhersage nur bis 16 Tage im Voraus verfügbar",
        )

    data = await _weather_client.get(
        "/forecast",
        params={
            "latitude": lat,
            "longitude": lng,
            "daily": (
                "temperature_2m_min,temperature_2m_max,"
                "weather_code,precipitation_sum,"
                "wind_speed_10m_max,wind_direction_10m_dominant,"
                "relative_humidity_2m_mean"
            ),
            "start_date": target_date.isoformat(),
            "end_date": target_date.isoformat(),
            "timezone": "auto",
        },
    )

    if not data or "daily" not in data:
        raise HTTPException(status_code=502, detail="Wetter-Daten nicht verfügbar")

    daily = data["daily"]
    try:
        t_min = float(daily["temperature_2m_min"][0])
        t_max = float(daily["temperature_2m_max"][0])
        code = int(daily["weather_code"][0] or 0)

        return RaceDayWeatherResponse(
            date=target_date.isoformat(),
            temperature_min=t_min,
            temperature_max=t_max,
            temperature_avg=round((t_min + t_max) / 2, 1),
            wind_speed_max_kmh=float(daily["wind_speed_10m_max"][0] or 0),
            wind_direction_deg=_safe_float(daily.get("wind_direction_10m_dominant", [None])[0]),
            precipitation_mm=float(daily["precipitation_sum"][0] or 0),
            humidity_percent=_safe_float(daily.get("relative_humidity_2m_mean", [None])[0]),
            weather_label=wmo_to_label(code),
        )
    except (IndexError, TypeError, ValueError) as e:
        logger.warning("Fehler beim Parsen des Wetter-Forecasts: %s", e)
        raise HTTPException(status_code=502, detail="Wetter-Daten nicht parsbar") from e


@router.post("/recommend", response_model=PacingRecommendationResponse)
async def recommend_pacing(
    body: PacingRecommendationRequest,
    db: AsyncSession = Depends(get_db),
) -> PacingRecommendationResponse:
    """KI-Empfehlung fuer die optimale Pacing-Strategie."""
    api_key = await resolve_claude_api_key(db)
    if not api_key:
        raise HTTPException(status_code=503, detail="Kein KI-Provider verfügbar")

    try:
        return await get_pacing_recommendation(body, api_key, db)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        logger.error("Pacing-Empfehlung fehlgeschlagen: %s", e)
        raise HTTPException(
            status_code=502, detail="KI-Empfehlung konnte nicht generiert werden"
        ) from e


def _safe_float(value: object) -> float | None:
    """Konvertiert einen Wert sicher zu float oder gibt None zurueck."""
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
