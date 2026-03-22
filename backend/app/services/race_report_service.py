"""Race Report Service — Post-Race Analyse (#52).

Berechnet race-spezifische Metriken: Pacing-Strategie, Pace-Konsistenz,
HR-Management, Trainingsvergleich und historische Rennen.
"""

from __future__ import annotations

import json
import math
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import RaceGoalModel, WorkoutModel
from app.models.race_report import (
    GoalComparison,
    HRManagement,
    PaceConsistency,
    PacingStrategy,
    PreviousRace,
    RaceReportResponse,
    TrainingComparison,
)
from app.services.km_split_calculator import calculate_km_splits


def _format_time(seconds: int) -> str:
    """Formatiert Sekunden als H:MM:SS oder MM:SS."""
    hours = seconds // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{mins:02d}:{secs:02d}"
    return f"{mins}:{secs:02d}"


def _format_pace(sec_per_km: float) -> str:
    """Formatiert Pace (sec/km) als M:SS."""
    mins = int(sec_per_km // 60)
    secs = int(sec_per_km % 60)
    return f"{mins}:{secs:02d}"


def _format_delta(seconds: int) -> str:
    """Formatiert Delta als +/-M:SS."""
    sign = "+" if seconds >= 0 else "-"
    abs_sec = abs(seconds)
    mins = abs_sec // 60
    secs = abs_sec % 60
    return f"{sign}{mins}:{secs:02d}"


async def generate_race_report(
    session_id: int,
    db: AsyncSession,
) -> RaceReportResponse:
    """Erstellt vollstaendigen Race Report fuer eine Session."""
    workout = await _load_workout(session_id, db)
    if not workout:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Session nicht gefunden")

    splits = _get_splits(workout)

    goal_comparison = await _compute_goal_comparison(workout, db)
    pacing_strategy = _compute_pacing_strategy(splits)
    pace_consistency = _compute_pace_consistency(splits)
    hr_management = _compute_hr_management(workout)
    training_comparison = await _compute_training_comparison(workout, db)
    previous_races = await _find_previous_races(workout, db)

    return RaceReportResponse(
        session_id=session_id,
        goal_comparison=goal_comparison,
        pacing_strategy=pacing_strategy,
        pace_consistency=pace_consistency,
        hr_management=hr_management,
        training_comparison=training_comparison,
        previous_races=previous_races,
    )


async def _load_workout(session_id: int, db: AsyncSession) -> WorkoutModel | None:
    result = await db.execute(select(WorkoutModel).where(WorkoutModel.id == session_id))
    return result.scalar_one_or_none()


def _get_splits(workout: WorkoutModel) -> list[dict]:
    """Berechnet KM-Splits aus GPS-Track."""
    if not workout.gps_track_json:
        return []
    gps_track = json.loads(str(workout.gps_track_json))
    return calculate_km_splits(gps_track)


async def _compute_goal_comparison(
    workout: WorkoutModel,
    db: AsyncSession,
) -> GoalComparison | None:
    """Vergleicht Rennergebnis mit verknuepftem oder auto-gematchtem Ziel."""
    goal = await _find_matching_goal(workout, db)
    if not goal or not workout.duration_sec or not workout.distance_km:
        return None

    actual_sec = workout.duration_sec
    target_sec = goal.target_time_seconds
    delta = actual_sec - target_sec

    target_pace = target_sec / goal.distance_km
    actual_pace = actual_sec / workout.distance_km

    return GoalComparison(
        goal_id=goal.id,
        goal_title=str(goal.title),
        target_time_seconds=target_sec,
        target_time_formatted=_format_time(target_sec),
        actual_time_seconds=actual_sec,
        actual_time_formatted=_format_time(actual_sec),
        delta_seconds=delta,
        delta_formatted=_format_delta(delta),
        target_achieved=delta <= 0,
        target_pace_sec_per_km=round(target_pace, 1),
        target_pace_formatted=_format_pace(target_pace),
        actual_pace_sec_per_km=round(actual_pace, 1),
        actual_pace_formatted=_format_pace(actual_pace),
    )


async def _find_matching_goal(
    workout: WorkoutModel,
    db: AsyncSession,
) -> RaceGoalModel | None:
    """Findet passendes Ziel: erst race_goal_id, dann Auto-Match."""
    if workout.race_goal_id:
        result = await db.execute(
            select(RaceGoalModel).where(RaceGoalModel.id == workout.race_goal_id)
        )
        return result.scalar_one_or_none()

    # Auto-Match: race_date ±1 Tag UND distance_km ±10%
    if not workout.distance_km:
        return None

    workout_date = workout.date.date() if isinstance(workout.date, datetime) else workout.date
    date_min = workout_date - timedelta(days=1)
    date_max = workout_date + timedelta(days=1)
    dist_min = workout.distance_km * 0.9
    dist_max = workout.distance_km * 1.1

    result = await db.execute(
        select(RaceGoalModel)
        .where(RaceGoalModel.race_date >= date_min)
        .where(RaceGoalModel.race_date <= date_max)
        .where(RaceGoalModel.distance_km >= dist_min)
        .where(RaceGoalModel.distance_km <= dist_max)
        .order_by(RaceGoalModel.race_date.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def _compute_pacing_strategy(splits: list[dict]) -> PacingStrategy | None:
    """Erkennt Negative/Positive/Even Split."""
    full_splits = [s for s in splits if not s.get("is_partial")]
    if len(full_splits) < 2:
        return None

    mid = len(full_splits) // 2
    first_half = full_splits[:mid]
    second_half = full_splits[mid:]

    first_avg_pace = _weighted_avg_pace(first_half)
    second_avg_pace = _weighted_avg_pace(second_half)
    if first_avg_pace is None or second_avg_pace is None:
        return None

    delta_sec = second_avg_pace - first_avg_pace  # positiv = 2. Haelfte langsamer

    # Schwellwert: ±3 sec/km = Even Split
    if abs(delta_sec) <= 3:
        strategy_type = "even_split"
        label = "Even Split"
    elif delta_sec < 0:
        strategy_type = "negative_split"
        label = "Negative Split"
    else:
        strategy_type = "positive_split"
        label = "Positive Split"

    return PacingStrategy(
        type=strategy_type,
        label=label,
        first_half_pace_formatted=_format_pace(first_avg_pace),
        second_half_pace_formatted=_format_pace(second_avg_pace),
        split_delta_sec=round(delta_sec, 1),
    )


def _weighted_avg_pace(splits: list[dict]) -> float | None:
    """Berechnet distanz-gewichteten Durchschnittspace (sec/km)."""
    total_sec = 0.0
    total_km = 0.0
    for s in splits:
        pace = s.get("pace_min_per_km")
        dist = s.get("distance_km", 0)
        if pace is not None and dist > 0:
            total_sec += pace * 60.0 * dist
            total_km += dist
    if total_km <= 0:
        return None
    return total_sec / total_km


def _compute_pace_consistency(splits: list[dict]) -> PaceConsistency | None:
    """Berechnet Pace-Gleichmaessigkeit (Variationskoeffizient)."""
    full_splits = [s for s in splits if not s.get("is_partial")]
    paces = [s["pace_min_per_km"] for s in full_splits if s.get("pace_min_per_km")]
    if len(paces) < 3:
        return None

    mean = sum(paces) / len(paces)
    variance = sum((p - mean) ** 2 for p in paces) / len(paces)
    std_dev = math.sqrt(variance)
    cv = (std_dev / mean) * 100 if mean > 0 else 0

    if cv < 3:
        label = "Sehr gleichmaessig"
    elif cv < 6:
        label = "Gleichmaessig"
    else:
        label = "Ungleichmaessig"

    fastest_idx = paces.index(min(paces))
    slowest_idx = paces.index(max(paces))

    return PaceConsistency(
        coefficient_of_variation=round(cv, 1),
        label=label,
        fastest_km=full_splits[fastest_idx]["km_number"],
        slowest_km=full_splits[slowest_idx]["km_number"],
        fastest_pace_formatted=_format_pace(min(paces) * 60),
        slowest_pace_formatted=_format_pace(max(paces) * 60),
    )


def _compute_hr_management(workout: WorkoutModel) -> HRManagement | None:
    """Analysiert HR-Verhalten waehrend des Rennens."""
    if not workout.hr_avg or not workout.hr_max:
        return None

    zone_distribution = _get_zone_distribution(workout)

    hr_drift = _compute_hr_drift(workout)
    hr_drift_label = None
    if hr_drift is not None:
        if hr_drift < 3:
            hr_drift_label = "Sehr gut kontrolliert"
        elif hr_drift < 8:
            hr_drift_label = "Gut kontrolliert"
        else:
            hr_drift_label = "Hoher HR-Drift — zu schnell gestartet?"

    return HRManagement(
        avg_hr=workout.hr_avg,
        max_hr=workout.hr_max,
        zone_distribution=zone_distribution,
        hr_drift_pct=hr_drift,
        hr_drift_label=hr_drift_label,
    )


def _get_zone_distribution(workout: WorkoutModel) -> dict[str, float]:
    """Liest gespeicherte HR-Zonen-Verteilung."""
    if not workout.hr_zones_json:
        return {}
    zones = json.loads(str(workout.hr_zones_json))
    return {k: v.get("percentage", 0) for k, v in zones.items() if isinstance(v, dict)}


def _compute_hr_drift(workout: WorkoutModel) -> float | None:
    """Berechnet HR-Drift: Anstieg der durchschnittlichen HR (1. vs 2. Haelfte)."""
    if not workout.hr_timeseries_json:
        return None

    ts_list = json.loads(str(workout.hr_timeseries_json))
    hr_values = [entry.get("hr") for entry in ts_list if entry.get("hr")]
    if len(hr_values) < 60:
        return None

    mid = len(hr_values) // 2
    first_avg = sum(hr_values[:mid]) / mid
    second_avg = sum(hr_values[mid:]) / (len(hr_values) - mid)

    if first_avg <= 0:
        return None
    drift_pct = ((second_avg - first_avg) / first_avg) * 100
    return round(drift_pct, 1)


async def _compute_training_comparison(
    workout: WorkoutModel,
    db: AsyncSession,
) -> TrainingComparison | None:
    """Vergleicht Race-Pace mit Trainings-Durchschnitt der letzten 4 Wochen."""
    if not workout.duration_sec or not workout.distance_km:
        return None

    workout_date = workout.date.date() if isinstance(workout.date, datetime) else workout.date
    date_from = workout_date - timedelta(weeks=4)

    result = await db.execute(
        select(WorkoutModel)
        .where(WorkoutModel.workout_type == "running")
        .where(WorkoutModel.date >= date_from)
        .where(WorkoutModel.date < workout_date)
        .where(WorkoutModel.id != workout.id)
        .where(WorkoutModel.duration_sec.isnot(None))
        .where(WorkoutModel.distance_km > 0)
    )
    training_sessions = result.scalars().all()

    if not training_sessions:
        return None

    total_sec = sum(s.duration_sec for s in training_sessions if s.duration_sec)
    total_km = sum(s.distance_km for s in training_sessions if s.distance_km)
    if total_km <= 0:
        return None

    avg_training_pace = total_sec / total_km
    race_pace = workout.duration_sec / workout.distance_km

    delta_pct = ((avg_training_pace - race_pace) / avg_training_pace) * 100

    return TrainingComparison(
        avg_training_pace_sec=round(avg_training_pace, 1),
        avg_training_pace_formatted=_format_pace(avg_training_pace),
        race_pace_sec=round(race_pace, 1),
        race_pace_formatted=_format_pace(race_pace),
        delta_pct=round(delta_pct, 1),
    )


async def _find_previous_races(
    workout: WorkoutModel,
    db: AsyncSession,
) -> list[PreviousRace]:
    """Findet vorherige Rennen aehnlicher Distanz (±10%)."""
    if not workout.distance_km or not workout.duration_sec:
        return []

    dist_min = workout.distance_km * 0.9
    dist_max = workout.distance_km * 1.1

    result = await db.execute(
        select(WorkoutModel)
        .where(WorkoutModel.id != workout.id)
        .where(WorkoutModel.workout_type == "running")
        .where(WorkoutModel.distance_km >= dist_min)
        .where(WorkoutModel.distance_km <= dist_max)
        .where(WorkoutModel.duration_sec.isnot(None))
        .where(
            (WorkoutModel.training_type_override == "race")
            | (
                (WorkoutModel.training_type_override.is_(None))
                & (WorkoutModel.training_type_auto == "race")
            )
        )
        .order_by(WorkoutModel.date.desc())
        .limit(10)
    )
    races = result.scalars().all()

    current_sec = workout.duration_sec
    previous: list[PreviousRace] = []
    for r in races:
        if not r.duration_sec or not r.distance_km:
            continue
        r_date = r.date.date() if isinstance(r.date, datetime) else r.date
        pace_sec = r.duration_sec / r.distance_km
        previous.append(
            PreviousRace(
                session_id=r.id,
                date=r_date.isoformat() if isinstance(r_date, date) else str(r_date),
                distance_km=round(r.distance_km, 2),
                duration_formatted=_format_time(r.duration_sec),
                pace_formatted=_format_pace(pace_sec),
                delta_seconds=r.duration_sec - current_sec,
            )
        )

    return previous
