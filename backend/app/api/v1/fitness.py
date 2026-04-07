"""Fitness-Score API — Endpunkte für Score, Form, ACWR, History, Insights, Today.

Basiert auf dem Banister Fitness-Fatigue-Modell (#675, #676).
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    AthleteModel,
    PlannedSessionModel,
    RaceGoalModel,
    UserModel,
    WeeklyPlanDayModel,
    WorkoutModel,
)
from app.infrastructure.database.session import get_db
from app.models.fitness import (
    DayStatus,
    FitnessHistoryResponse,
    FitnessScoreResponse,
    GoalSummary,
    InsightResponse,
    InsightsListResponse,
    IntensityDistributionResponse,
    LastSessionSummary,
    NextSessionInfo,
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
    sessions = await _get_all_sessions(db)
    result = compute_full_score(sessions)

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
    sessions = await _get_all_sessions(db)
    history = compute_history(sessions, days)

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
    score_result = compute_full_score(sessions)
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


def _greeting(name: str | None = None) -> str:
    """Tageszeit-abhängige, persönliche Begrüßung."""
    hour = datetime.now().hour
    if hour < 11:
        base = "Guten Morgen"
    elif hour < 17:
        base = "Guten Tag"
    else:
        base = "Guten Abend"
    if name:
        return f"{base}, {name}!"
    return base


def _compute_streak(sessions: list[WorkoutModel]) -> int:
    """Berechne aktuelle Trainings-Streak (aufeinanderfolgende Tage)."""
    if not sessions:
        return 0
    today = date.today()
    training_dates: set[date] = set()
    for s in sessions:
        d = s.date.date() if hasattr(s.date, "date") else s.date
        training_dates.add(d)

    streak = 0
    check = today
    if check not in training_dates:
        check = today - timedelta(days=1)
    while check in training_dates:
        streak += 1
        check -= timedelta(days=1)
    return streak


def _build_motivation(
    streak: int,
    trend: str,
    form_status: str,
    last_session_days_ago: int | None,
) -> str | None:
    """Generiere einen kurzen, emotionalen Motivations-Satz."""
    if streak >= 5:
        return f"{streak}-Tage-Streak — herausragend!"
    if streak >= 3:
        return f"{streak}-Tage-Streak — weiter so!"
    if form_status == "fresh":
        return "Perfekt erholt — bereit für ein gutes Training"
    if trend == "rising":
        return "Deine Fitness entwickelt sich super!"
    if last_session_days_ago is not None and last_session_days_ago >= 3:
        return "Zeit für eine Einheit? Dein Körper ist bereit"
    return None


async def _build_next_session(
    db: AsyncSession,
) -> NextSessionInfo | None:
    """Finde die nächste geplante Session aus dem Wochenplan."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    day_names = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]

    # Tage dieser Woche ab heute laden
    result = await db.execute(
        select(WeeklyPlanDayModel)
        .where(
            WeeklyPlanDayModel.week_start == monday,
            WeeklyPlanDayModel.day_of_week >= today.weekday(),
            WeeklyPlanDayModel.is_rest_day.is_(False),
        )
        .order_by(WeeklyPlanDayModel.day_of_week)
    )
    plan_days = list(result.scalars().all())

    for plan_day in plan_days:
        # Geplante Sessions für diesen Tag
        sessions_result = await db.execute(
            select(PlannedSessionModel)
            .where(
                PlannedSessionModel.day_id == plan_day.id,
                PlannedSessionModel.status == "active",
            )
            .limit(1)
        )
        planned = sessions_result.scalar_one_or_none()
        if not planned:
            continue

        target_date = monday + timedelta(days=plan_day.day_of_week)
        if target_date == today:
            day_label = "Heute"
        elif target_date == today + timedelta(days=1):
            day_label = "Morgen"
        else:
            day_label = day_names[plan_day.day_of_week]

        description = _describe_planned_session(planned)
        return NextSessionInfo(
            day_name=day_label,
            workout_type=planned.training_type,
            description=description,
        )
    return None


def _describe_planned_session(planned: PlannedSessionModel) -> str:
    """Generiere kurze Beschreibung einer geplanten Session."""
    if planned.training_type == "strength":
        return "Krafttraining"
    if planned.run_details_json:
        try:
            details = json.loads(planned.run_details_json)
            training_type = details.get("training_type", "")
            type_labels = {
                "easy": "Lockerer Lauf",
                "long_run": "Langer Lauf",
                "intervals": "Intervall-Training",
                "tempo": "Tempo-Lauf",
                "threshold": "Schwellenlauf",
                "fartlek": "Fahrtspiel",
                "repetitions": "Wiederholungsläufe",
                "progression": "Steigerungslauf",
                "recovery": "Regenerationslauf",
            }
            return type_labels.get(training_type, "Lauf")
        except (json.JSONDecodeError, TypeError):
            pass
    return "Lauf"


async def _build_goal_summary(db: AsyncSession) -> GoalSummary | None:
    """Lade aktives Wettkampf-Ziel."""
    result = await db.execute(
        select(RaceGoalModel)
        .where(RaceGoalModel.is_active.is_(True))
        .order_by(RaceGoalModel.race_date.asc())
        .limit(1)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        return None

    race_date = goal.race_date.date() if hasattr(goal.race_date, "date") else goal.race_date
    days_until = (race_date - date.today()).days
    if days_until < 0:
        return None

    target_formatted = None
    if goal.target_time_seconds:
        h = goal.target_time_seconds // 3600
        m = (goal.target_time_seconds % 3600) // 60
        target_formatted = f"{h}:{m:02d}" if h > 0 else f"{m} min"

    return GoalSummary(
        title=goal.title,
        days_until=days_until,
        target_time_formatted=target_formatted,
    )


async def _get_user(db: AsyncSession) -> UserModel | None:
    """Lade ersten User (Single-User-Mode)."""
    result = await db.execute(select(UserModel).limit(1))
    return result.scalar_one_or_none()


def _build_last_session(
    sessions: list[WorkoutModel],
) -> LastSessionSummary | None:
    """Letzte absolvierte Session mit Vergleichs-Einordnung.

    Gibt None zurück wenn keine Session innerhalb der letzten 14 Tage liegt.
    """
    if not sessions:
        return None

    last = sessions[-1]

    # Nur Sessions der letzten 14 Tage anzeigen
    session_date = last.date.date() if hasattr(last.date, "date") else last.date
    if (date.today() - session_date).days > 14:
        return None
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


async def _build_week_progress(
    sessions: list[WorkoutModel],
    db: AsyncSession,
) -> WeekProgressResponse:
    """Wochenfortschritt: geplante und absolvierte Sessions dieser Woche."""
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    day_names = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

    # Absolvierte Sessions
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

    # Geplante Sessions aus Wochenplan
    planned_by_dow: set[int] = set()
    plan_count = 0
    plan_result = await db.execute(
        select(WeeklyPlanDayModel).where(
            WeeklyPlanDayModel.week_start == monday,
            WeeklyPlanDayModel.is_rest_day.is_(False),
        )
    )
    plan_days = list(plan_result.scalars().all())

    for plan_day in plan_days:
        sessions_result = await db.execute(
            select(PlannedSessionModel.id)
            .where(
                PlannedSessionModel.day_id == plan_day.id,
                PlannedSessionModel.status == "active",
            )
            .limit(1)
        )
        if sessions_result.scalar_one_or_none() is not None:
            planned_by_dow.add(plan_day.day_of_week)
            plan_count += 1

    days: list[DayStatus] = []
    for i in range(7):
        d = monday + timedelta(days=i)
        has_completed = d in completed_by_day
        has_planned = i in planned_by_dow
        is_future = d > today

        if has_completed:
            status = "completed"
        elif has_planned and is_future:
            status = "planned"
        elif has_planned and not is_future:
            status = "skipped"
        else:
            status = "rest"

        days.append(
            DayStatus(
                date=d.isoformat(),
                day_name=day_names[i],
                has_planned=has_planned,
                has_completed=has_completed,
                status=status,
            )
        )

    return WeekProgressResponse(
        sessions_completed=count,
        sessions_planned=plan_count,
        distance_completed_km=round(total_km, 1),
        distance_planned_km=None,
        time_completed_seconds=total_sec,
        time_planned_seconds=None,
        days=days,
    )


@router.get("/today", response_model=TodayResponse)
async def get_today(
    db: AsyncSession = Depends(get_db),
) -> TodayResponse:
    """Aggregierte Daten für das Heute-Dashboard."""
    athlete = await _get_athlete(db)
    user = await _get_user(db)
    sessions = await _get_all_sessions(db)

    resting_hr = (athlete.resting_hr or 60) if athlete else 60
    max_hr = (athlete.max_hr or 190) if athlete else 190

    # Fitness-Score
    score_result = compute_full_score(sessions)

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

    # Persönliche Daten
    streak = _compute_streak(sessions)
    last_session = _build_last_session(sessions)

    # Letzte Session: wie viele Tage her?
    last_session_days_ago: int | None = None
    if sessions:
        last_date = sessions[-1].date
        d = last_date.date() if hasattr(last_date, "date") else last_date
        last_session_days_ago = (date.today() - d).days

    motivation = _build_motivation(
        streak=streak,
        trend=score_result["trend"],
        form_status=form.status,
        last_session_days_ago=last_session_days_ago,
    )

    return TodayResponse(
        greeting=_greeting(user.name if user else None),
        motivation=motivation,
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
        last_session=last_session,
        week_progress=await _build_week_progress(sessions, db),
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
        next_session=await _build_next_session(db),
        goal_summary=await _build_goal_summary(db),
    )
