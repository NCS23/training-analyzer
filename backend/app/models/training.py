"""Pydantic Models für Training API"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import date, datetime
from enum import Enum

class TrainingType(str, Enum):
    """Trainingstyp"""
    RUNNING = "running"
    STRENGTH = "strength"

class TrainingSubType(str, Enum):
    """Unter-Typ für spezifischere Klassifizierung"""
    # Running
    INTERVAL = "interval"
    TEMPO = "tempo"
    LONGRUN = "longrun"
    RECOVERY = "recovery"
    
    # Strength
    KNEE_DOMINANT = "knee_dominant"  # Studio Tag 1
    HIP_DOMINANT = "hip_dominant"    # Studio Tag 2

class TrainingUploadRequest(BaseModel):
    """Request für Training Upload"""
    training_date: date = Field(..., description="Datum des Trainings")
    training_type: TrainingType = Field(..., description="Trainingstyp (running/strength)")
    training_subtype: Optional[TrainingSubType] = Field(None, description="Spezifischer Trainingstyp")
    notes: Optional[str] = Field(None, description="Notizen zum Training")

class LapData(BaseModel):
    """Daten für einen einzelnen Lap (Laufen)"""
    lap_number: int
    duration_seconds: int
    duration_formatted: str
    distance_km: float
    pace_min_per_km: Optional[float]
    avg_hr_bpm: Optional[int]
    max_hr_bpm: Optional[int]
    min_hr_bpm: Optional[int]
    avg_cadence_spm: Optional[int]

class RunningSummary(BaseModel):
    """Zusammenfassung Lauftraining"""
    total_distance_km: float
    total_duration_seconds: int
    total_duration_formatted: str
    avg_pace_min_per_km: Optional[float]
    avg_hr_bpm: Optional[int]
    max_hr_bpm: Optional[int]
    min_hr_bpm: Optional[int]
    avg_cadence_spm: Optional[int]

class StrengthSummary(BaseModel):
    """Zusammenfassung Krafttraining"""
    total_duration_seconds: int
    total_duration_formatted: str
    avg_hr_bpm: Optional[int]
    max_hr_bpm: Optional[int]
    min_hr_bpm: Optional[int]

class HRZone(BaseModel):
    """HF-Zone Daten"""
    seconds: int
    percentage: float
    label: str

class HRZones(BaseModel):
    """HF-Zonen Verteilung"""
    zone_1_recovery: HRZone
    zone_2_base: HRZone
    zone_3_tempo: HRZone

class HRTimeseriesPoint(BaseModel):
    """Einzelner HF-Datenpunkt"""
    seconds: int
    hr_bpm: int
    timestamp: str

class TrainingUploadResponse(BaseModel):
    """Response für Training Upload"""
    success: bool
    training_id: Optional[int] = None
    data: Optional[Dict] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict] = None
