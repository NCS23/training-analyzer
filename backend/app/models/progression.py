"""Pydantic Schemas für Krafttraining Progression-Tracking (Issue #17)."""

from typing import Optional

from pydantic import BaseModel


class ExerciseHistoryPoint(BaseModel):
    """Einzelner Datenpunkt in der Übungshistorie."""

    date: str
    session_id: int
    max_weight_kg: float
    total_reps: int
    total_sets: int
    completed_sets: int
    tonnage_kg: float
    best_set_weight_kg: float
    best_set_reps: int


class ExerciseHistoryResponse(BaseModel):
    """Verlauf einer Übung über die Zeit."""

    exercise_name: str
    data_points: list[ExerciseHistoryPoint]
    current_max_weight: float
    previous_max_weight: Optional[float] = None
    weight_progression: Optional[float] = None  # +/- kg since last session


class PersonalRecord(BaseModel):
    """Persönliche Bestleistung für eine Übung."""

    exercise_name: str
    record_type: str  # max_weight, max_volume_set, max_tonnage_session
    value: float
    unit: str
    date: str
    session_id: int
    detail: Optional[str] = None  # e.g. "100kg x 8"


class PersonalRecordsResponse(BaseModel):
    """Alle PRs gruppiert nach Übung."""

    records: list[PersonalRecord]
    new_prs_session: Optional[list[PersonalRecord]] = None  # PRs from a specific session


class WeeklyTonnagePoint(BaseModel):
    """Tonnage einer Kalenderwoche."""

    week: str
    week_start: str
    total_tonnage_kg: float
    session_count: int
    exercise_count: int


class TonnageTrendResponse(BaseModel):
    """Wöchentlicher Tonnage-Trend."""

    weeks: list[WeeklyTonnagePoint]
    total_tonnage_kg: float
    avg_weekly_tonnage_kg: float
    trend_direction: Optional[str] = None  # up, down, stable


class ExerciseListItem(BaseModel):
    """Übung in der Übungsliste (für Autocomplete/Selection)."""

    name: str
    category: str
    session_count: int
    last_date: str
    last_max_weight_kg: float
