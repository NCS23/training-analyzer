"""Pydantic schemas for Training Plans and Training Phases (S07, S08)."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class PhaseFocus(BaseModel):
    """Focus areas for a training phase."""

    primary: list[str] = Field(default_factory=list)
    secondary: Optional[list[str]] = None


class PhaseTargetMetrics(BaseModel):
    """Target metrics for a training phase."""

    weekly_volume_min: Optional[float] = None
    weekly_volume_max: Optional[float] = None
    quality_sessions_per_week: Optional[int] = None
    strength_sessions_per_week: Optional[int] = None


class PhaseWeeklyTemplateDayEntry(BaseModel):
    """A single day slot in a phase's weekly template."""

    day_of_week: int = Field(..., ge=0, le=6, description="0=Mon, 6=Sun")
    training_type: Optional[str] = Field(None, pattern="^(strength|running)$")
    is_rest_day: bool = False
    run_type: Optional[str] = Field(
        None, pattern="^(recovery|easy|long_run|tempo|intervals)$"
    )
    template_id: Optional[int] = None
    notes: Optional[str] = Field(None, max_length=200)


class PhaseWeeklyTemplate(BaseModel):
    """7-day weekly template for a training phase."""

    days: list[PhaseWeeklyTemplateDayEntry] = Field(..., min_length=7, max_length=7)


class TrainingPhaseCreate(BaseModel):
    """Request schema: create a training phase."""

    name: str = Field(..., min_length=1, max_length=200)
    phase_type: str = Field(..., pattern="^(base|build|peak|taper|transition)$")
    start_week: int = Field(..., ge=1, le=52)
    end_week: int = Field(..., ge=1, le=52)
    focus: Optional[PhaseFocus] = None
    target_metrics: Optional[PhaseTargetMetrics] = None
    weekly_template: Optional[PhaseWeeklyTemplate] = None
    notes: Optional[str] = Field(None, max_length=2000)


class TrainingPhaseUpdate(BaseModel):
    """Request schema: update a training phase."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    phase_type: Optional[str] = Field(
        None, pattern="^(base|build|peak|taper|transition)$"
    )
    start_week: Optional[int] = Field(None, ge=1, le=52)
    end_week: Optional[int] = Field(None, ge=1, le=52)
    focus: Optional[PhaseFocus] = None
    target_metrics: Optional[PhaseTargetMetrics] = None
    weekly_template: Optional[PhaseWeeklyTemplate] = None
    notes: Optional[str] = Field(None, max_length=2000)


class TrainingPhaseResponse(BaseModel):
    """Response schema: training phase."""

    id: int
    training_plan_id: int
    name: str
    phase_type: str
    start_week: int
    end_week: int
    focus: Optional[PhaseFocus] = None
    target_metrics: Optional[PhaseTargetMetrics] = None
    weekly_template: Optional[PhaseWeeklyTemplate] = None
    notes: Optional[str] = None
    created_at: str


class GoalCreate(BaseModel):
    """Embedded goal for auto-creation with a training plan."""

    title: str = Field(..., min_length=1, max_length=200)
    race_date: Optional[date] = None  # defaults to plan's target_event_date or end_date
    distance_km: float = Field(..., gt=0)
    target_time_seconds: int = Field(..., gt=0)


class GoalSummary(BaseModel):
    """Embedded goal summary in plan response."""

    id: int
    title: str


class WeeklyStructure(BaseModel):
    """Weekly structure template for a training plan."""

    rest_days: list[int] = Field(default_factory=list)  # 0=Mon, 6=Sun


class TrainingPlanCreate(BaseModel):
    """Request schema: create a training plan."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    goal_id: Optional[int] = None
    start_date: date
    end_date: date
    target_event_date: Optional[date] = None
    weekly_structure: Optional[WeeklyStructure] = None
    status: Optional[str] = Field("draft", pattern="^(draft|active|completed|paused)$")
    phases: Optional[list[TrainingPhaseCreate]] = None
    goal: Optional[GoalCreate] = None


class TrainingPlanUpdate(BaseModel):
    """Request schema: update a training plan."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    goal_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    target_event_date: Optional[date] = None
    weekly_structure: Optional[WeeklyStructure] = None
    status: Optional[str] = Field(
        None, pattern="^(draft|active|completed|paused)$"
    )


class TrainingPlanResponse(BaseModel):
    """Response schema: training plan with phases."""

    id: int
    name: str
    description: Optional[str] = None
    goal_id: Optional[int] = None
    start_date: str
    end_date: str
    target_event_date: Optional[str] = None
    weekly_structure: Optional[WeeklyStructure] = None
    status: str
    phases: list[TrainingPhaseResponse] = Field(default_factory=list)
    goal_summary: Optional[GoalSummary] = None
    created_at: str
    updated_at: str


class TrainingPlanSummary(BaseModel):
    """Summary schema for list views."""

    id: int
    name: str
    status: str
    start_date: str
    end_date: str
    phase_count: int = 0
    goal_title: Optional[str] = None
    created_at: str
    updated_at: str


class TrainingPlanListResponse(BaseModel):
    """Response schema: list of training plans."""

    plans: list[TrainingPlanSummary]
    total: int


class GenerateWeeklyPlansResponse(BaseModel):
    """Response schema: weekly plan generation result."""

    weeks_generated: int
    total_weeks: int
