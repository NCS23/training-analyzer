"""Pydantic schemas for Session Templates (renamed from Training Plans)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.weekly_plan import RunDetails


class TemplateExercise(BaseModel):
    """A planned exercise within a session template."""

    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., pattern="^(push|pull|legs|core|cardio)$")
    sets: int = Field(..., ge=1, le=20)
    reps: int = Field(..., ge=1, le=100)
    weight_kg: Optional[float] = Field(None, ge=0, le=999)
    exercise_type: str = Field("kraft", pattern="^(kraft|mobilitaet|dehnung)$")
    notes: Optional[str] = Field(None, max_length=500)


class SessionTemplateCreate(BaseModel):
    """Create a new session template."""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    session_type: str = Field("strength", pattern="^(strength|running)$")
    exercises: Optional[list[TemplateExercise]] = None
    run_details: Optional[RunDetails] = None


class SessionTemplateUpdate(BaseModel):
    """Update an existing session template."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    exercises: Optional[list[TemplateExercise]] = Field(None, min_length=1)
    run_details: Optional[RunDetails] = None


class SessionTemplateResponse(BaseModel):
    """Response for a single session template."""

    id: int
    name: str
    description: Optional[str]
    session_type: str
    exercises: list[TemplateExercise]
    run_details: Optional[RunDetails] = None
    is_template: bool
    created_at: datetime
    updated_at: datetime


class SessionTemplateSummary(BaseModel):
    """Lightweight summary for list view."""

    id: int
    name: str
    session_type: str
    exercise_count: int
    total_sets: int
    run_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class SessionTemplateListResponse(BaseModel):
    """Response for listing session templates."""

    templates: list[SessionTemplateSummary]
    total: int
