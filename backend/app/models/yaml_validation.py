"""Pydantic schemas for YAML training plan validation results."""

from typing import Literal

from pydantic import BaseModel


class YamlValidationIssue(BaseModel):
    """A single validation error or warning."""

    code: str
    level: Literal["error", "warning"]
    message: str
    location: str | None = None


class YamlValidationResult(BaseModel):
    """Result of YAML training plan validation."""

    valid: bool
    errors: list[YamlValidationIssue]
    warnings: list[YamlValidationIssue]
