"""Pydantic schemas for Seasonal Analysis (Issue #49)."""

from typing import Optional

from pydantic import BaseModel


class SeasonStats(BaseModel):
    """Stats for a single season."""

    season: str  # 'Fruehling', 'Sommer', 'Herbst', 'Winter'
    total_sessions: int = 0
    running_sessions: int = 0
    strength_sessions: int = 0
    total_distance_km: float = 0.0
    total_duration_sec: int = 0
    avg_pace: Optional[str] = None  # min:sec format
    avg_hr: Optional[int] = None


class SeasonalInsight(BaseModel):
    """A generated insight from seasonal analysis."""

    type: str  # 'positive', 'warning', 'neutral'
    message: str


class SeasonalAnalysisResponse(BaseModel):
    """Full seasonal analysis response."""

    seasons: list[SeasonStats]
    insights: list[SeasonalInsight]
    years_analyzed: int
    total_sessions: int
