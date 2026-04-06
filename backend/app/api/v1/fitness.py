"""Fitness-Score API — Endpunkte für Score, Form, ACWR, History, Insights, Today.

Basiert auf dem Banister Fitness-Fatigue-Modell (#675, #676).
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import AthleteModel, WorkoutModel
from app.infrastructure.database.session import get_db
from app.models.fitness import (
    DayStatus,
    FitnessHistoryResponse,
    FitnessScoreResponse,
    InsightResponse,
    InsightsListResponse,
    IntensityDistributionResponse,
    LastSessionSummary,
    RecalculateResponse,
    TodayResponse,
    TrainingQualityResponse,
    WeekProgressResponse,
)
from app.services.fitness_score import (
    ACWRResult,
    FormIndicator,
    calculate_trimp,
    compute_full_score,
    compute_history,
)
from app.services.insight_engine import InsightContext, generate_insights
from app.services.training_quality import (
    calculate_intensity_distribution,
    calculate_monotony,
    calculate_strain,
    get_last_7_days_trimps,
)

router = APIRouter(prefix="/fitness", tags=["fitness"])


async def _get_athlete(db: AsyncSession) -> AthleteModel | None:
    result = await db.execute(select(AthleteModel).limit(1))
    return result.scalar_one_or_none()


async def _get_all_sessions(db: AsyncSession) -> list[WorkoutModel]:
    result = await db.execute(select(WorkoutModel).order_by(WorkoutModel.date.asc()))
    return list(result.scalars().all())


@router.get("/score", response_model=FitnessScoreResponse)
async def get_fitness_score(
    db: AsyncSession = Depends(get_db),
) -> FitnessScoreResponse:
    """Aktueller Fitness-Score mit Form-Indikator und ACWR."""
    athlete = await _get_athlete(db)
    sessions = await _get_all_sessions(db)

    personal_max_ctl = athlete.personal_max_ctl if athlete else None

    result = compute_full_score(sessions, personal_max_ctl)

    # Max CTL aktualisieren wenn nötig
    if athlete and result["new_max_ctl"] and result["new_max_ctl"] != personal_max_ctl:
        athlete.personal_max_ctl = result["new_max_ctl"]
        await db.commit()

    return FitnessScoreResponse(
        score=result["score"],
        endurance_score=result["endurance_score"],
        strength_score=result["strength_score"],
        trend=result["trend"],
        trend_label=result["trend_label"],
        form=result["form"],
        acwr=result["acwr"],
        context_message=result["context_message"],
        updated_at=datetime.utcnow().isoformat(),
    )


@router.get("/history", response_model=FitnessHistoryResponse)
async def get_fitness_history(
    days: int = Query(90, ge=7, le=365, description="Anzahl Tage für den Verlauf"),
    db: AsyncSession = Depends(get_db),
) -> FitnessHistoryResponse:
    """Fitness-Verlauf (CTL/ATL/TSB/Score) für Charts."""
    athlete = await _get_athlete(db)
    sessions = await _get_all_sessions(db)

    personal_max_ctl = athlete.personal_max_ctl if athlete else None
    history = compute_history(sessions, personal_max_ctl, days)

    return FitnessHistoryResponse(**history)


@router.post("/recalculate", response_model=RecalculateResponse)
async def recalculate_trimp(
    db: AsyncSession = Depends(get_db),
) -> RecalculateResponse:
    """Batch-Neuberechnung aller TRIMP-Werte.

    Nützlich nach Migration oder wenn sich die Berechnungslogik ändert.
    """
    sessions = await _get_all_sessions(db)
    count = 0

    for session in sessions:
        trimp = calculate_trimp(session)
        if trimp != session.trimp_score:
            session.trimp_score = trimp
            count += 1

    if count > 0:
        await db.commit()

    return RecalculateResponse(recalculated_sessions=count)


# ---------------------------------------------------------------------------
# Insights & Trainingsqualität (#676)
# ---------------------------------------------------------------------------


@router.get("/insights", response_model=InsightsListResponse)
async def get_insights(
    max_count: int = Query(5, ge=1, le=20, alias="max"),
    db: AsyncSession = Depends(get_db),
) -> InsightsListResponse:
    """Aktuelle trainingswissenschaftliche Insights."""
    athlete = await _get_athlete(db)
    sessions = await _get_all_sessions(db)

    resting_hr = (athlete.resting_hr or 60) if athlete else 60
    max_hr = (athlete.max_hr or 190) if athlete else 190
    personal_max_ctl = athlete.personal_max_ctl if athlete else None

    score_result = compute_full_score(sessions, personal_max_ctl)
    intensity = calculate_intensity_distribution(sessions, resting_hr, max_hr)
    trimps_7d = get_last_7_days_trimps(sessions)
    monotony = calculate_monotony(trimps_7d)

    form = FormIndicator(**score_result["form"])
    acwr_data = score_result["acwr"]
    acwr = ACWRResult(**acwr_data) if acwr_data else None

    ctx = InsightContext(
        acwr=acwr,
        form=form,
        trend=score_result["trend"],
        intensity=intensity,
        monotony=monotony,
        sessions=sessions,
    )
    insights = generate_insights(ctx, max_insights=max_count)

    return InsightsListResponse(
        insights=[
            InsightResponse(
                type=i.type,
                priority=i.priority,
                title=i.title,
                message=i.message,
                category=i.category,
                icon=i.icon,
            )
            for i in insights
        ],
        generated_at=datetime.utcnow().isoformat(),
    )


@router.get("/quality", response_model=TrainingQualityResponse)
async def get_training_quality(
    days: int = Query(28, ge=7, le=180),
    db: AsyncSession = Depends(get_db),
) -> TrainingQualityResponse:
    """Trainingsqualität: 80/20-Verteilung, Monotonie, Strain."""
    athlete = await _get_athlete(db)
    sessions = await _get_all_sessions(db)

    resting_hr = (athlete.resting_hr or 60) if athlete else 60
    max_hr = (athlete.max_hr or 190) if athlete else 190

    intensity = calculate_intensity_distribution(sessions, resting_hr, max_hr, days)
    trimps_7d = get_last_7_days_trimps(sessions)
    monotony = calculate_monotony(trimps_7d)
    weekly_trimp = sum(trimps_7d)
    strain = calculate_strain(weekly_trimp, monotony.value)

    return TrainingQualityResponse(
        intensity_distribution=IntensityDistributionResponse(
            low_percent=intensity.low_percent,
            medium_percent=intensity.medium_percent,
            high_percent=intensity.high_percent,
            is_polarized=intensity.is_polarized,
            total_minutes=intensity.total_minutes,
        ),
        monotony=monotony.value,
        monotony_level=monotony.level,
        strain=strain.value,
        strain_level=strain.level,
    )


# ---------------------------------------------------------------------------
# Today Dashboard Aggregat (#676)
# ---------------------------------------------------------------------------


def _greeting() -> str:
    """Tageszeit-abhängige Begrüßung."""
    hour = datetime.now().hour
    if hour < 11:
        return "Guten Morgen"
    if hour < 17:
        return "Guten Tag"
    return "Guten Abend"


def _build_last_session(
    sessions: list[WorkoutModel],
) -> LastSessionSummary | None:
    """Letzte absolvierte Session mit Vergleichs-Einordnung."""
    if not sessions:
        return None

    last = sessions[-1]
    training_type = last.training_type_override or last.training_type_auto

    # Vergleich: Durchschnittspace für gleichen Trainingstyp
    comparison = _compare_to_average(last, sessions, training_type)

    exercise_count = None
    tonnage_kg = None
    session_rpe: float | None = float(last.rpe) if last.rpe else None

    if last.workout_type == "strength" and last.exercises_json:
        try:
            data = json.loads(last.exercises_json)
            if isinstance(data, list):
                exercise_count = len(data)
            elif isinstance(data, dict):
                exercises = data.get("exercises", [])
                exercise_count = len(exercises)
                tonnage_kg = data.get("tonnage_kg")
                if not session_rpe:
                    session_rpe = data.get("rpe")
        except (json.JSONDecodeError, TypeError):
            pass

    session_date = last.date.date() if hasattr(last.date, "date") else last.date

    return LastSessionSummary(
        id=last.id,
        date=session_date.isoformat(),
        workout_type=last.workout_type,
        training_type=training_type,
        distance_km=last.distance_km,
        duration_seconds=last.duration_sec,
        avg_pace_formatted=last.pace,
        avg_heartrate=float(last.hr_avg) if last.hr_avg else None,
        exercise_count=exercise_count,
        tonnage_kg=tonnage_kg,
        rpe=session_rpe,
        trimp_score=last.trimp_score,
        comparison_message=comparison,
    )


def _compare_to_average(
    session: WorkoutModel,
    all_sessions: list[WorkoutModel],
    training_type: str | None,
) -> str:
    """Vergleiche Session mit Durchschnitt gleichen Typs."""
    if session.workout_type != "running" or not session.pace:
        return ""

    pace_sec = _parse_pace(session.pace)
    if not pace_sec:
        return ""

    # Durchschnitt berechnen für gleichen Trainingstyp
    same_type_paces: list[float] = []
    for s in all_sessions:
        if s.id == session.id:
            continue
        s_type = s.training_type_override or s.training_type_auto
        if s_type == training_type and s.pace:
            p = _parse_pace(s.pace)
            if p:
                same_type_paces.append(p)

    if len(same_type_paces) < 3:
        return ""

    avg_pace = sum(same_type_paces) / len(same_type_paces)
    diff = avg_pace - pace_sec  # Positiv = schneller als Schnitt

    if abs(diff) < 3:
        return "Im Bereich deines Durchschnitts"
    if diff > 0:
        return f"{diff:.0f}s/km schneller als dein Durchschnitt"
    return f"{abs(diff):.0f}s/km langsamer als dein Durchschnitt"


def _parse_pace(pace_str: str | None) -> float | None:
    if not pace_str:
        return None
    try:
        parts = pace_str.replace(",", ".").split(":")
        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])
    except (ValueError, IndexError):
        pass
    return None


def _build_week_progress(sessions: list[WorkoutModel]) -> WeekProgressResponse:
    """Wochenfortschritt: Sessions und km dieser Woche."""
    today = date.today()
    # Montag dieser Woche
    monday = today - timedelta(days=today.weekday())
    day_names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    completed_by_day: dict[date, bool] = {}
    total_km = 0.0
    total_sec = 0
    count = 0

    for s in sessions:
        d = s.date.date() if hasattr(s.date, "date") else s.date
        if monday <= d <= today:
            completed_by_day[d] = True
            total_km += s.distance_km or 0
            total_sec += s.duration_sec or 0
            count += 1

    days: list[DayStatus] = []
    for i in range(7):
        d = monday + timedelta(days=i)
        has_completed = d in completed_by_day
        is_future = d > today
        status = "rest"
        if has_completed:
            status = "completed"
        elif not is_future:
            status = "rest"  # Vergangenheit ohne Session
        # geplante Sessions würden aus dem Wochenplan kommen (Phase 3)

        days.append(
            DayStatus(
                date=d.isoformat(),
                day_name=day_names[i],
                has_planned=False,  # Wird in Phase 3 ergänzt
                has_completed=has_completed,
                status=status,
            )
        )

    return WeekProgressResponse(
        sessions_completed=count,
        sessions_planned=0,  # Phase 3
        distance_completed_km=round(total_km, 1),
        distance_planned_km=None,  # Phase 3
        time_completed_seconds=total_sec,
        time_planned_seconds=None,  # Phase 3
        days=days,
    )


@router.get("/today", response_model=TodayResponse)
async def get_today(
    db: AsyncSession = Depends(get_db),
) -> TodayResponse:
    """Aggregierte Daten für das Heute-Dashboard."""
    athlete = await _get_athlete(db)
    sessions = await _get_all_sessions(db)

    resting_hr = (athlete.resting_hr or 60) if athlete else 60
    max_hr = (athlete.max_hr or 190) if athlete else 190
    personal_max_ctl = athlete.personal_max_ctl if athlete else None

    # Fitness-Score
    score_result = compute_full_score(sessions, personal_max_ctl)

    if athlete and score_result["new_max_ctl"] != personal_max_ctl:
        athlete.personal_max_ctl = score_result["new_max_ctl"]
        await db.commit()

    # Trainingsqualität
    intensity = calculate_intensity_distribution(sessions, resting_hr, max_hr)
    trimps_7d = get_last_7_days_trimps(sessions)
    monotony = calculate_monotony(trimps_7d)

    form = FormIndicator(**score_result["form"])
    acwr_data = score_result["acwr"]
    acwr = ACWRResult(**acwr_data) if acwr_data else None

    # Insights (max 2 für Dashboard)
    ctx = InsightContext(
        acwr=acwr,
        form=form,
        trend=score_result["trend"],
        intensity=intensity,
        monotony=monotony,
        sessions=sessions,
    )
    insights = generate_insights(ctx, max_insights=2)

    return TodayResponse(
        greeting=_greeting(),
        fitness_score=FitnessScoreResponse(
            score=score_result["score"],
            endurance_score=score_result["endurance_score"],
            strength_score=score_result["strength_score"],
            trend=score_result["trend"],
            trend_label=score_result["trend_label"],
            form=score_result["form"],
            acwr=score_result["acwr"],
            context_message=score_result["context_message"],
            updated_at=datetime.utcnow().isoformat(),
        ),
        last_session=_build_last_session(sessions),
        week_progress=_build_week_progress(sessions),
        insights=[
            InsightResponse(
                type=i.type,
                priority=i.priority,
                title=i.title,
                message=i.message,
                category=i.category,
                icon=i.icon,
            )
            for i in insights
        ],
    )
