"""Pydantic schemas for Weekly Plan (Issue #26, #27)."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.models.taxonomy import SEGMENT_TYPE_REGEX, SESSION_TYPE_REGEX


class RunInterval(BaseModel):
    """A single interval in a structured run workout."""

    type: str = Field(..., pattern=SEGMENT_TYPE_REGEX)
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
        pattern=SESSION_TYPE_REGEX,
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
    training_type: Optional[str] = Field(None, pattern="^(strength|running)$")
    template_id: Optional[int] = None
    template_name: Optional[str] = None  # returned in response only
    is_rest_day: bool = False
    notes: Optional[str] = Field(None, max_length=500)
    run_details: Optional[RunDetails] = None
    plan_id: Optional[int] = None  # returned in response only
    edited: bool = False  # returned in response only


class WeeklyPlanResponse(BaseModel):
    """Full week plan response."""

    week_start: date
    entries: list[WeeklyPlanEntry]


class WeeklyPlanSaveRequest(BaseModel):
    """Save/update a full week plan."""

    week_start: date
    entries: list[WeeklyPlanEntry] = Field(..., min_length=1, max_length=7)


class ActualSession(BaseModel):
    """Matched actual session for compliance tracking."""

    session_id: int
    workout_type: str
    training_type_effective: Optional[str] = None
    duration_sec: Optional[int] = None
    distance_km: Optional[float] = None
    pace: Optional[str] = None
    planned_entry_id: Optional[int] = None  # S10: Soll/Ist-Link


class ComplianceDayEntry(BaseModel):
    """Compliance status for a single day."""

    day_of_week: int = Field(..., ge=0, le=6)
    date: date
    planned_type: Optional[str] = None  # 'strength', 'running', or None
    planned_run_type: Optional[str] = None  # run_details.run_type
    is_rest_day: bool = False
    status: str = Field(
        ...,
        pattern="^(completed|off_target|missed|rest_ok|unplanned|empty)$",
    )
    actual_sessions: list[ActualSession] = Field(default_factory=list)


class ComplianceResponse(BaseModel):
    """Weekly compliance tracking response."""

    week_start: date
    entries: list[ComplianceDayEntry]
    completed_count: int
    planned_count: int
