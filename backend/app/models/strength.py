"""Pydantic Schemas für Krafttraining API."""

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class ExerciseCategory(str, Enum):
    """Übungskategorie."""

    PUSH = "push"
    PULL = "pull"
    LEGS = "legs"
    CORE = "core"
    CARDIO = "cardio"
    DRILLS = "drills"


class SetStatus(str, Enum):
    """Status eines Satzes."""

    COMPLETED = "completed"
    REDUCED = "reduced"
    SKIPPED = "skipped"


class SetType(str, Enum):
    """Typ eines Satzes — bestimmt welche Felder relevant sind."""

    WEIGHT_REPS = "weight_reps"
    BODYWEIGHT_REPS = "bodyweight_reps"
    WEIGHTED_BODYWEIGHT = "weighted_bodyweight"
    ASSISTED_BODYWEIGHT = "assisted_bodyweight"
    DURATION = "duration"
    WEIGHT_DURATION = "weight_duration"
    DISTANCE_DURATION = "distance_duration"
    WEIGHT_DISTANCE = "weight_distance"


# Felder die je Set-Typ erforderlich bzw. erlaubt sind
SET_TYPE_FIELDS: dict[SetType, dict[str, list[str]]] = {
    SetType.WEIGHT_REPS: {"required": ["reps", "weight_kg"], "optional": []},
    SetType.BODYWEIGHT_REPS: {"required": ["reps"], "optional": []},
    SetType.WEIGHTED_BODYWEIGHT: {"required": ["reps", "weight_kg"], "optional": []},
    SetType.ASSISTED_BODYWEIGHT: {"required": ["reps", "weight_kg"], "optional": []},
    SetType.DURATION: {"required": ["duration_sec"], "optional": []},
    SetType.WEIGHT_DURATION: {"required": ["weight_kg", "duration_sec"], "optional": []},
    SetType.DISTANCE_DURATION: {"required": ["distance_m"], "optional": ["duration_sec"]},
    SetType.WEIGHT_DISTANCE: {"required": ["weight_kg", "distance_m"], "optional": []},
}


# --- Request Models ---


class SetInput(BaseModel):
    """Einzelner Satz einer Übung."""

    type: SetType = SetType.WEIGHT_REPS
    reps: int | None = Field(default=None, ge=0, le=999)
    weight_kg: float | None = Field(default=None, ge=0, le=999)
    duration_sec: int | None = Field(default=None, ge=0, le=86400)
    distance_m: float | None = Field(default=None, ge=0, le=99999)
    status: SetStatus = SetStatus.COMPLETED

    @model_validator(mode="before")
    @classmethod
    def apply_backward_compat(cls, data: dict) -> dict:  # type: ignore[type-arg]
        """Backward Compatibility: Sets ohne type → weight_reps mit required-Feldern."""
        if isinstance(data, dict) and "type" not in data:
            data["type"] = SetType.WEIGHT_REPS.value
            # Alte Sets haben reps/weight_kg als required — Defaults setzen falls fehlend
            data.setdefault("reps", data.get("reps", 0))
            data.setdefault("weight_kg", data.get("weight_kg", 0))
        return data

    @model_validator(mode="after")
    def validate_fields_for_type(self) -> "SetInput":
        """Validiert dass die für den Set-Typ erforderlichen Felder vorhanden sind."""
        field_config = SET_TYPE_FIELDS[self.type]
        for field_name in field_config["required"]:
            value = getattr(self, field_name)
            if value is None:
                msg = f"Feld '{field_name}' ist erforderlich für Set-Typ '{self.type.value}'"
                raise ValueError(msg)
        return self


class ExerciseInput(BaseModel):
    """Einzelne Übung mit Sätzen."""

    name: str = Field(..., min_length=1, max_length=100, description="Name der Übung")
    category: ExerciseCategory = Field(..., description="Kategorie")
    sets: list[SetInput] = Field(..., min_length=1, description="Mindestens ein Satz")


class StrengthSessionCreate(BaseModel):
    """Request zum Erstellen einer Krafttraining-Session."""

    date: date
    duration_minutes: int = Field(..., ge=1, le=600, description="Dauer in Minuten")
    exercises: list[ExerciseInput] = Field(..., min_length=1, description="Mindestens eine Übung")
    notes: Optional[str] = Field(None, max_length=2000, description="Notizen")
    rpe: Optional[int] = Field(None, ge=1, le=10, description="RPE (Rate of Perceived Exertion)")


# --- Response Models ---


class SetResponse(BaseModel):
    """Satz in der API-Antwort."""

    type: str = "weight_reps"
    reps: Optional[int] = None
    weight_kg: Optional[float] = None
    duration_sec: Optional[int] = None
    distance_m: Optional[float] = None
    status: str


class ExerciseResponse(BaseModel):
    """Übung in der API-Antwort."""

    name: str
    category: str
    sets: list[SetResponse]


class StrengthMetrics(BaseModel):
    """Auto-berechnete Metriken für Krafttraining."""

    total_exercises: int
    total_sets: int
    total_tonnage_kg: float
    completed_sets: int
    rpe: Optional[int] = None


class LastExerciseSets(BaseModel):
    """Letzte Sätze einer Übung (Quick-Add)."""

    exercise_name: str
    category: str
    sets: list[SetResponse]
    session_date: date


class LastCompleteSessionResponse(BaseModel):
    """Letzte vollstaendige Strength-Session (fuer Clone)."""

    id: int
    date: date
    exercises: list[ExerciseResponse]
    total_tonnage_kg: float
    duration_minutes: Optional[int] = None
