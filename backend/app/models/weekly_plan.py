"""Pydantic schemas for Weekly Plan (Issue #26, #27, E17-S02)."""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.segment import Segment, intervals_to_segments, segments_to_intervals
from app.models.taxonomy import SEGMENT_TYPE_REGEX, SESSION_TYPE_REGEX


class RunInterval(BaseModel):
    """A single interval in a structured run workout."""

    type: str = Field(..., pattern=SEGMENT_TYPE_REGEX)
    duration_minutes: float = Field(..., gt=0, le=180)
    target_pace_min: Optional[str] = Field(default=None, max_length=10)  # e.g. "5:30"
    target_pace_max: Optional[str] = Field(default=None, max_length=10)  # e.g. "6:00"
    target_hr_min: Optional[int] = Field(default=None, ge=60, le=220)
    target_hr_max: Optional[int] = Field(default=None, ge=60, le=220)
    repeats: int = Field(default=1, ge=1, le=50)


class RunDetails(BaseModel):
    """Planned running session details."""

    run_type: str = Field(
        ...,
        pattern=SESSION_TYPE_REGEX,
    )
    target_duration_minutes: Optional[int] = Field(default=None, ge=5, le=360)
    target_pace_min: Optional[str] = Field(default=None, max_length=10)
    target_pace_max: Optional[str] = Field(default=None, max_length=10)
    target_hr_min: Optional[int] = Field(default=None, ge=60, le=220)
    target_hr_max: Optional[int] = Field(default=None, ge=60, le=220)
    intervals: Optional[list[RunInterval]] = None
    segments: Optional[list[Segment]] = None  # Unified segment model (#133)

    @model_validator(mode="after")
    def _populate_segments(self) -> RunDetails:
        """Auto-populate segments from intervals if not explicitly set."""
        if self.segments is None and self.intervals:
            self.segments = intervals_to_segments(self.intervals)
        return self

    @model_validator(mode="after")
    def _populate_intervals(self) -> RunDetails:
        """Auto-derive intervals from segments when only segments provided."""
        if self.intervals is None and self.segments:
            self.intervals = segments_to_intervals(self.segments)
        return self


class PlannedSession(BaseModel):
    """A single planned session within a day (E17)."""

    id: Optional[int] = None  # response only (DB id)
    position: int = 0
    training_type: str = Field(..., pattern="^(strength|running)$")
    template_id: Optional[int] = None
    template_name: Optional[str] = None  # response only
    notes: Optional[str] = Field(default=None, max_length=500)
    run_details: Optional[RunDetails] = None


class WeeklyPlanEntry(BaseModel):
    """A single day entry in the weekly plan (E17: with sessions[])."""

    day_of_week: int = Field(..., ge=0, le=6, description="0=Mon, 6=Sun")
    is_rest_day: bool = False
    notes: Optional[str] = Field(default=None, max_length=500)
    sessions: list[PlannedSession] = Field(default_factory=list)
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
    planned_entry_id: Optional[int] = None  # S10: FK to planned_sessions


class ComplianceDayEntry(BaseModel):
    """Compliance status for a single day."""

    day_of_week: int = Field(..., ge=0, le=6)
    date: date
    planned_types: list[str] = Field(default_factory=list)
    planned_run_type: Optional[str] = None  # first running session's run_type
    is_rest_day: bool = False
    status: str = Field(
        ...,
        pattern="^(completed|partial|off_target|missed|rest_ok|unplanned|empty)$",
    )
    actual_sessions: list[ActualSession] = Field(default_factory=list)


class ComplianceResponse(BaseModel):
    """Weekly compliance tracking response."""

    week_start: date
    entries: list[ComplianceDayEntry]
    completed_count: int
    planned_count: int


class SyncToPlanRequest(BaseModel):
    """Request: sync weekly plan entries back to training plan phase template."""

    week_start: date
    plan_id: int = Field(..., gt=0)
    apply_to_all_weeks: bool = False


class SyncToPlanResponse(BaseModel):
    """Response: result of syncing weekly plan back to training plan."""

    phase_id: int
    phase_name: str
    week_key: str
    apply_to_all_weeks: bool
    synced_days: int
