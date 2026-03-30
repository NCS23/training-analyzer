"""Fitness-Profil-Aggregation aus vorhandenen Athleten-Daten.

Sammelt alle verfügbaren Daten (Schwellentests, HR-Zonen, Trainingshistorie,
Race Goals) und aggregiert sie zu einem `FitnessProfile`, das der
Plan-Generator für individualisierte Trainingspläne nutzt.

Quellen der Daten:
- ThresholdTestModel → LTHR, Max-HR, Schwellenpace
- AthleteModel → Ruhe-HR, Max-HR
- WorkoutModel → Wochenvolumen, Pace-Trends
- RaceGoalModel → Zieldistanz, Zielzeit
- VDOT-Rechner (vdot_calculator.py) → VDOT aus Leistungsdaten
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    AthleteModel,
    RaceGoalModel,
    ThresholdTestModel,
    WorkoutModel,
)
from app.services.vdot_calculator import estimate_vdot

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# FitnessProfile Model
# ---------------------------------------------------------------------------


class FitnessProfile(BaseModel):
    """Aggregiertes Fitness-Profil eines Athleten.

    Alle Felder sind optional — der Plan-Generator nutzt was verfügbar ist
    und fällt auf Defaults zurück wenn Daten fehlen.
    """

    # Herzfrequenz
    resting_hr: Optional[int] = None
    max_hr: Optional[int] = None
    lthr: Optional[int] = None  # Laktatschwellen-HR

    # Leistung
    vdot: Optional[float] = None
    threshold_pace_sec_km: Optional[float] = None  # Schwellenpace sec/km

    # Trainingshistorie (letzte 4-8 Wochen)
    avg_weekly_km: Optional[float] = None
    avg_weekly_sessions: Optional[float] = None
    weeks_consistent_training: int = 0  # Wochen mit ≥2 Sessions

    # Pace-Daten
    avg_easy_pace_sec_km: Optional[float] = None
    best_recent_pace_sec_km: Optional[float] = None  # Schnellste Pace (letzte 8W)

    # Aktives Ziel
    goal_distance_km: Optional[float] = None
    goal_time_seconds: Optional[int] = None
    goal_race_date: Optional[date] = None

    # Meta
    data_quality: str = "none"  # none, low, medium, high
    data_sources: list[str] = []


# ---------------------------------------------------------------------------
# Haupt-API
# ---------------------------------------------------------------------------

# Analyse-Zeiträume
_RECENT_WEEKS = 8  # Für Volumen/Pace-Trends
_CONSISTENCY_WEEKS = 16  # Für Trainings-Konsistenz


async def build_fitness_profile(db: AsyncSession) -> FitnessProfile:
    """Aggregiere alle verfügbaren Athleten-Daten zu einem FitnessProfile.

    Fallback-Kette für fehlende Daten:
    1. Schwellentest → LTHR, Max-HR, Schwellenpace, VDOT
    2. Athleten-Profil → Ruhe-HR, Max-HR (Fallback)
    3. Trainingshistorie → Wochenvolumen, Pace, Konsistenz
    4. Race Goals → Zieldistanz, Zielzeit
    5. Pace-basierte VDOT-Schätzung wenn kein Schwellentest

    Args:
        db: Async DB-Session.

    Returns:
        FitnessProfile mit allen verfügbaren Daten.
    """
    sources: list[str] = []

    # 1. Schwellentest-Daten
    hr_data = await _get_threshold_data(db)
    if hr_data:
        sources.append("threshold_test")

    # 2. Athleten-Profil (Fallback für HR-Daten)
    athlete_data = await _get_athlete_data(db)
    if athlete_data:
        sources.append("athlete_profile")

    # 3. Trainingshistorie
    training_data = await _get_training_history(db)
    if training_data:
        sources.append("training_history")

    # 4. Race Goals
    goal_data = await _get_active_goal(db)
    if goal_data:
        sources.append("race_goal")

    # HR-Werte zusammenführen (Schwellentest > Athleten-Profil)
    resting_hr = athlete_data.get("resting_hr") if athlete_data else None
    max_hr = (hr_data.get("max_hr_measured") if hr_data else None) or (
        athlete_data.get("max_hr") if athlete_data else None
    )
    lthr = hr_data.get("lthr") if hr_data else None
    threshold_pace = hr_data.get("avg_pace_sec") if hr_data else None

    # VDOT schätzen
    vdot = _estimate_vdot_from_data(hr_data, training_data, goal_data)

    # Datenqualität bewerten
    quality = _assess_data_quality(sources, vdot, training_data)

    return FitnessProfile(
        resting_hr=resting_hr,
        max_hr=max_hr,
        lthr=lthr,
        vdot=round(vdot, 1) if vdot else None,
        threshold_pace_sec_km=threshold_pace,
        avg_weekly_km=training_data.get("avg_weekly_km") if training_data else None,
        avg_weekly_sessions=training_data.get("avg_weekly_sessions") if training_data else None,
        weeks_consistent_training=(
            training_data.get("weeks_consistent", 0) if training_data else 0
        ),
        avg_easy_pace_sec_km=training_data.get("avg_easy_pace") if training_data else None,
        best_recent_pace_sec_km=training_data.get("best_pace") if training_data else None,
        goal_distance_km=goal_data.get("distance_km") if goal_data else None,
        goal_time_seconds=goal_data.get("target_time_seconds") if goal_data else None,
        goal_race_date=goal_data.get("race_date") if goal_data else None,
        data_quality=quality,
        data_sources=sources,
    )


# ---------------------------------------------------------------------------
# Datenquellen
# ---------------------------------------------------------------------------


async def _get_threshold_data(db: AsyncSession) -> dict | None:
    """Letzten Schwellentest laden."""
    result = await db.execute(
        select(ThresholdTestModel).order_by(ThresholdTestModel.test_date.desc()).limit(1)
    )
    test = result.scalar_one_or_none()
    if not test:
        return None

    return {
        "lthr": test.lthr,
        "max_hr_measured": test.max_hr_measured,
        "avg_pace_sec": test.avg_pace_sec,
        "test_date": test.test_date,
    }


async def _get_athlete_data(db: AsyncSession) -> dict | None:
    """Athleten-Profil laden (Singleton)."""
    result = await db.execute(select(AthleteModel).limit(1))
    athlete = result.scalar_one_or_none()
    if not athlete:
        return None

    if not athlete.resting_hr and not athlete.max_hr:
        return None

    return {
        "resting_hr": athlete.resting_hr,
        "max_hr": athlete.max_hr,
    }


async def _get_training_history(db: AsyncSession) -> dict | None:
    """Trainingshistorie der letzten Wochen aggregieren."""
    today = date.today()
    start_recent = today - timedelta(weeks=_RECENT_WEEKS)
    start_consistency = today - timedelta(weeks=_CONSISTENCY_WEEKS)

    # Volumen und Sessions (letzte 8 Wochen)
    result = await db.execute(
        select(
            func.count(WorkoutModel.id).label("total_sessions"),
            func.sum(WorkoutModel.distance_km).label("total_km"),
        ).where(
            WorkoutModel.date >= datetime.combine(start_recent, datetime.min.time()),
            WorkoutModel.date <= datetime.combine(today, datetime.max.time()),
            WorkoutModel.workout_type == "running",
        )
    )
    row = result.one()
    total_sessions = row.total_sessions or 0
    total_km = float(row.total_km or 0)

    if total_sessions == 0:
        return None

    avg_weekly_km = round(total_km / _RECENT_WEEKS, 1)
    avg_weekly_sessions = round(total_sessions / _RECENT_WEEKS, 1)

    # Konsistenz (letzte 16 Wochen): Wochen mit ≥2 Running-Sessions
    weeks_consistent = await _count_consistent_weeks(db, start_consistency, today)

    # Pace-Daten (Easy Runs der letzten 8 Wochen)
    avg_easy_pace = await _get_avg_easy_pace(db, start_recent, today)

    # Schnellste Pace (letzte 8 Wochen, nur Runs ≥3km)
    best_pace = await _get_best_recent_pace(db, start_recent, today)

    return {
        "avg_weekly_km": avg_weekly_km,
        "avg_weekly_sessions": avg_weekly_sessions,
        "weeks_consistent": weeks_consistent,
        "avg_easy_pace": avg_easy_pace,
        "best_pace": best_pace,
    }


async def _count_consistent_weeks(db: AsyncSession, start: date, end: date) -> int:
    """Zähle Wochen mit mindestens 2 Lauf-Sessions."""
    result = await db.execute(
        select(
            func.date_trunc("week", WorkoutModel.date).label("week"),
            func.count(WorkoutModel.id).label("cnt"),
        )
        .where(
            WorkoutModel.date >= datetime.combine(start, datetime.min.time()),
            WorkoutModel.date <= datetime.combine(end, datetime.max.time()),
            WorkoutModel.workout_type == "running",
        )
        .group_by("week")
    )
    return sum(1 for row in result.all() if row.cnt >= 2)


async def _get_avg_easy_pace(db: AsyncSession, start: date, end: date) -> float | None:
    """Durchschnittliche Easy-Pace (sec/km) der letzten Wochen.

    Nutzt Sessions die als 'easy', 'recovery' oder 'base' klassifiziert sind.
    """
    easy_types = ("easy", "recovery", "base", "long_run")
    result = await db.execute(
        select(
            func.avg(WorkoutModel.duration_sec / WorkoutModel.distance_km).label("avg_pace"),
        ).where(
            WorkoutModel.date >= datetime.combine(start, datetime.min.time()),
            WorkoutModel.date <= datetime.combine(end, datetime.max.time()),
            WorkoutModel.workout_type == "running",
            WorkoutModel.distance_km > 0,
            WorkoutModel.duration_sec.is_not(None),
            func.coalesce(
                WorkoutModel.training_type_override,
                WorkoutModel.training_type_auto,
            ).in_(easy_types),
        )
    )
    row = result.one()
    pace = row.avg_pace
    return round(float(pace), 1) if pace else None


async def _get_best_recent_pace(db: AsyncSession, start: date, end: date) -> float | None:
    """Schnellste durchschnittliche Pace (sec/km) für Runs ≥3km."""
    result = await db.execute(
        select(
            func.min(WorkoutModel.duration_sec / WorkoutModel.distance_km).label("best_pace"),
        ).where(
            WorkoutModel.date >= datetime.combine(start, datetime.min.time()),
            WorkoutModel.date <= datetime.combine(end, datetime.max.time()),
            WorkoutModel.workout_type == "running",
            WorkoutModel.distance_km >= 3.0,
            WorkoutModel.duration_sec.is_not(None),
        )
    )
    row = result.one()
    pace = row.best_pace
    return round(float(pace), 1) if pace else None


async def _get_active_goal(db: AsyncSession) -> dict | None:
    """Aktives Race Goal laden (nächstes nach Datum)."""
    result = await db.execute(
        select(RaceGoalModel)
        .where(
            RaceGoalModel.is_active.is_(True),
            RaceGoalModel.race_date >= datetime.combine(date.today(), datetime.min.time()),
        )
        .order_by(RaceGoalModel.race_date.asc())
        .limit(1)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        return None

    return {
        "distance_km": goal.distance_km,
        "target_time_seconds": goal.target_time_seconds,
        "race_date": goal.race_date.date()
        if isinstance(goal.race_date, datetime)
        else goal.race_date,
    }


# ---------------------------------------------------------------------------
# VDOT-Schätzung
# ---------------------------------------------------------------------------


def _estimate_vdot_from_data(
    hr_data: dict | None,
    training_data: dict | None,
    goal_data: dict | None,
) -> float | None:
    """Schätze VDOT aus den besten verfügbaren Daten.

    Priorität:
    1. Schwellentest-Pace (genaueste Quelle)
    2. Beste kürzliche Pace + geschätzte Distanz
    3. Zielzeit (als Untergrenze)
    """
    # 1. Aus Schwellentest-Pace (30min-Test ≈ Schwellenpace ≈ 10K-Pace)
    if hr_data and hr_data.get("avg_pace_sec"):
        pace_sec_km = hr_data["avg_pace_sec"]
        # 30min Schwellentest ≈ 10K-Leistung
        estimated_10k_time = pace_sec_km * 10.0
        vdot = estimate_vdot(10.0, estimated_10k_time)
        if vdot:
            return vdot

    # 2. Aus bester kürzlicher Pace (grobe Schätzung)
    if training_data and training_data.get("best_pace"):
        best_pace = training_data["best_pace"]
        # Schnellste durchschnittliche Pace → grobe 5K-Schätzung
        estimated_5k_time = best_pace * 5.0
        vdot = estimate_vdot(5.0, estimated_5k_time)
        if vdot:
            # Abschlag weil Trainingspace ≠ Wettkampfpace
            return vdot * 0.95

    # 3. Aus Zielzeit (als konservative Schätzung)
    if goal_data and goal_data.get("distance_km") and goal_data.get("target_time_seconds"):
        vdot = estimate_vdot(goal_data["distance_km"], goal_data["target_time_seconds"])
        if vdot:
            # Ziel-VDOT minus Puffer (Ziel > aktuelles Niveau)
            return vdot * 0.92

    return None


# ---------------------------------------------------------------------------
# Datenqualität
# ---------------------------------------------------------------------------


def _assess_data_quality(
    sources: list[str],
    vdot: float | None,
    training_data: dict | None,
) -> str:
    """Bewerte die Qualität der verfügbaren Daten.

    Returns:
        "high": Schwellentest + Trainingshistorie vorhanden
        "medium": Trainingshistorie mit ≥4 Wochen Konsistenz
        "low": Nur rudimentäre Daten
        "none": Keine verwertbaren Daten
    """
    if not sources:
        return "none"

    has_threshold = "threshold_test" in sources
    has_training = "training_history" in sources
    weeks = training_data.get("weeks_consistent", 0) if training_data else 0

    if has_threshold and has_training and weeks >= 4:
        return "high"

    if has_training and weeks >= 4:
        return "medium"

    if vdot is not None or has_training:
        return "low"

    return "none"
