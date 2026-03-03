"""Pydantic Schemas fuer Session API."""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

from app.models.segment import Segment, laps_to_segments

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
    start_seconds: Optional[float] = None
    end_seconds: Optional[float] = None


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


class TrainingTypeInfo(BaseModel):
    """Training Type Klassifizierungsergebnis."""

    auto: Optional[str] = None
    confidence: Optional[int] = None
    override: Optional[str] = None
    effective: Optional[str] = None


class SessionResponse(BaseModel):
    """Vollstaendige Session-Antwort."""

    id: int
    date: date
    workout_type: str
    subtype: Optional[str] = None
    training_type: Optional[TrainingTypeInfo] = None
    duration_sec: Optional[int] = None
    distance_km: Optional[float] = None
    pace: Optional[str] = None
    hr_avg: Optional[int] = None
    hr_max: Optional[int] = None
    hr_min: Optional[int] = None
    cadence_avg: Optional[int] = None
    notes: Optional[str] = None
    rpe: Optional[int] = None
    laps: Optional[list[LapResponse]] = None
    segments: Optional[list[Segment]] = None  # Unified segment model (#133)
    hr_zones: Optional[dict] = None
    exercises: Optional[list] = None
    has_gps: bool = False
    planned_entry_id: Optional[int] = None  # S10: Soll/Ist-Link
    athlete_resting_hr: Optional[int] = None
    athlete_max_hr: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db(cls, model: WorkoutModel) -> SessionResponse:
        """Erstellt SessionResponse aus DB-Model."""
        laps = None
        if model.laps_json:
            laps_raw = json.loads(str(model.laps_json))
            # Compute cumulative start/end seconds for each lap
            elapsed = 0.0
            for lap_dict in laps_raw:
                dur = lap_dict.get("duration_seconds", 0)
                lap_dict["start_seconds"] = elapsed
                lap_dict["end_seconds"] = elapsed + dur
                elapsed += dur
            laps = [LapResponse(**lap) for lap in laps_raw]

        hr_zones = None
        if model.hr_zones_json:
            hr_zones = json.loads(str(model.hr_zones_json))

        exercises = None
        if model.exercises_json:
            exercises = json.loads(str(model.exercises_json))

        model_date = model.date  # type: ignore[assignment]
        session_date: date = (
            model_date.date() if isinstance(model_date, datetime) else model_date  # type: ignore[assignment]
        )

        # Training Type Info
        training_type = None
        auto_type = str(model.training_type_auto) if model.training_type_auto else None
        override_type = str(model.training_type_override) if model.training_type_override else None
        if auto_type or override_type:
            training_type = TrainingTypeInfo(
                auto=auto_type,
                confidence=(
                    int(model.training_type_confidence)  # type: ignore[arg-type]
                    if model.training_type_confidence
                    else None
                ),
                override=override_type,
                effective=override_type or auto_type,
            )

        # Convert laps to unified segments (#133)
        segments = laps_to_segments(laps) if laps else None

        return cls(
            id=int(model.id),  # type: ignore[arg-type]
            date=session_date,
            workout_type=str(model.workout_type),
            subtype=model.subtype if model.subtype is None else str(model.subtype),
            training_type=training_type,
            duration_sec=int(model.duration_sec) if model.duration_sec else None,  # type: ignore[arg-type]
            distance_km=float(model.distance_km) if model.distance_km else None,  # type: ignore[arg-type]
            pace=str(model.pace) if model.pace else None,
            hr_avg=int(model.hr_avg) if model.hr_avg else None,  # type: ignore[arg-type]
            hr_max=int(model.hr_max) if model.hr_max else None,  # type: ignore[arg-type]
            hr_min=int(model.hr_min) if model.hr_min else None,  # type: ignore[arg-type]
            cadence_avg=int(model.cadence_avg) if model.cadence_avg else None,  # type: ignore[arg-type]
            notes=str(model.notes) if model.notes else None,
            rpe=int(model.rpe) if model.rpe else None,  # type: ignore[arg-type]
            laps=laps,
            segments=segments,
            hr_zones=hr_zones,
            exercises=exercises,
            has_gps=bool(model.has_gps),
            planned_entry_id=int(model.planned_entry_id) if model.planned_entry_id else None,  # type: ignore[arg-type]
            athlete_resting_hr=int(model.athlete_resting_hr) if model.athlete_resting_hr else None,  # type: ignore[arg-type]
            athlete_max_hr=int(model.athlete_max_hr) if model.athlete_max_hr else None,  # type: ignore[arg-type]
            created_at=model.created_at,  # type: ignore[arg-type]
            updated_at=model.updated_at,  # type: ignore[arg-type]
        )


class SessionListItem(BaseModel):
    """Kurzformat fuer Session-Liste."""

    id: int
    date: date
    workout_type: str
    subtype: Optional[str] = None
    training_type: Optional[TrainingTypeInfo] = None
    duration_sec: Optional[int] = None
    distance_km: Optional[float] = None
    pace: Optional[str] = None
    hr_avg: Optional[int] = None
    exercises_count: Optional[int] = None
    total_tonnage_kg: Optional[float] = None

    @classmethod
    def from_db(cls, model: WorkoutModel) -> SessionListItem:
        model_date = model.date  # type: ignore[assignment]
        session_date: date = (
            model_date.date() if isinstance(model_date, datetime) else model_date  # type: ignore[assignment]
        )

        # Training Type Info
        training_type = None
        auto_type = str(model.training_type_auto) if model.training_type_auto else None
        override_type = str(model.training_type_override) if model.training_type_override else None
        if auto_type or override_type:
            training_type = TrainingTypeInfo(
                auto=auto_type,
                confidence=(
                    int(model.training_type_confidence)  # type: ignore[arg-type]
                    if model.training_type_confidence
                    else None
                ),
                override=override_type,
                effective=override_type or auto_type,
            )

        # Strength metrics
        exercises_count = None
        total_tonnage_kg = None
        if model.exercises_json:
            from app.services.tonnage_calculator import calculate_strength_metrics

            exercises_raw = json.loads(str(model.exercises_json))
            m = calculate_strength_metrics(exercises_raw)
            exercises_count = m["total_exercises"]
            total_tonnage_kg = m["total_tonnage_kg"]

        return cls(
            id=int(model.id),  # type: ignore[arg-type]
            date=session_date,
            workout_type=str(model.workout_type),
            subtype=model.subtype if model.subtype is None else str(model.subtype),
            training_type=training_type,
            duration_sec=int(model.duration_sec) if model.duration_sec else None,  # type: ignore[arg-type]
            distance_km=float(model.distance_km) if model.distance_km else None,  # type: ignore[arg-type]
            pace=str(model.pace) if model.pace else None,
            hr_avg=int(model.hr_avg) if model.hr_avg else None,  # type: ignore[arg-type]
            exercises_count=exercises_count,
            total_tonnage_kg=total_tonnage_kg,
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


class SessionParseResponse(BaseModel):
    """Antwort nach CSV-Parse (ohne Session-Erstellung)."""

    success: bool
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


class TrainingTypeOverrideRequest(BaseModel):
    """Request fuer Training Type Override."""

    training_type: str


class NotesUpdateRequest(BaseModel):
    """Request fuer Notizen-Update."""

    notes: Optional[str] = None


class DateUpdateRequest(BaseModel):
    """Request fuer Datums-Update."""

    date: date


class RpeUpdateRequest(BaseModel):
    """Request fuer RPE-Update."""

    rpe: Optional[int] = Field(None, ge=1, le=10)


class PlannedEntryUpdateRequest(BaseModel):
    """Request fuer planned_entry_id Update."""

    planned_entry_id: Optional[int] = None


class RecalculateZonesRequest(BaseModel):
    """Request fuer HF-Zonen Neuberechnung mit optionalen HR-Werten."""

    resting_hr: Optional[int] = None
    max_hr: Optional[int] = None
