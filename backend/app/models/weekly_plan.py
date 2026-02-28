"""Pydantic schemas for Weekly Plan (Issue #26, #27)."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class RunInterval(BaseModel):
    """A single interval in a structured run workout."""

    type: str = Field(..., pattern="^(work|rest|warmup|cooldown)$")
    duration_minutes: float = Field(..., gt=0, le=180)
    target_pace_min: Optional[str] = Field(None, max_length=10)  # e.g. "5:30"
    target_pace_max: Optional[str] = Field(None, max_length=10)  # e.g. "6:00"
    target_hr_min: Optional[int] = Field(None, ge=60, le=220)
    target_hr_max: Optional[int] = Field(None, ge=60, le=220)
    repeats: int = Field(1, ge=1, le=50)


class RunDetails(BaseModel):
    """Planned running session details."""

    run_type: str = Field(
        ...,
        pattern="^(recovery|easy|long_run|tempo|intervals)$",
    )
    target_duration_minutes: Optional[int] = Field(None, ge=5, le=360)
    target_pace_min: Optional[str] = Field(None, max_length=10)
    target_pace_max: Optional[str] = Field(None, max_length=10)
    target_hr_min: Optional[int] = Field(None, ge=60, le=220)
    target_hr_max: Optional[int] = Field(None, ge=60, le=220)
    intervals: Optional[list[RunInterval]] = None


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
    run_details: Optional[RunDetails] = None


class WeeklyPlanResponse(BaseModel):
    """Full week plan response."""

    week_start: date
    entries: list[WeeklyPlanEntry]


class WeeklyPlanSaveRequest(BaseModel):
    """Save/update a full week plan."""

    week_start: date
    entries: list[WeeklyPlanEntry] = Field(..., min_length=1, max_length=7)
