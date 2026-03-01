"""Training Balance Analysis API (Issue #48)."""

import json
from collections import Counter
from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import WorkoutModel
from app.infrastructure.database.session import get_db
from app.models.training_balance import (
    BalanceInsight,
    IntensityDistribution,
    MuscleGroupBalance,
    SportMix,
    TrainingBalanceResponse,
    VolumeWeek,
)

router = APIRouter(prefix="/training-balance", tags=["analytics"])

# Classification of running types into intensity zones
EASY_TYPES = {"recovery", "easy", "long_run"}
MODERATE_TYPES = {"tempo"}
HARD_TYPES = {"intervals", "threshold", "race"}

# Muscle group mapping from exercise categories
CATEGORY_TO_MUSCLE = {
    "push": "Brust/Schulter/Trizeps",
    "pull": "Rücken/Bizeps",
    "legs": "Beine",
    "core": "Core",
    "cardio": "Kardio",
}


@router.get("", response_model=TrainingBalanceResponse)
async def get_training_balance(
    days: int = Query(default=28, ge=7, le=365),
    db: AsyncSession = Depends(get_db),
) -> TrainingBalanceResponse:
    """Analyse the training balance over a given period."""
    cutoff = datetime.utcnow() - timedelta(days=days)

    # Fetch all sessions in period
    result = await db.execute(
        select(
            WorkoutModel.date,
            WorkoutModel.workout_type,
            WorkoutModel.distance_km,
            WorkoutModel.duration_sec,
            WorkoutModel.exercises_json,
            func.coalesce(
                WorkoutModel.training_type_override,
                WorkoutModel.training_type_auto,
            ).label("effective_type"),
        )
        .where(WorkoutModel.date >= cutoff)
        .order_by(WorkoutModel.date.asc())
    )
    sessions = result.all()

    # Compute all metrics
    intensity = _compute_intensity(sessions)
    volume_weeks = _compute_volume_weeks(sessions)
    muscle_groups = _compute_muscle_groups(sessions)
    sport_mix = _compute_sport_mix(sessions)
    insights = _compute_insights(intensity, volume_weeks, muscle_groups, sport_mix)

    return TrainingBalanceResponse(
        period_days=days,
        intensity=intensity,
        volume_weeks=volume_weeks,
        muscle_groups=muscle_groups,
        sport_mix=sport_mix,
        insights=insights,
    )


def _compute_intensity(sessions: Sequence[Any]) -> IntensityDistribution:
    """Classify running sessions into easy/moderate/hard intensity zones."""
    easy = 0
    moderate = 0
    hard = 0

    for s in sessions:
        if str(s.workout_type) != "running":
            continue
        etype = str(s.effective_type).lower() if s.effective_type else "easy"
        if etype in EASY_TYPES:
            easy += 1
        elif etype in MODERATE_TYPES:
            moderate += 1
        elif etype in HARD_TYPES:
            hard += 1
        else:
            easy += 1  # Default to easy

    total = easy + moderate + hard
    if total == 0:
        return IntensityDistribution(
            easy_percent=0,
            moderate_percent=0,
            hard_percent=0,
        )

    easy_pct = round(easy / total * 100, 1)
    mod_pct = round(moderate / total * 100, 1)
    hard_pct = round(hard / total * 100, 1)
    is_polarized = easy_pct >= 75 and (moderate + hard) > 0

    return IntensityDistribution(
        easy_percent=easy_pct,
        moderate_percent=mod_pct,
        hard_percent=hard_pct,
        easy_sessions=easy,
        moderate_sessions=moderate,
        hard_sessions=hard,
        total_sessions=total,
        is_polarized=is_polarized,
    )


def _compute_volume_weeks(sessions: Sequence[Any]) -> list[VolumeWeek]:
    """Group sessions by ISO week and compute volume per week."""
    weeks: dict[str, dict] = {}

    for s in sessions:
        session_date = s.date
        if isinstance(session_date, datetime):
            session_date = session_date.date()

        week_key = s.date.strftime("%G-W%V")
        monday = session_date - timedelta(days=session_date.weekday())

        if week_key not in weeks:
            weeks[week_key] = {
                "week_start": monday.isoformat(),
                "running_km": 0.0,
                "running_min": 0,
                "strength_sessions": 0,
                "total_sessions": 0,
            }

        w = weeks[week_key]
        w["total_sessions"] += 1

        if str(s.workout_type) == "running":
            w["running_km"] += float(s.distance_km) if s.distance_km else 0
            w["running_min"] += int(s.duration_sec) // 60 if s.duration_sec else 0
        elif str(s.workout_type) == "strength":
            w["strength_sessions"] += 1

    result: list[VolumeWeek] = []
    prev_km: Optional[float] = None

    for week_key in sorted(weeks.keys()):
        w = weeks[week_key]
        km = round(w["running_km"], 1)

        change: Optional[float] = None
        if prev_km is not None and prev_km > 0:
            change = round((km - prev_km) / prev_km * 100, 1)

        result.append(
            VolumeWeek(
                week=week_key,
                week_start=w["week_start"],
                running_km=km,
                running_min=w["running_min"],
                strength_sessions=w["strength_sessions"],
                total_sessions=w["total_sessions"],
                volume_change_percent=change,
            )
        )
        prev_km = km

    return result


def _compute_muscle_groups(sessions: Sequence[Any]) -> list[MuscleGroupBalance]:
    """Analyse muscle group distribution from strength training."""
    group_sets: Counter[str] = Counter()
    group_sessions: Counter[str] = Counter()

    for s in sessions:
        if str(s.workout_type) != "strength" or not s.exercises_json:
            continue

        try:
            exercises = json.loads(str(s.exercises_json))
        except (json.JSONDecodeError, TypeError):
            continue

        session_groups: set[str] = set()
        for ex in exercises:
            cat = str(ex.get("category", "")).lower()
            group = CATEGORY_TO_MUSCLE.get(cat, cat.capitalize() if cat else "Sonstiges")
            sets_count = len(ex.get("sets", []))
            group_sets[group] += sets_count
            session_groups.add(group)

        for g in session_groups:
            group_sessions[g] += 1

    total_sets = sum(group_sets.values())
    if total_sets == 0:
        return []

    result: list[MuscleGroupBalance] = []
    for group, sets in group_sets.most_common():
        result.append(
            MuscleGroupBalance(
                group=group,
                session_count=group_sessions[group],
                total_sets=sets,
                percentage=round(sets / total_sets * 100, 1),
            )
        )

    return result


def _compute_sport_mix(sessions: Sequence[Any]) -> SportMix:
    """Distribution across sport types."""
    running = sum(1 for s in sessions if str(s.workout_type) == "running")
    strength = sum(1 for s in sessions if str(s.workout_type) == "strength")
    total = len(sessions)

    if total == 0:
        return SportMix()

    return SportMix(
        running_sessions=running,
        strength_sessions=strength,
        running_percent=round(running / total * 100, 1),
        strength_percent=round(strength / total * 100, 1),
        total_sessions=total,
    )


def _compute_insights(
    intensity: IntensityDistribution,
    volume_weeks: list[VolumeWeek],
    muscle_groups: list[MuscleGroupBalance],
    sport_mix: SportMix,
) -> list[BalanceInsight]:
    """Generate insights and warnings from balance data."""
    insights: list[BalanceInsight] = []

    # Intensity: 80/20 rule check
    if intensity.total_sessions >= 3:
        if intensity.is_polarized:
            insights.append(
                BalanceInsight(
                    type="positive",
                    category="intensity",
                    message=f"Gute Polarisierung: {intensity.easy_percent:.0f}% locker, "
                    f"{intensity.moderate_percent + intensity.hard_percent:.0f}% intensiv.",
                )
            )
        elif intensity.hard_percent + intensity.moderate_percent > 40:
            insights.append(
                BalanceInsight(
                    type="warning",
                    category="intensity",
                    message=f"Zu viel Intensität: {intensity.hard_percent + intensity.moderate_percent:.0f}% "
                    "intensiv (Ziel: max 20%). Mehr lockere Läufe einbauen.",
                )
            )

    # Volume: 10% rule
    for vw in volume_weeks:
        if vw.volume_change_percent is not None and vw.volume_change_percent > 10:
            insights.append(
                BalanceInsight(
                    type="warning",
                    category="volume",
                    message=f"Woche {vw.week}: Volumen um {vw.volume_change_percent:.0f}% "
                    "gesteigert (10%-Regel beachten).",
                )
            )
            break  # Only warn for the most recent spike

    # Muscle group balance
    if len(muscle_groups) >= 2:
        top = muscle_groups[0]
        bottom = muscle_groups[-1]
        if top.percentage > 50 and len(muscle_groups) > 2:
            insights.append(
                BalanceInsight(
                    type="warning",
                    category="muscle",
                    message=f"Ungleichmäßig: {top.group} dominiert mit "
                    f"{top.percentage:.0f}% aller Sätze. "
                    f"{bottom.group} könnte mehr Aufmerksamkeit brauchen.",
                )
            )

    # Sport mix
    if sport_mix.total_sessions >= 4:
        if sport_mix.strength_sessions == 0:
            insights.append(
                BalanceInsight(
                    type="warning",
                    category="sport_mix",
                    message="Kein Krafttraining im Zeitraum. "
                    "Ergänzendes Krafttraining hilft Verletzungen vorzubeugen.",
                )
            )
        elif sport_mix.running_sessions == 0:
            insights.append(
                BalanceInsight(
                    type="neutral",
                    category="sport_mix",
                    message="Nur Krafttraining im Zeitraum. "
                    "Ausdauereinheiten ergänzen die Fitness.",
                )
            )
        elif sport_mix.strength_percent >= 20 and sport_mix.running_percent >= 40:
            insights.append(
                BalanceInsight(
                    type="positive",
                    category="sport_mix",
                    message="Guter Mix aus Laufen und Kraft!",
                )
            )

    return insights
