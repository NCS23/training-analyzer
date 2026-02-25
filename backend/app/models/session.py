"""Pydantic Schemas fuer Session API."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.infrastructure.database.models import WorkoutModel


# --- Response Schemas ---


class LapResponse(BaseModel):
    """Einzelner Lap in der API-Antwort."""

    lap_number: int
    duration_seconds: int
    duration_formatted: str
    distance_km: Optional[float] = None
    pace_min_per_km: Optional[float] = None
    pace_formatted: Optional[str] = None
    avg_hr_bpm: Optional[int] = None
    max_hr_bpm: Optional[int] = None
    min_hr_bpm: Optional[int] = None
    avg_cadence_spm: Optional[int] = None
    suggested_type: Optional[str] = None
    confidence: Optional[str] = None
    user_override: Optional[str] = None


class HRZoneResponse(BaseModel):
    """HF-Zone."""

    seconds: int
    percentage: float
    label: str


class HRZonesResponse(BaseModel):
    """HF-Zonen Verteilung."""

    zone_1_recovery: HRZoneResponse
    zone_2_base: HRZoneResponse
    zone_3_tempo: HRZoneResponse


class SessionSummaryResponse(BaseModel):
    """Zusammenfassung einer Session."""

    total_duration_seconds: int
    total_duration_formatted: str
    total_distance_km: Optional[float] = None
    avg_pace_min_per_km: Optional[float] = None
    avg_pace_formatted: Optional[str] = None
    avg_hr_bpm: Optional[int] = None
    max_hr_bpm: Optional[int] = None
    min_hr_bpm: Optional[int] = None
    avg_cadence_spm: Optional[int] = None


class SessionResponse(BaseModel):
    """Vollstaendige Session-Antwort."""

    id: int
    date: date
    workout_type: str
    subtype: Optional[str] = None
    duration_sec: Optional[int] = None
    distance_km: Optional[float] = None
    pace: Optional[str] = None
    hr_avg: Optional[int] = None
    hr_max: Optional[int] = None
    hr_min: Optional[int] = None
    cadence_avg: Optional[int] = None
    notes: Optional[str] = None
    laps: Optional[list[LapResponse]] = None
    hr_zones: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db(cls, model: WorkoutModel) -> SessionResponse:
        """Erstellt SessionResponse aus DB-Model."""
        laps = None
        if model.laps_json:
            laps_raw = json.loads(str(model.laps_json))
            laps = [LapResponse(**lap) for lap in laps_raw]

        hr_zones = None
        if model.hr_zones_json:
            hr_zones = json.loads(str(model.hr_zones_json))

        model_date = model.date  # type: ignore[assignment]
        session_date: date = (
            model_date.date() if isinstance(model_date, datetime) else model_date  # type: ignore[assignment]
        )

        return cls(
            id=int(model.id),  # type: ignore[arg-type]
            date=session_date,
            workout_type=str(model.workout_type),
            subtype=model.subtype if model.subtype is None else str(model.subtype),
            duration_sec=int(model.duration_sec) if model.duration_sec else None,  # type: ignore[arg-type]
            distance_km=float(model.distance_km) if model.distance_km else None,  # type: ignore[arg-type]
            pace=str(model.pace) if model.pace else None,
            hr_avg=int(model.hr_avg) if model.hr_avg else None,  # type: ignore[arg-type]
            hr_max=int(model.hr_max) if model.hr_max else None,  # type: ignore[arg-type]
            hr_min=int(model.hr_min) if model.hr_min else None,  # type: ignore[arg-type]
            cadence_avg=int(model.cadence_avg) if model.cadence_avg else None,  # type: ignore[arg-type]
            notes=str(model.notes) if model.notes else None,
            laps=laps,
            hr_zones=hr_zones,
            created_at=model.created_at,  # type: ignore[arg-type]
            updated_at=model.updated_at,  # type: ignore[arg-type]
        )


class SessionListItem(BaseModel):
    """Kurzformat fuer Session-Liste."""

    id: int
    date: date
    workout_type: str
    subtype: Optional[str] = None
    duration_sec: Optional[int] = None
    distance_km: Optional[float] = None
    pace: Optional[str] = None
    hr_avg: Optional[int] = None

    @classmethod
    def from_db(cls, model: WorkoutModel) -> SessionListItem:
        model_date = model.date  # type: ignore[assignment]
        session_date: date = (
            model_date.date() if isinstance(model_date, datetime) else model_date  # type: ignore[assignment]
        )

        return cls(
            id=int(model.id),  # type: ignore[arg-type]
            date=session_date,
            workout_type=str(model.workout_type),
            subtype=model.subtype if model.subtype is None else str(model.subtype),
            duration_sec=int(model.duration_sec) if model.duration_sec else None,  # type: ignore[arg-type]
            distance_km=float(model.distance_km) if model.distance_km else None,  # type: ignore[arg-type]
            pace=str(model.pace) if model.pace else None,
            hr_avg=int(model.hr_avg) if model.hr_avg else None,  # type: ignore[arg-type]
        )


class SessionListResponse(BaseModel):
    """Paginierte Session-Liste."""

    sessions: list[SessionListItem]
    total: int
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)


class SessionUploadResponse(BaseModel):
    """Antwort nach erfolgreichem Upload."""

    success: bool
    session_id: Optional[int] = None
    data: Optional[dict] = None
    errors: Optional[list[str]] = None
    metadata: Optional[dict] = None


# --- Request Schemas ---


class LapOverride(BaseModel):
    """Einzelner Lap-Override vom User."""

    lap_number: int
    user_override: str


class LapOverrideRequest(BaseModel):
    """Request fuer Lap-Type Overrides."""

    overrides: list[LapOverride]


class LapOverrideResponse(BaseModel):
    """Antwort nach Lap-Override Update."""

    success: bool
    laps: list[LapResponse]
    summary_working: Optional[SessionSummaryResponse] = None
    hr_zones_working: Optional[dict] = None
