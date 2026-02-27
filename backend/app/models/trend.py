"""Pydantic Schemas fuer Trend-Analyse API."""

from typing import Optional

from pydantic import BaseModel


class WeeklyDataPoint(BaseModel):
    """Aggregierte Daten fuer eine Kalenderwoche."""

    week: str
    week_start: str
    session_count: int
    total_distance_km: float
    total_duration_sec: int
    avg_pace_sec_per_km: Optional[float] = None
    avg_pace_formatted: Optional[str] = None
    avg_hr_bpm: Optional[int] = None


class TrendInsight(BaseModel):
    """Insight aus der Trend-Analyse."""

    type: str
    message: str


class TrendResponse(BaseModel):
    """Response-Schema: Trend-Analyse."""

    weeks: list[WeeklyDataPoint]
    insights: list[TrendInsight]
