"""Pydantic schemas for Training Plans (Issue #14)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PlanExercise(BaseModel):
    """A planned exercise within a training plan."""

    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., pattern="^(push|pull|legs|core|cardio)$")
    sets: int = Field(..., ge=1, le=20)
    reps: int = Field(..., ge=1, le=100)
    weight_kg: Optional[float] = Field(None, ge=0, le=999)
    exercise_type: str = Field(
        "kraft", pattern="^(kraft|mobilitaet|dehnung)$"
    )
    notes: Optional[str] = Field(None, max_length=500)


class TrainingPlanCreate(BaseModel):
    """Create a new training plan."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    session_type: str = Field("strength", pattern="^(strength|running)$")
    exercises: list[PlanExercise] = Field(..., min_length=1)


class TrainingPlanUpdate(BaseModel):
    """Update an existing training plan."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    exercises: Optional[list[PlanExercise]] = Field(None, min_length=1)


class TrainingPlanResponse(BaseModel):
    """Response for a single training plan."""

    id: int
    name: str
    description: Optional[str]
    session_type: str
    exercises: list[PlanExercise]
    is_template: bool
    created_at: datetime
    updated_at: datetime


class TrainingPlanSummary(BaseModel):
    """Lightweight summary for list view."""

    id: int
    name: str
    session_type: str
    exercise_count: int
    total_sets: int
    created_at: datetime
    updated_at: datetime


class TrainingPlanListResponse(BaseModel):
    """Response for listing training plans."""

    plans: list[TrainingPlanSummary]
    total: int
