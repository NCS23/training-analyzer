"""Pydantic Models für wöchentliches KI-Trainingsreview (E06-S06)."""

from enum import Enum

from pydantic import BaseModel


class OverallRating(str, Enum):
    """Gesamtbewertung der Trainingswoche."""

    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"


class FatigueLevel(str, Enum):
    """Ermüdungseinschätzung."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class VolumeComparison(BaseModel):
    """Soll/Ist-Vergleich des Wochenvolumens."""

    planned_km: float | None = None
    actual_km: float
    planned_sessions: int | None = None
    actual_sessions: int
    planned_hours: float | None = None
    actual_hours: float


class WeeklyReviewResponse(BaseModel):
    """Wöchentliches KI-Trainingsreview — Response."""

    id: int
    week_start: str
    summary: str
    volume_comparison: VolumeComparison
    highlights: list[str]
    improvements: list[str]
    next_week_recommendations: list[str]
    overall_rating: OverallRating
    fatigue_assessment: FatigueLevel
    session_count: int
    provider: str
    cached: bool = False
    created_at: str


class WeeklyReviewGenerateRequest(BaseModel):
    """Request zum Generieren eines Wochen-Reviews."""

    week_start: str  # ISO-Datum (Montag), z.B. "2026-03-10"
    force_refresh: bool = False
