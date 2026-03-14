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
