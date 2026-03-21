"""Pydantic Schemas für Laktatschwellen-Tests."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.infrastructure.database.models import ThresholdTestModel


class ThresholdTestCreate(BaseModel):
    """Request zum Anlegen eines Schwellentests."""

    test_date: date = Field(..., description="Datum des Tests")
    lthr: int = Field(..., ge=100, le=220, description="Laktatschwellen-HF (bpm)")
    max_hr_measured: Optional[int] = Field(
        None, ge=120, le=230, description="Gemessene Max-HF (bpm)"
    )
    avg_pace_sec: Optional[float] = Field(None, ge=120, le=900, description="Ø Pace in sec/km")
    session_id: Optional[int] = Field(None, description="Referenz zur importierten Session")
    notes: Optional[str] = Field(None, max_length=500, description="Notizen zum Test")


class ThresholdTestResponse(BaseModel):
    """Response für einen einzelnen Schwellentest."""

    id: int
    test_date: date
    lthr: int
    max_hr_measured: Optional[int] = None
    avg_pace_sec: Optional[float] = None
    session_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime
    friel_zones: Optional[list[dict]] = None

    @classmethod
    def from_db(
        cls,
        model: ThresholdTestModel,
        friel_zones: Optional[list[dict]] = None,
    ) -> ThresholdTestResponse:
        return cls(
            id=model.id,
            test_date=model.test_date,
            lthr=model.lthr,
            max_hr_measured=model.max_hr_measured,
            avg_pace_sec=model.avg_pace_sec,
            session_id=model.session_id,
            notes=model.notes,
            created_at=model.created_at,
            friel_zones=friel_zones,
        )


class ThresholdTestListResponse(BaseModel):
    """Response für die Testhistorie."""

    tests: list[ThresholdTestResponse]
    total: int
