"""Vollstaendiger Export fuer die minsaga-Migration (#823/#825, Format-Version 3).

Sammelt serverseitig ALLES, was fuer nahtloses Weitertrainieren in der
minsaga-iOS-App noetig ist: Profilwerte + Schwellentests, Ziele, Plaene
mit Phasen-Templates UND Changelog (Entscheidungen samt Begruendung),
saemtliche gespeicherten Wochenplan-Wochen inklusive aller Anpassungen
(run_details, Status, edited-Flag) — und seit v3 die Trainings-Historie.

Zur Historie (#825): v2 schloss Workouts bewusst aus, weil Apple Health
als Import-Master galt. Das war ein Irrtum — Apple Health enthaelt nur
die junge Apple-Watch-Aera, die Garmin-Jahre liegen ausschliesslich hier.
Ohne sie rechnet minsaga Trainingslast, Langlauf-Basis und Pace-Spezifitaet
systematisch falsch. Der `sessions`-Block liefert deshalb Kerndaten plus
Laps je Workout; GPS-Tracks und Zeitreihen bleiben aussen vor.
"""

import json
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_active_user
from app.infrastructure.database.models import (
    AthleteModel,
    PlanChangeLogModel,
    PlannedSessionModel,
    RaceGoalModel,
    ThresholdTestModel,
    TrainingPhaseModel,
    TrainingPlanModel,
    UserModel,
    WeeklyPlanDayModel,
    WorkoutModel,
)
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/export", tags=["export"])


def _parse_json(raw: str | None) -> object:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def _iso(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


async def _athlete_block(db: AsyncSession, user_id: int) -> dict[str, object]:
    athlete_result = await db.execute(select(AthleteModel).where(AthleteModel.user_id == user_id))
    athlete = athlete_result.scalars().first()

    latest_test_result = await db.execute(
        select(ThresholdTestModel)
        .where(ThresholdTestModel.user_id == user_id)
        .order_by(ThresholdTestModel.test_date.desc())
        .limit(1)
    )
    latest_test = latest_test_result.scalars().first()

    return {
        "resting_hr": athlete.resting_hr if athlete else None,
        "max_hr": athlete.max_hr if athlete else None,
        "lthr": latest_test.lthr if latest_test else None,
        "threshold_pace_sec_per_km": latest_test.avg_pace_sec if latest_test else None,
    }


async def _threshold_tests_block(db: AsyncSession, user_id: int) -> list[dict[str, object]]:
    result = await db.execute(
        select(ThresholdTestModel)
        .where(ThresholdTestModel.user_id == user_id)
        .order_by(ThresholdTestModel.test_date)
    )
    return [
        {
            "test_date": _iso(test.test_date),
            "lthr": test.lthr,
            "max_hr_measured": test.max_hr_measured,
            "avg_pace_sec": test.avg_pace_sec,
        }
        for test in result.scalars().all()
    ]


async def _goals_block(db: AsyncSession, user_id: int) -> list[dict[str, object]]:
    result = await db.execute(
        select(RaceGoalModel)
        .where(RaceGoalModel.user_id == user_id)
        .order_by(RaceGoalModel.race_date)
    )
    return [
        {
            "title": goal.title,
            "race_date": _iso(goal.race_date),
            "distance_km": goal.distance_km,
            "target_time_seconds": goal.target_time_seconds,
            "is_active": goal.is_active,
        }
        for goal in result.scalars().all()
    ]


async def _changelog_block(db: AsyncSession, plan_id: int) -> list[dict[str, object]]:
    result = await db.execute(
        select(PlanChangeLogModel)
        .where(PlanChangeLogModel.plan_id == plan_id)
        .order_by(PlanChangeLogModel.created_at)
    )
    return [
        {
            "change_type": entry.change_type,
            "category": entry.category,
            "summary": entry.summary,
            "details": _parse_json(entry.details_json),
            "reason": entry.reason,
            "created_by": entry.created_by,
            "created_at": _iso(entry.created_at),
        }
        for entry in result.scalars().all()
    ]


async def _plans_block(db: AsyncSession, user_id: int) -> list[dict[str, object]]:
    plans_result = await db.execute(
        select(TrainingPlanModel)
        .where(TrainingPlanModel.user_id == user_id)
        .order_by(TrainingPlanModel.start_date)
    )
    plans: list[dict[str, object]] = []
    for plan in plans_result.scalars().all():
        goal_title = None
        if plan.goal_id:
            goal_result = await db.execute(
                select(RaceGoalModel.title).where(RaceGoalModel.id == plan.goal_id)
            )
            goal_title = goal_result.scalar_one_or_none()

        phases_result = await db.execute(
            select(TrainingPhaseModel)
            .where(TrainingPhaseModel.training_plan_id == plan.id)
            .order_by(TrainingPhaseModel.start_week)
        )
        phases = [
            {
                "name": phase.name,
                "phase_type": phase.phase_type,
                "start_week": phase.start_week,
                "end_week": phase.end_week,
                "notes": phase.notes,
                "weekly_template": _parse_json(phase.weekly_template_json) or {"days": []},
                "weekly_templates": _parse_json(phase.weekly_templates_json),
            }
            for phase in phases_result.scalars().all()
        ]

        plans.append(
            {
                "id": plan.id,
                "name": plan.name,
                "description": plan.description,
                "status": plan.status,
                "start_date": _iso(plan.start_date),
                "end_date": _iso(plan.end_date),
                "target_event_date": _iso(plan.target_event_date),
                "goal_title": goal_title,
                "phases": phases,
                "changelog": await _changelog_block(db, plan.id),
            }
        )
    return plans


async def _weekly_plans_block(
    db: AsyncSession, user_id: int, plan_names: dict[int, str]
) -> list[dict[str, object]]:
    days_result = await db.execute(
        select(WeeklyPlanDayModel)
        .where(WeeklyPlanDayModel.user_id == user_id)
        .order_by(WeeklyPlanDayModel.week_start, WeeklyPlanDayModel.day_of_week)
    )
    days = list(days_result.scalars().all())
    if not days:
        return []

    sessions_result = await db.execute(
        select(PlannedSessionModel)
        .where(PlannedSessionModel.day_id.in_([day.id for day in days]))
        .order_by(PlannedSessionModel.day_id, PlannedSessionModel.position)
    )
    sessions_by_day: dict[int, list[PlannedSessionModel]] = {}
    for session in sessions_result.scalars().all():
        sessions_by_day.setdefault(int(session.day_id), []).append(session)

    weeks: dict[str, dict[str, object]] = {}
    for day in days:
        week_key = _iso(day.week_start) or ""
        week = weeks.setdefault(week_key, {"week_start": week_key, "days": []})
        day_sessions = [
            {
                "position": session.position,
                "training_type": session.training_type,
                "run_details": _parse_json(session.run_details_json),
                "notes": session.notes,
                "status": session.status,
            }
            for session in sessions_by_day.get(day.id, [])
        ]
        assert isinstance(week["days"], list)
        week["days"].append(
            {
                "day_of_week": day.day_of_week,
                "is_rest_day": day.is_rest_day,
                "edited": day.edited,
                "notes": day.notes,
                "plan_name": plan_names.get(day.plan_id) if day.plan_id else None,
                "sessions": day_sessions,
            }
        )
    return list(weeks.values())


def _lap_eintrag(lap: object) -> dict[str, object] | None:
    if not isinstance(lap, dict):
        return None
    return {
        "lap_number": lap.get("lap_number"),
        "duration_seconds": lap.get("duration_seconds"),
        "distance_km": lap.get("distance_km"),
        "avg_pace_min_per_km": lap.get("avg_pace_min_per_km"),
        "avg_hr_bpm": lap.get("avg_hr_bpm"),
        # Nutzer-Korrektur schlaegt die Klassifikation.
        "type": lap.get("user_override") or lap.get("suggested_type"),
    }


async def _sessions_block(db: AsyncSession, user_id: int) -> list[dict[str, object]]:
    """Trainings-Historie (#825): Kerndaten + Laps, keine Zeitreihen."""
    result = await db.execute(
        select(WorkoutModel).where(WorkoutModel.user_id == user_id).order_by(WorkoutModel.date)
    )
    sessions: list[dict[str, object]] = []
    for workout in result.scalars().all():
        laps_raw = _parse_json(workout.laps_json)
        laps = (
            [eintrag for lap in laps_raw if (eintrag := _lap_eintrag(lap)) is not None]
            if isinstance(laps_raw, list)
            else []
        )
        sessions.append(
            {
                "id": workout.id,
                "date": _iso(workout.date),
                "workout_type": workout.workout_type,
                "subtype": workout.subtype,
                "duration_sec": workout.duration_sec,
                "distance_km": workout.distance_km,
                "hr_avg": workout.hr_avg,
                "hr_max": workout.hr_max,
                "cadence_avg": workout.cadence_avg,
                "rpe": workout.rpe,
                "notes": workout.notes,
                "laps": laps,
            }
        )
    return sessions


@router.get("/minsaga")
async def export_minsaga(
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
) -> dict[str, object]:
    """Kompletter minsaga-Export (Format-Version 3)."""
    user_id = int(current_user.id)

    plans = await _plans_block(db, user_id)
    plan_names = {
        int(plan["id"]): str(plan["name"]) for plan in plans if isinstance(plan["id"], int)
    }
    # Interne Plan-IDs gehoeren nicht in den Export — nur zum Aufloesen benutzt.
    for plan in plans:
        plan.pop("id", None)

    return {
        "version": 3,
        "exported_at": datetime.utcnow().isoformat(),
        "athlete": await _athlete_block(db, user_id),
        "threshold_tests": await _threshold_tests_block(db, user_id),
        "goals": await _goals_block(db, user_id),
        "plans": plans,
        "weekly_plans": await _weekly_plans_block(db, user_id, plan_names),
        "sessions": await _sessions_block(db, user_id),
    }
