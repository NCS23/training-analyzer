"""Response models for category tonnage trend analysis (#151)."""

from pydantic import BaseModel, Field

from app.models.weekly_plan import CategoryTonnage


class WeeklyCategoryTonnage(BaseModel):
    """Per-week category tonnage breakdown."""

    week: str
    week_start: str
    categories: list[CategoryTonnage] = Field(default_factory=list)
    total_tonnage_kg: float


class CategoryTonnageTrendResponse(BaseModel):
    """Multi-week category tonnage trend response."""

    weeks: list[WeeklyCategoryTonnage]
    aggregated: list[CategoryTonnage]
    total_tonnage_kg: float
    period_days: int
