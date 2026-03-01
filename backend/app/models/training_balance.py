"""Pydantic schemas for Training Balance Analysis (Issue #48)."""

from typing import Optional

from pydantic import BaseModel, Field


class IntensityDistribution(BaseModel):
    """Running intensity distribution (polarized training check)."""

    easy_percent: float = Field(0, ge=0, le=100)
    moderate_percent: float = Field(0, ge=0, le=100)
    hard_percent: float = Field(0, ge=0, le=100)
    easy_sessions: int = 0
    moderate_sessions: int = 0
    hard_sessions: int = 0
    total_sessions: int = 0
    is_polarized: bool = False  # True if 80/20 split


class VolumeWeek(BaseModel):
    """Weekly volume data for progression tracking."""

    week: str  # e.g. "2026-W09"
    week_start: str
    running_km: float = 0
    running_min: int = 0
    strength_sessions: int = 0
    total_sessions: int = 0
    volume_change_percent: Optional[float] = None  # vs. previous week


class MuscleGroupBalance(BaseModel):
    """Muscle group distribution from strength training."""

    group: str
    session_count: int = 0
    total_sets: int = 0
    percentage: float = 0


class SportMix(BaseModel):
    """Distribution across sport types."""

    running_sessions: int = 0
    strength_sessions: int = 0
    running_percent: float = 0
    strength_percent: float = 0
    total_sessions: int = 0


class BalanceInsight(BaseModel):
    """A single balance insight/warning."""

    type: str = Field(..., pattern="^(positive|warning|neutral)$")
    category: str  # 'intensity', 'volume', 'muscle', 'sport_mix'
    message: str


class TrainingBalanceResponse(BaseModel):
    """Full training balance analysis response."""

    period_days: int
    intensity: IntensityDistribution
    volume_weeks: list[VolumeWeek]
    muscle_groups: list[MuscleGroupBalance]
    sport_mix: SportMix
    insights: list[BalanceInsight]
