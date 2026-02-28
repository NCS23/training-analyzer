"""Pydantic schemas for Weekly Plan (Issue #26)."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class WeeklyPlanEntry(BaseModel):
    """A single day entry in the weekly plan."""

    day_of_week: int = Field(..., ge=0, le=6, description="0=Mon, 6=Sun")
    training_type: Optional[str] = Field(
        None, pattern="^(strength|running)$"
    )
    plan_id: Optional[int] = None
    plan_name: Optional[str] = None  # returned in response only
    is_rest_day: bool = False
    notes: Optional[str] = Field(None, max_length=500)


class WeeklyPlanResponse(BaseModel):
    """Full week plan response."""

    week_start: date
    entries: list[WeeklyPlanEntry]


class WeeklyPlanSaveRequest(BaseModel):
    """Save/update a full week plan."""

    week_start: date
    entries: list[WeeklyPlanEntry] = Field(..., min_length=1, max_length=7)
