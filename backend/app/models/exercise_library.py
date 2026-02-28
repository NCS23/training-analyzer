"""Pydantic Schemas für Übungs-Bibliothek API."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.infrastructure.database.models import ExerciseModel


class ExerciseCreate(BaseModel):
    """Request zum Erstellen einer Übung."""

    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=20)


class ExerciseUpdate(BaseModel):
    """Request zum Aktualisieren einer Übung."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[str] = Field(None, min_length=1, max_length=20)
    is_favorite: Optional[bool] = None
    instructions: Optional[list[str]] = None
    primary_muscles: Optional[list[str]] = None
    secondary_muscles: Optional[list[str]] = None


class ExerciseResponse(BaseModel):
    """Einzelne Übung in der API-Antwort."""

    id: int
    name: str
    category: str
    is_favorite: bool
    is_custom: bool
    usage_count: int
    last_used_at: Optional[datetime] = None

    # Enrichment fields
    instructions: Optional[list[str]] = None
    primary_muscles: Optional[list[str]] = None
    secondary_muscles: Optional[list[str]] = None
    image_urls: Optional[list[str]] = None
    equipment: Optional[str] = None
    level: Optional[str] = None
    force: Optional[str] = None
    mechanic: Optional[str] = None
    exercise_db_id: Optional[str] = None

    @classmethod
    def from_db(cls, model: ExerciseModel) -> ExerciseResponse:
        return cls(
            id=int(model.id),  # type: ignore[arg-type]
            name=str(model.name),
            category=str(model.category),
            is_favorite=bool(model.is_favorite),
            is_custom=bool(model.is_custom),
            usage_count=int(model.usage_count),  # type: ignore[arg-type]
            last_used_at=model.last_used_at,  # type: ignore[arg-type]
            instructions=_parse_json_list(model.instructions_json),  # type: ignore[arg-type]
            primary_muscles=_parse_json_list(model.primary_muscles_json),  # type: ignore[arg-type]
            secondary_muscles=_parse_json_list(model.secondary_muscles_json),  # type: ignore[arg-type]
            image_urls=_parse_json_list(model.image_urls_json),  # type: ignore[arg-type]
            equipment=model.equipment,  # type: ignore[arg-type]
            level=model.level,  # type: ignore[arg-type]
            force=model.force,  # type: ignore[arg-type]
            mechanic=model.mechanic,  # type: ignore[arg-type]
            exercise_db_id=model.exercise_db_id,  # type: ignore[arg-type]
        )


class ExerciseListResponse(BaseModel):
    """Liste aller Übungen."""

    exercises: list[ExerciseResponse]
    total: int


class EnrichRequest(BaseModel):
    """Optionaler Request-Body für Anreicherung mit spezifischer exercise-db ID."""

    exercise_db_id: Optional[str] = None


class ExerciseDbEntry(BaseModel):
    """Kompakter Eintrag aus der free-exercise-db fürs Browsen."""

    id: str
    name: str
    name_de: Optional[str] = None
    category: Optional[str] = None
    equipment: Optional[str] = None
    primary_muscles: list[str] = []
    level: Optional[str] = None
    force: Optional[str] = None


class ExerciseDbSearchResponse(BaseModel):
    """Paginierte Suchergebnisse aus der free-exercise-db."""

    exercises: list[ExerciseDbEntry]
    total: int


def _parse_json_list(raw: Optional[str]) -> Optional[list[str]]:
    """Parse a JSON string into a list of strings, or None."""
    if not raw:
        return None
    try:
        result = json.loads(raw)
        if isinstance(result, list):
            return result
    except (json.JSONDecodeError, TypeError):
        pass
    return None
