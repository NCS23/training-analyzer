"""Pydantic schemas for YAML training plan validation results."""

from typing import Literal

from pydantic import BaseModel, Field


class YamlValidationIssue(BaseModel):
    """A single validation error or warning."""

    code: str
    level: Literal["error", "warning"]
    message: str
    location: str | None = None


class ExerciseCheck(BaseModel):
    """An exercise_name from the YAML that does not exist in the Exercise Library."""

    exercise_name: str
    locations: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class YamlValidationResult(BaseModel):
    """Result of YAML training plan validation."""

    valid: bool
    errors: list[YamlValidationIssue]
    warnings: list[YamlValidationIssue]
    unknown_exercises: list[ExerciseCheck] = Field(default_factory=list)
