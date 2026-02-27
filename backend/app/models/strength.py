"""Pydantic Schemas fuer Krafttraining API."""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ExerciseCategory(str, Enum):
    """Uebungskategorie."""

    PUSH = "push"
    PULL = "pull"
    LEGS = "legs"
    CORE = "core"
    CARDIO = "cardio"


class SetStatus(str, Enum):
    """Status eines Satzes."""

    COMPLETED = "completed"
    REDUCED = "reduced"
    SKIPPED = "skipped"


# --- Request Models ---


class SetInput(BaseModel):
    """Einzelner Satz einer Uebung."""

    reps: int = Field(..., ge=0, le=999, description="Anzahl Wiederholungen")
    weight_kg: float = Field(..., ge=0, le=999, description="Gewicht in kg")
    status: SetStatus = Field(default=SetStatus.COMPLETED, description="Status des Satzes")


class ExerciseInput(BaseModel):
    """Einzelne Uebung mit Saetzen."""

    name: str = Field(..., min_length=1, max_length=100, description="Name der Uebung")
    category: ExerciseCategory = Field(..., description="Kategorie")
    sets: list[SetInput] = Field(..., min_length=1, description="Mindestens ein Satz")


class StrengthSessionCreate(BaseModel):
    """Request zum Erstellen einer Krafttraining-Session."""

    date: date
    duration_minutes: int = Field(..., ge=1, le=600, description="Dauer in Minuten")
    exercises: list[ExerciseInput] = Field(..., min_length=1, description="Mindestens eine Uebung")
    notes: Optional[str] = Field(None, max_length=2000, description="Notizen")
    rpe: Optional[int] = Field(None, ge=1, le=10, description="RPE (Rate of Perceived Exertion)")


# --- Response Models ---


class SetResponse(BaseModel):
    """Satz in der API-Antwort."""

    reps: int
    weight_kg: float
    status: str


class ExerciseResponse(BaseModel):
    """Uebung in der API-Antwort."""

    name: str
    category: str
    sets: list[SetResponse]


class StrengthMetrics(BaseModel):
    """Auto-berechnete Metriken fuer Krafttraining."""

    total_exercises: int
    total_sets: int
    total_tonnage_kg: float
    completed_sets: int
    rpe: Optional[int] = None


class LastExerciseSets(BaseModel):
    """Letzte Saetze einer Uebung (Quick-Add)."""

    exercise_name: str
    category: str
    sets: list[SetResponse]
    session_date: date
