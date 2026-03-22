"""Pydantic Schemas fuer Race Report API (#52)."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class GoalComparison(BaseModel):
    """Vergleich des Rennergebnisses mit dem Wettkampf-Ziel."""

    goal_id: int
    goal_title: str
    target_time_seconds: int
    target_time_formatted: str
    actual_time_seconds: int
    actual_time_formatted: str
    delta_seconds: int  # positiv = langsamer als Ziel
    delta_formatted: str
    target_achieved: bool
    target_pace_sec_per_km: float
    target_pace_formatted: str
    actual_pace_sec_per_km: float
    actual_pace_formatted: str


class PacingStrategy(BaseModel):
    """Analyse der Pacing-Strategie (Negative/Positive/Even Split)."""

    type: str  # "negative_split" | "positive_split" | "even_split"
    label: str
    first_half_pace_formatted: str
    second_half_pace_formatted: str
    split_delta_sec: float  # positiv = 2. Haelfte langsamer


class PaceConsistency(BaseModel):
    """Gleichmaessigkeit der Pace ueber alle KM-Splits."""

    coefficient_of_variation: float  # CV in %
    label: str  # "Sehr gleichmaessig" / "Gleichmaessig" / "Ungleichmaessig"
    fastest_km: int
    slowest_km: int
    fastest_pace_formatted: str
    slowest_pace_formatted: str


class HRManagement(BaseModel):
    """Herzfrequenz-Analyse waehrend des Rennens."""

    avg_hr: int
    max_hr: int
    zone_distribution: dict[str, float]  # zone_name -> percentage
    hr_drift_pct: Optional[float] = None  # HR-Anstieg 1. vs 2. Haelfte
    hr_drift_label: Optional[str] = None


class TrainingComparison(BaseModel):
    """Vergleich Race-Pace vs. Trainingsdurchschnitt."""

    avg_training_pace_sec: float
    avg_training_pace_formatted: str
    race_pace_sec: float
    race_pace_formatted: str
    delta_pct: float  # positiv = schneller als Training


class PreviousRace(BaseModel):
    """Vorheriges Rennen gleicher Distanz."""

    session_id: int
    date: str
    distance_km: float
    duration_formatted: str
    pace_formatted: str
    delta_seconds: int  # vs aktuelles Rennen


class RaceReportResponse(BaseModel):
    """Vollstaendiger Race Report fuer eine Wettkampf-Session."""

    session_id: int
    goal_comparison: Optional[GoalComparison] = None
    pacing_strategy: Optional[PacingStrategy] = None
    pace_consistency: Optional[PaceConsistency] = None
    hr_management: Optional[HRManagement] = None
    training_comparison: Optional[TrainingComparison] = None
    previous_races: list[PreviousRace] = []
