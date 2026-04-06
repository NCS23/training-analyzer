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
