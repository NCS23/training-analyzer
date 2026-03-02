"""Pydantic schemas for Plan Change Log (Audit Trail)."""

from pydantic import BaseModel, Field


class PlanChangeLogEntry(BaseModel):
    id: int
    plan_id: int
    change_type: str
    summary: str
    details: dict[str, object] | None = None
    reason: str | None = None
    created_by: str | None = None
    created_at: str


class PlanChangeLogResponse(BaseModel):
    entries: list[PlanChangeLogEntry]
    total: int


class PlanChangeLogReasonUpdate(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)
