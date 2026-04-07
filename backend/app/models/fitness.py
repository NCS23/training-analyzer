"""Pydantic Schemas für Fitness-Score API.

Basiert auf dem Banister Fitness-Fatigue-Modell:
- TRIMP (Edwards): Trainingsbelastung pro Session
- CTL (Chronic Training Load): Fitness (~42 Tage EWMA)
- ATL (Acute Training Load): Ermüdung (~7 Tage EWMA)
- TSB (Training Stress Balance): Form = CTL - ATL
- ACWR (Acute:Chronic Workload Ratio): Verletzungsrisiko
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class FormIndicatorResponse(BaseModel):
    """Frische/Ermüdungs-Indikator basierend auf TSB."""

    status: str = Field(..., description="fresh | normal | fatigued")
    label: str = Field(..., description="Frisch | Normal | Ermüdet")
    color: str = Field(..., description="green | yellow | orange")
    recommendation: str


class ACWRResponse(BaseModel):
    """Acute:Chronic Workload Ratio — Verletzungsrisiko-Indikator."""

    ratio: float
    zone: str = Field(..., description="low | optimal | warning | danger")
    message: str


class FitnessScoreResponse(BaseModel):
    """Haupt-Response: Aktueller Fitness-Score mit allen Indikatoren."""

    score: int = Field(..., ge=0, le=100)
    endurance_score: int = Field(..., ge=0, le=100)
    strength_score: int = Field(..., ge=0, le=100)
    trend: str = Field(..., description="rising | stable | falling")
    trend_label: str = Field(..., description="↑ steigend | → stabil | ↓ fallend")
    form: FormIndicatorResponse
    acwr: ACWRResponse | None = None
    context_message: str
    updated_at: str


class FitnessDataPoint(BaseModel):
    """Ein Datenpunkt im Fitness-Verlauf (für Charts)."""

    date: str
    value: float


class FitnessHistoryResponse(BaseModel):
    """Fitness-Verlauf über Zeit (für Fortschritt-Charts)."""

    ctl_history: list[FitnessDataPoint]
    atl_history: list[FitnessDataPoint]
    tsb_history: list[FitnessDataPoint]
    score_history: list[FitnessDataPoint]


class RecalculateResponse(BaseModel):
    """Response für Batch-Neuberechnung."""

    recalculated_sessions: int


# ---------------------------------------------------------------------------
# Insight-Engine Responses
# ---------------------------------------------------------------------------


class InsightResponse(BaseModel):
    """Ein einzelner proaktiver Hinweis."""

    type: str = Field(..., description="warning | trend | achievement | recommendation | info")
    priority: int = Field(..., ge=1, le=10)
    title: str
    message: str
    category: str = Field(..., description="load | balance | performance | plan | recovery")
    icon: str


class InsightsListResponse(BaseModel):
    """Liste aktiver Insights."""

    insights: list[InsightResponse]
    generated_at: str


class IntensityDistributionResponse(BaseModel):
    """80/20-Verteilung der Trainingsintensität."""

    low_percent: float
    medium_percent: float
    high_percent: float
    is_polarized: bool
    total_minutes: float


class TrainingQualityResponse(BaseModel):
    """Trainingsqualität-Metriken."""

    intensity_distribution: IntensityDistributionResponse
    monotony: float
    monotony_level: str
    strain: float
    strain_level: str


# ---------------------------------------------------------------------------
# Today-Dashboard Responses
# ---------------------------------------------------------------------------


class LastSessionSummary(BaseModel):
    """Zusammenfassung der letzten Session mit Einordnung."""

    id: int
    date: str
    workout_type: str
    training_type: str | None = None
    distance_km: float | None = None
    duration_seconds: int | None = None
    avg_pace_formatted: str | None = None
    avg_heartrate: float | None = None
    exercise_count: int | None = None
    tonnage_kg: float | None = None
    rpe: float | None = None
    trimp_score: float | None = None
    comparison_message: str = ""


class DayStatus(BaseModel):
    """Status eines einzelnen Tages in der Wochenübersicht."""

    date: str
    day_name: str
    has_planned: bool
    has_completed: bool
    status: str = Field(..., description="completed | planned | skipped | extra | rest")


class WeekProgressResponse(BaseModel):
    """Wochenfortschritt: geplant vs. erledigt."""

    sessions_completed: int
    sessions_planned: int
    distance_completed_km: float
    distance_planned_km: float | None = None
    time_completed_seconds: int
    time_planned_seconds: int | None = None
    days: list[DayStatus]


class NextSessionInfo(BaseModel):
    """Nächste geplante Session aus dem Wochenplan."""

    day_name: str = Field(..., description="z.B. 'Morgen', 'Mittwoch'")
    workout_type: str = Field(..., description="running | strength")
    description: str = Field(..., description="z.B. 'Intervall-Lauf' oder 'Oberkörper'")


class GoalSummary(BaseModel):
    """Zusammenfassung des aktiven Trainingsziels."""

    title: str
    days_until: int
    target_time_formatted: str | None = None


class TodayResponse(BaseModel):
    """Aggregierte Dashboard-Daten für die Heute-Seite."""

    greeting: str
    motivation: str | None = None
    fitness_score: FitnessScoreResponse
    last_session: LastSessionSummary | None = None
    week_progress: WeekProgressResponse
    insights: list[InsightResponse]
    next_session: NextSessionInfo | None = None
    goal_summary: GoalSummary | None = None
