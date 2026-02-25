"""Pydantic Schemas fuer Athlete Settings API."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.infrastructure.database.models import AthleteModel


class AthleteSettingsRequest(BaseModel):
    """Request fuer Athlete HR Settings."""

    resting_hr: Optional[int] = Field(None, ge=30, le=120, description="Ruheherzfrequenz")
    max_hr: Optional[int] = Field(None, ge=120, le=230, description="Maximale Herzfrequenz")


class AthleteSettingsResponse(BaseModel):
    """Response fuer Athlete HR Settings."""

    id: int
    resting_hr: Optional[int] = None
    max_hr: Optional[int] = None
    karvonen_zones: Optional[list[dict]] = None

    @classmethod
    def from_db(cls, model: AthleteModel, zones: Optional[list[dict]] = None) -> AthleteSettingsResponse:
        return cls(
            id=int(model.id),  # type: ignore[arg-type]
            resting_hr=int(model.resting_hr) if model.resting_hr else None,  # type: ignore[arg-type]
            max_hr=int(model.max_hr) if model.max_hr else None,  # type: ignore[arg-type]
            karvonen_zones=zones,
        )
