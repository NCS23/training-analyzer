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
    elevation_gain_factor: Optional[float] = Field(
        None, ge=0, le=30, description="Höhenkorrektur-Faktor Anstieg (sec/km pro 100m)"
    )
    elevation_loss_factor: Optional[float] = Field(
        None, ge=0, le=20, description="Höhenkorrektur-Faktor Abstieg (sec/km pro 100m)"
    )


class AthleteSettingsResponse(BaseModel):
    """Response fuer Athlete HR Settings."""

    id: int
    resting_hr: Optional[int] = None
    max_hr: Optional[int] = None
    elevation_gain_factor: float = 10.0
    elevation_loss_factor: float = 5.0
    karvonen_zones: Optional[list[dict]] = None

    @classmethod
    def from_db(
        cls, model: AthleteModel, zones: Optional[list[dict]] = None
    ) -> AthleteSettingsResponse:
        return cls(
            id=model.id,
            resting_hr=model.resting_hr if model.resting_hr else None,
            max_hr=model.max_hr if model.max_hr else None,
            elevation_gain_factor=float(model.elevation_gain_factor)
            if model.elevation_gain_factor
            else 10.0,
            elevation_loss_factor=float(model.elevation_loss_factor)
            if model.elevation_loss_factor
            else 5.0,
            karvonen_zones=zones,
        )
