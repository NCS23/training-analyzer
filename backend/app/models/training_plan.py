"""Pydantic schemas for Training Plans and Training Phases (S07, S08, E17)."""

from datetime import date
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.models.taxonomy import SESSION_TYPE_REGEX
from app.models.weekly_plan import RunDetails


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


class PhaseWeeklyTemplateSessionEntry(BaseModel):
    """A single session within a phase template day (E17)."""

    position: int = 0
    training_type: str = Field(..., pattern="^(strength|running)$")
    run_type: Optional[str] = Field(default=None, pattern=SESSION_TYPE_REGEX)
    template_id: Optional[int] = None
    notes: Optional[str] = Field(default=None, max_length=200)
    run_details: Optional[RunDetails] = None


class PhaseWeeklyTemplateDayEntry(BaseModel):
    """A single day slot in a phase's weekly template (E17: multi-session)."""

    day_of_week: int = Field(..., ge=0, le=6, description="0=Mon, 6=Sun")
    sessions: list[PhaseWeeklyTemplateSessionEntry] = Field(default_factory=list)
    is_rest_day: bool = False
    notes: Optional[str] = Field(default=None, max_length=200)

    # Legacy flat fields (backwards-compat for old JSON, excluded from serialization)
    training_type: Optional[str] = Field(default=None, pattern="^(strength|running)$", exclude=True)
    run_type: Optional[str] = Field(default=None, pattern=SESSION_TYPE_REGEX, exclude=True)
    template_id: Optional[int] = Field(default=None, exclude=True)
    run_details: Optional[RunDetails] = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def _migrate_flat_to_sessions(self) -> "PhaseWeeklyTemplateDayEntry":
        """Auto-convert old flat format to sessions[]."""
        if not self.sessions and self.training_type:
            self.sessions = [
                PhaseWeeklyTemplateSessionEntry(
                    position=0,
                    training_type=self.training_type,
                    run_type=self.run_type,
                    template_id=self.template_id,
                    run_details=self.run_details,
                )
            ]
        return self


class PhaseWeeklyTemplate(BaseModel):
    """7-day weekly template for a training phase."""

    days: list[PhaseWeeklyTemplateDayEntry] = Field(..., min_length=7, max_length=7)


class PhaseWeeklyTemplates(BaseModel):
    """Per-week templates: week_number (1-indexed within phase) to template."""

    weeks: dict[str, PhaseWeeklyTemplate] = Field(default_factory=dict)


class TrainingPhaseCreate(BaseModel):
    """Request schema: create a training phase."""

    name: str = Field(..., min_length=1, max_length=200)
    phase_type: str = Field(..., pattern="^(base|build|peak|taper|transition)$")
    start_week: int = Field(..., ge=1, le=52)
    end_week: int = Field(..., ge=1, le=52)
    focus: Optional[PhaseFocus] = None
    target_metrics: Optional[PhaseTargetMetrics] = None
    weekly_template: Optional[PhaseWeeklyTemplate] = None
    weekly_templates: Optional[PhaseWeeklyTemplates] = None
    notes: Optional[str] = Field(None, max_length=2000)


class TrainingPhaseUpdate(BaseModel):
    """Request schema: update a training phase."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    phase_type: Optional[str] = Field(None, pattern="^(base|build|peak|taper|transition)$")
    start_week: Optional[int] = Field(None, ge=1, le=52)
    end_week: Optional[int] = Field(None, ge=1, le=52)
    focus: Optional[PhaseFocus] = None
    target_metrics: Optional[PhaseTargetMetrics] = None
    weekly_template: Optional[PhaseWeeklyTemplate] = None
    weekly_templates: Optional[PhaseWeeklyTemplates] = None
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
    weekly_templates: Optional[PhaseWeeklyTemplates] = None
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
    status: Optional[str] = Field(None, pattern="^(draft|active|completed|paused)$")


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


class GenerationPreviewResponse(BaseModel):
    """Response schema: preview of what generation would affect."""

    total_generated_weeks: int
    edited_week_count: int
    edited_week_starts: list[str]
    unedited_week_count: int
