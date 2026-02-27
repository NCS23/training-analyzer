"""Pydantic Schemas fuer Race Goal API."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.infrastructure.database.models import RaceGoalModel


class RaceGoalCreate(BaseModel):
    """Request-Schema: neues Wettkampf-Ziel erstellen."""

    title: str = Field(..., min_length=1, max_length=200)
    race_date: date
    distance_km: float = Field(..., gt=0)
    target_time_seconds: int = Field(..., gt=0)


class RaceGoalUpdate(BaseModel):
    """Request-Schema: Wettkampf-Ziel aktualisieren."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    race_date: Optional[date] = None
    distance_km: Optional[float] = Field(None, gt=0)
    target_time_seconds: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class RaceGoalResponse(BaseModel):
    """Response-Schema: Wettkampf-Ziel."""

    id: int
    title: str
    race_date: str
    distance_km: float
    target_time_seconds: int
    target_time_formatted: str
    target_pace_formatted: str
    is_active: bool
    days_until: int
    created_at: str
    updated_at: str

    @staticmethod
    def from_db(goal: RaceGoalModel) -> RaceGoalResponse:
        """Build response from DB model."""
        target_secs = int(goal.target_time_seconds)  # type: ignore[arg-type]
        distance = float(goal.distance_km)  # type: ignore[arg-type]

        # Format target time
        hours = target_secs // 3600
        mins = (target_secs % 3600) // 60
        secs = target_secs % 60
        time_fmt = f"{hours}:{mins:02d}:{secs:02d}" if hours > 0 else f"{mins}:{secs:02d}"

        # Calculate target pace
        if distance > 0:
            pace_total_sec = target_secs / distance
            pace_min = int(pace_total_sec // 60)
            pace_sec = int(pace_total_sec % 60)
            pace_fmt = f"{pace_min}:{pace_sec:02d}"
        else:
            pace_fmt = "-"

        # Days until race
        race_dt = goal.race_date
        race_d = race_dt.date() if isinstance(race_dt, datetime) else race_dt  # type: ignore[assignment]
        days = (race_d - date.today()).days

        return RaceGoalResponse(
            id=int(goal.id),  # type: ignore[arg-type]
            title=str(goal.title),
            race_date=race_d.isoformat(),
            distance_km=distance,
            target_time_seconds=target_secs,
            target_time_formatted=time_fmt,
            target_pace_formatted=pace_fmt,
            is_active=bool(goal.is_active),
            days_until=days,
            created_at=goal.created_at.isoformat() if goal.created_at else "",  # type: ignore[union-attr]
            updated_at=goal.updated_at.isoformat() if goal.updated_at else "",  # type: ignore[union-attr]
        )


class RaceGoalListResponse(BaseModel):
    """Response-Schema: Liste aller Wettkampf-Ziele."""

    goals: list[RaceGoalResponse]


class GoalProgressResponse(BaseModel):
    """Response-Schema: Ziel-Fortschritt mit aktuellem Pace."""

    goal: RaceGoalResponse
    current_pace_sec_per_km: Optional[float] = None
    current_pace_formatted: Optional[str] = None
    target_pace_sec_per_km: float
    target_pace_formatted: str
    pace_gap_sec: Optional[float] = None
    pace_gap_formatted: Optional[str] = None
    pace_gap_label: Optional[str] = None
    progress_percent: Optional[float] = None
    sessions_used: int = 0
    estimated_finish_seconds: Optional[int] = None
    estimated_finish_formatted: Optional[str] = None
    finish_delta_seconds: Optional[int] = None
    finish_delta_formatted: Optional[str] = None
    finish_delta_label: Optional[str] = None
    weekly_pace_trend_sec: Optional[float] = None
    weekly_pace_trend_label: Optional[str] = None
    weeks_to_goal: Optional[int] = None
    goal_reachable: Optional[bool] = None
