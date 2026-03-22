"""Pydantic Models für KI Session-Analyse."""

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    """Request für Session-Analyse."""

    force_refresh: bool = False


class SessionAnalysisResponse(BaseModel):
    """Strukturierte KI-Analyse einer Trainingseinheit."""

    session_id: int
    provider: str
    summary: str
    intensity_rating: str  # leicht|moderat|intensiv|zu_intensiv
    intensity_text: str
    hr_zone_assessment: str
    plan_comparison: str | None = None
    fatigue_indicators: str | None = None
    recommendations: list[str]
    cached: bool = False


class RaceAnalysisResponse(BaseModel):
    """KI-Analyse speziell fuer Wettkampf-Sessions (#52)."""

    session_id: int
    provider: str
    pacing_assessment: str
    goal_assessment: str | None = None
    what_went_well: list[str]
    lessons_learned: list[str]
    summary: str
    cached: bool = False
