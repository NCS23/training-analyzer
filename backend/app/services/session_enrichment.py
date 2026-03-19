"""Session Enrichment Service — koordiniert externe API-Aufrufe."""

import json
import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.infrastructure.database.models import WorkoutModel
from app.infrastructure.external.nominatim import NominatimClient
from app.infrastructure.external.open_meteo_air_quality import OpenMeteoAirQualityClient
from app.infrastructure.external.open_meteo_elevation import OpenMeteoElevationClient
from app.infrastructure.external.open_meteo_weather import OpenMeteoWeatherClient

logger = logging.getLogger(__name__)


class SessionEnrichmentService:
    """Reichert Sessions mit Wetter, Location, Luftqualitaet und Elevation an."""

    def __init__(self) -> None:
        self.weather = OpenMeteoWeatherClient()
        self.geocoder = NominatimClient()
        self.air_quality = OpenMeteoAirQualityClient()
        self.elevation = OpenMeteoElevationClient()

    async def enrich_session(self, workout_id: int, db: AsyncSession) -> None:
        """Einzelne Session mit allen verfuegbaren Daten anreichern."""
        if not settings.enrichment_enabled:
            return

        workout = await db.get(WorkoutModel, workout_id)
        if not workout or not workout.has_gps or not workout.gps_track_json:
            if workout:
                workout.enrichment_status = "skipped"
                await db.commit()
            return

        try:
            gps_track = json.loads(str(workout.gps_track_json))
            lat, lon = self._get_midpoint(gps_track)
            if lat is None or lon is None:
                workout.enrichment_status = "skipped"
                await db.commit()
                return

            session_dt = self._get_session_datetime(workout)
            await self._enrich_weather(workout, lat, lon, session_dt)
            await self._enrich_location(workout, lat, lon)
            await self._enrich_air_quality(workout, lat, lon, session_dt)
            await self._enrich_elevation(workout, gps_track)

            workout.enrichment_status = "enriched"
            await db.commit()
            logger.info("Session %d erfolgreich angereichert", workout_id)

        except Exception:
            logger.exception("Fehler beim Anreichern von Session %d", workout_id)
            workout.enrichment_status = "failed"
            await db.commit()

    async def _enrich_weather(
        self, workout: WorkoutModel, lat: float, lon: float, dt: datetime
    ) -> None:
        if workout.weather_json:
            return
        weather = await self.weather.get_historical(lat, lon, dt)
        if weather:
            workout.weather_json = weather.model_dump_json()

    async def _enrich_location(self, workout: WorkoutModel, lat: float, lon: float) -> None:
        if workout.location_name:
            return
        location = await self.geocoder.reverse_geocode(lat, lon)
        if location:
            workout.location_name = location

    async def _enrich_air_quality(
        self, workout: WorkoutModel, lat: float, lon: float, dt: datetime
    ) -> None:
        if workout.air_quality_json:
            return
        aq = await self.air_quality.get_air_quality(lat, lon, dt)
        if aq:
            workout.air_quality_json = aq.model_dump_json()

    async def _enrich_elevation(self, workout: WorkoutModel, gps_track: dict) -> None:
        if workout.elevation_corrected:
            return
        corrected = await self.elevation.fill_missing_elevation(gps_track)
        if corrected:
            workout.gps_track_json = json.dumps(gps_track)
            workout.elevation_corrected = True

    async def enrich_batch(self, db: AsyncSession, limit: int = 50) -> int:
        """Batch-Enrichment fuer alle pending Sessions. Gibt Anzahl zurück."""
        result = await db.execute(
            select(WorkoutModel.id)
            .where(
                WorkoutModel.enrichment_status == "pending",
                WorkoutModel.has_gps.is_(True),
            )
            .order_by(WorkoutModel.date.asc())
            .limit(limit)
        )
        ids = [row[0] for row in result.all()]

        if not ids:
            return 0

        count = 0
        for workout_id in ids:
            await self.enrich_session(workout_id, db)
            count += 1

        logger.info("Batch-Enrichment: %d/%d Sessions verarbeitet", count, len(ids))
        return count

    def _get_midpoint(self, gps_track: dict) -> tuple[float | None, float | None]:
        """Midpoint der Route berechnen (besser als Start/Ende)."""
        points = gps_track.get("points", [])
        if not points:
            # Fallback auf start_location
            start = gps_track.get("start_location")
            if start:
                return start.get("lat"), start.get("lng")
            return None, None

        mid_idx = len(points) // 2
        return points[mid_idx].get("lat"), points[mid_idx].get("lng")

    def _get_session_datetime(self, workout: WorkoutModel) -> datetime:
        """Session-Datetime ermitteln (fuer Stunden-Matching bei Wetter)."""
        if isinstance(workout.date, datetime):
            return workout.date
        # Falls nur date, nehme 9:00 Uhr als Default
        return datetime.combine(workout.date, datetime.min.time().replace(hour=9))


# Globale Instanz
enrichment_service = SessionEnrichmentService()
