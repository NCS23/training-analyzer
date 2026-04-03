"""Pacing-Strategie Generator API — km-genaue Pace-Empfehlungen."""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.infrastructure.database.models import (
    PacingStrategyModel,
    PlannedSessionModel,
    RaceGoalModel,
    UserModel,
    WeeklyPlanDayModel,
)
from app.infrastructure.database.session import get_db
from app.infrastructure.external.http_client import ExternalAPIClient
from app.models.enrichment import wmo_to_label
from app.models.pacing import (
    ElevationSegment,
    KmPacingSplit,
    PacingRecommendationRequest,
    PacingRecommendationResponse,
    PacingRequest,
    PacingResponse,
    PacingToWeeklyPlanRequest,
    PacingToWeeklyPlanResponse,
    RaceDayWeatherResponse,
    SavedPacingStrategyListResponse,
    SavedPacingStrategyResponse,
    WeatherAdjustment,
)
from app.services.fit_export import export_template_to_fit
from app.services.gpx_elevation_parser import parse_gpx_elevation
from app.services.pacing_recommendation import recommend_pacing
from app.services.pacing_strategy import generate_pacing_strategy, pacing_splits_to_segments

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
    current_user: UserModel = Depends(get_current_user),
) -> PacingResponse:
    """Generiert eine Pacing-Strategie basierend auf Zielzeit, Hoehenprofil und Wetter."""
    # Wenn goal_id angegeben: Distanz und Zielzeit aus dem Goal laden
    if body.goal_id is not None:
        result = await db.execute(
            select(RaceGoalModel).where(
                RaceGoalModel.id == body.goal_id,
                RaceGoalModel.user_id == current_user.id,
            )
        )
        goal = result.scalar_one_or_none()
        if goal is None:
            raise HTTPException(status_code=404, detail="Ziel nicht gefunden")
        body = body.model_copy(
            update={
                "distance_km": goal.distance_km,
                "target_time_seconds": goal.target_time_seconds,
            }
        )

    pacing = generate_pacing_strategy(body)

    # Auto-Save: Strategie am Ziel speichern wenn goal_id vorhanden
    if body.goal_id is not None:
        await _save_pacing_strategy(
            db, body.goal_id, pacing, body.elevation_preset, current_user.id
        )

    return pacing


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
async def recommend_pacing_endpoint(
    body: PacingRecommendationRequest,
) -> PacingRecommendationResponse:
    """Evidenzbasierte Empfehlung fuer die optimale Pacing-Strategie."""
    return recommend_pacing(body)


@router.post("/parse-gpx", response_model=list[ElevationSegment])
async def parse_gpx(file: UploadFile) -> list[ElevationSegment]:
    """Parst eine GPX-Datei und gibt pro-km Höhenprofil zurück."""
    if not file.filename or not file.filename.lower().endswith(".gpx"):
        raise HTTPException(status_code=400, detail="Nur GPX-Dateien werden unterstützt")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10 MB Limit
        raise HTTPException(status_code=400, detail="Datei zu groß (max. 10 MB)")

    try:
        return parse_gpx_elevation(content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("GPX-Parsing fehlgeschlagen: %s", e)
        raise HTTPException(status_code=400, detail="GPX-Datei konnte nicht gelesen werden") from e


@router.post("/export-fit")
async def export_pacing_fit(
    body: PacingRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> Response:
    """Exportiert eine Pacing-Strategie als FIT-Workout-Datei fuer GPS-Uhren."""
    # Goal-ID Aufloesung (wie bei /generate)
    if body.goal_id is not None:
        result = await db.execute(
            select(RaceGoalModel).where(
                RaceGoalModel.id == body.goal_id,
                RaceGoalModel.user_id == current_user.id,
            )
        )
        goal = result.scalar_one_or_none()
        if goal is None:
            raise HTTPException(status_code=404, detail="Ziel nicht gefunden")
        body = body.model_copy(
            update={
                "distance_km": goal.distance_km,
                "target_time_seconds": goal.target_time_seconds,
            }
        )

    pacing = generate_pacing_strategy(body)
    segments = pacing_splits_to_segments(pacing.splits)

    if not segments:
        raise HTTPException(status_code=422, detail="Keine Segmente fuer FIT-Export")

    workout_name = f"{pacing.strategy_label} {pacing.distance_km}km"
    fit_bytes = export_template_to_fit(workout_name, segments)

    safe_name = workout_name.replace(" ", "-").lower()
    filename = f"pacing-{safe_name}.fit"

    return Response(
        content=fit_bytes,
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/to-weekly-plan", response_model=PacingToWeeklyPlanResponse)
async def transfer_pacing_to_weekly_plan(
    body: PacingToWeeklyPlanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> PacingToWeeklyPlanResponse:
    """Uebernimmt eine Pacing-Strategie als Wettkampf-Session in den Wochenplan."""
    # 1) Goal laden → race_date
    result = await db.execute(
        select(RaceGoalModel).where(
            RaceGoalModel.id == body.goal_id,
            RaceGoalModel.user_id == current_user.id,
        )
    )
    goal = result.scalar_one_or_none()
    if goal is None:
        raise HTTPException(status_code=404, detail="Ziel nicht gefunden")

    race_date: date = goal.race_date
    pacing_req = body.pacing_request.model_copy(
        update={
            "distance_km": goal.distance_km,
            "target_time_seconds": goal.target_time_seconds,
        }
    )

    # 2) Pacing generieren → Segments
    pacing = generate_pacing_strategy(pacing_req)
    segments = pacing_splits_to_segments(pacing.splits)

    # 3) week_start (Montag) + day_of_week berechnen
    # Python: weekday() 0=Mon..6=Sun  →  passt zu unserem Schema
    day_of_week = race_date.weekday()
    week_start = race_date - timedelta(days=day_of_week)

    # 4) WeeklyPlanDay finden oder erstellen
    day_result = await db.execute(
        select(WeeklyPlanDayModel).where(
            WeeklyPlanDayModel.week_start == week_start,
            WeeklyPlanDayModel.day_of_week == day_of_week,
        )
    )
    day_model = day_result.scalar_one_or_none()

    if day_model is None:
        day_model = WeeklyPlanDayModel(
            week_start=week_start,
            day_of_week=day_of_week,
            is_rest_day=False,
            user_id=current_user.id,
        )
        db.add(day_model)
        await db.flush()  # ID generieren

    # 5) RunDetails via Pydantic Model bauen (Validatoren berechnen top-level Felder)
    from app.models.weekly_plan import RunDetails

    run_details_model = RunDetails(run_type="race", segments=segments)
    run_details = run_details_model.model_dump(exclude_none=True)

    # 6) Existierende Race-Session suchen (Duplikat-Erkennung)
    sessions_result = await db.execute(
        select(PlannedSessionModel).where(PlannedSessionModel.day_id == day_model.id)
    )
    existing_sessions = sessions_result.scalars().all()

    race_session: PlannedSessionModel | None = None
    for sess in existing_sessions:
        if sess.training_type == "running" and sess.run_details_json:
            try:
                details = json.loads(sess.run_details_json)
                if details.get("run_type") == "race":
                    race_session = sess
                    break
            except json.JSONDecodeError:
                continue

    run_details_json = json.dumps(run_details, ensure_ascii=False)
    notes = (
        f"Pacing: {pacing.strategy_label} {pacing.distance_km}km — {pacing.target_time_formatted}"
    )

    if race_session:
        # Update
        race_session.run_details_json = run_details_json
        race_session.notes = notes
    else:
        # Neu erstellen
        max_pos = max((s.position for s in existing_sessions), default=-1)
        race_session = PlannedSessionModel(
            day_id=day_model.id,
            position=max_pos + 1,
            training_type="running",
            run_details_json=run_details_json,
            notes=notes,
            status="active",
            user_id=current_user.id,
        )
        db.add(race_session)

    await db.commit()
    await db.refresh(race_session)

    return PacingToWeeklyPlanResponse(
        entry_id=race_session.id,
        race_date=race_date.isoformat(),
        message=f"Pacing-Strategie für {race_date.strftime('%d.%m.%Y')} übernommen",
    )


def _safe_float(value: object) -> float | None:
    """Konvertiert einen Wert sicher zu float oder gibt None zurueck."""
    if value is None:
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Gespeicherte Pacing-Strategien (#528)
# ---------------------------------------------------------------------------


async def _save_pacing_strategy(
    db: AsyncSession,
    goal_id: int,
    pacing: PacingResponse,
    elevation_preset: str | None,
    user_id: int | None = None,
) -> PacingStrategyModel:
    """Speichert eine generierte Pacing-Strategie in der DB."""
    model = PacingStrategyModel(
        goal_id=goal_id,
        user_id=user_id,
        strategy=pacing.strategy,
        strategy_label=pacing.strategy_label,
        distance_km=pacing.distance_km,
        target_time_seconds=pacing.target_time_seconds,
        target_time_formatted=pacing.target_time_formatted,
        avg_pace_sec_per_km=pacing.avg_pace_sec_per_km,
        avg_pace_formatted=pacing.avg_pace_formatted,
        splits_json=json.dumps([s.model_dump() for s in pacing.splits], ensure_ascii=False),
        weather_json=(
            json.dumps(pacing.weather_adjustment.model_dump(), ensure_ascii=False)
            if pacing.weather_adjustment
            else None
        ),
        elevation_preset=elevation_preset,
        notes_json=json.dumps(pacing.notes, ensure_ascii=False) if pacing.notes else None,
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


def _db_to_response(model: PacingStrategyModel) -> SavedPacingStrategyResponse:
    """Konvertiert ein DB-Modell in ein Response-Schema."""
    splits = [KmPacingSplit(**s) for s in json.loads(model.splits_json)]
    weather = WeatherAdjustment(**json.loads(model.weather_json)) if model.weather_json else None
    notes: list[str] = json.loads(model.notes_json) if model.notes_json else []

    return SavedPacingStrategyResponse(
        id=model.id,
        goal_id=model.goal_id,
        strategy=model.strategy,
        strategy_label=model.strategy_label,
        distance_km=model.distance_km,
        target_time_seconds=model.target_time_seconds,
        target_time_formatted=model.target_time_formatted,
        avg_pace_sec_per_km=model.avg_pace_sec_per_km,
        avg_pace_formatted=model.avg_pace_formatted,
        splits=splits,
        weather_adjustment=weather,
        elevation_preset=model.elevation_preset,
        notes=notes,
        created_at=model.created_at.isoformat() if model.created_at else "",
    )


@router.get(
    "/goals/{goal_id}/strategies",
    response_model=SavedPacingStrategyListResponse,
)
async def list_pacing_strategies(
    goal_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> SavedPacingStrategyListResponse:
    """Listet alle gespeicherten Pacing-Strategien fuer ein Ziel."""
    result = await db.execute(
        select(PacingStrategyModel)
        .where(
            PacingStrategyModel.goal_id == goal_id,
            PacingStrategyModel.user_id == current_user.id,
        )
        .order_by(PacingStrategyModel.created_at.desc())
    )
    models = result.scalars().all()
    return SavedPacingStrategyListResponse(strategies=[_db_to_response(m) for m in models])


@router.get(
    "/goals/{goal_id}/strategies/{strategy_id}",
    response_model=SavedPacingStrategyResponse,
)
async def get_pacing_strategy(
    goal_id: int,
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> SavedPacingStrategyResponse:
    """Gibt eine einzelne gespeicherte Pacing-Strategie zurueck."""
    result = await db.execute(
        select(PacingStrategyModel).where(
            PacingStrategyModel.id == strategy_id,
            PacingStrategyModel.goal_id == goal_id,
            PacingStrategyModel.user_id == current_user.id,
        )
    )
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Strategie nicht gefunden")
    return _db_to_response(model)


@router.delete("/goals/{goal_id}/strategies/{strategy_id}", status_code=204)
async def delete_pacing_strategy(
    goal_id: int,
    strategy_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> None:
    """Loescht eine gespeicherte Pacing-Strategie."""
    result = await db.execute(
        select(PacingStrategyModel).where(
            PacingStrategyModel.id == strategy_id,
            PacingStrategyModel.goal_id == goal_id,
            PacingStrategyModel.user_id == current_user.id,
        )
    )
    model = result.scalar_one_or_none()
    if model is None:
        raise HTTPException(status_code=404, detail="Strategie nicht gefunden")
    await db.delete(model)
    await db.commit()
