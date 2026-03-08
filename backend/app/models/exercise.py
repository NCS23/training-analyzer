"""Pydantic schemas for exercises — shared between session_template and weekly_plan."""

from typing import Optional

from pydantic import BaseModel, Field


class TemplateExercise(BaseModel):
    """A planned exercise within a session template."""

    name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., pattern="^(push|pull|legs|core|cardio)$")
    sets: int = Field(..., ge=1, le=20)
    reps: int = Field(..., ge=1, le=100)
    weight_kg: Optional[float] = Field(None, ge=0, le=999)
    exercise_type: str = Field("kraft", pattern="^(kraft|mobilitaet|dehnung)$")
    notes: Optional[str] = Field(None, max_length=500)
