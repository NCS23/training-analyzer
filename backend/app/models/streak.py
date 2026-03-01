"""Pydantic schemas for Streak Tracking (Issue #58)."""

from typing import Optional

from pydantic import BaseModel


class StreakResponse(BaseModel):
    """Training streak statistics."""

    current_streak: int  # Current consecutive training days
    longest_streak: int  # All-time longest streak
    last_training_date: Optional[str] = None  # YYYY-MM-DD
    streak_at_risk: bool = False  # True if no training today and streak > 0
    # Calendar heatmap data: last 90 days, { "YYYY-MM-DD": session_count }
    calendar: dict[str, int]
