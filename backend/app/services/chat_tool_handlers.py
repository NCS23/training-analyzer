"""Chat Tool Handlers — DB-Queries fuer die 11 KI-Chat-Tools.

Jeder Handler bekommt die Tool-Argumente und eine DB-Session,
fuehrt die Abfrage durch und gibt ein JSON-serialisierbares Dict zurueck.
"""

import json
import logging
from datetime import date, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    AIRecommendationModel,
    ChatConversationModel,
    ChatMessageModel,
    ExerciseModel,
    PlanChangeLogModel,
    PlannedSessionModel,
    TrainingPhaseModel,
    TrainingPlanModel,
    WeeklyPlanDayModel,
    WeeklyReviewModel,
    WorkoutModel,
)

logger = logging.getLogger(__name__)

PERIOD_MAP = {
    "1w": timedelta(weeks=1),
    "2w": timedelta(weeks=2),
    "4w": timedelta(weeks=4),
    "3m": timedelta(days=90),
    "6m": timedelta(days=180),
    "1y": timedelta(days=365),
}


async def dispatch_tool(name: str, args: dict, db: AsyncSession) -> dict:
    """Ruft den passenden Tool-Handler auf."""
    handlers = {
        "get_session_details": handle_get_session_details,
        "search_sessions": handle_search_sessions,
        "get_training_stats": handle_get_training_stats,
        "get_plan_details": handle_get_plan_details,
        "get_plan_compliance": handle_get_plan_compliance,
        "get_personal_records": handle_get_personal_records,
        "get_exercises": handle_get_exercises,
        "get_ai_recommendations": handle_get_ai_recommendations,
        "get_weekly_review": handle_get_weekly_review,
        "search_conversations": handle_search_conversations,
        "get_plan_change_log": handle_get_plan_change_log,
    }
    handler = handlers.get(name)
    if not handler:
        return {"error": f"Unbekanntes Tool: {name}"}
    try:
        return await handler(args, db)
    except Exception as e:
        logger.exception("Tool-Handler %s fehlgeschlagen", name)
        return {"error": f"Fehler bei {name}: {str(e)}"}


async def handle_get_session_details(args: dict, db: AsyncSession) -> dict:
    """Laedt vollstaendige Session-Details."""
    session_id = args["session_id"]
    result = await db.execute(select(WorkoutModel).where(WorkoutModel.id == session_id))
    w = result.scalar_one_or_none()
    if not w:
        return {"error": f"Session {session_id} nicht gefunden"}

    w_date = w.date.date() if isinstance(w.date, datetime) else w.date
    data: dict = {
        "id": w.id,
        "date": str(w_date),
        "workout_type": str(w.workout_type),
        "training_type": str(w.training_type_override or w.training_type_auto or ""),
        "duration_min": round(w.duration_sec / 60) if w.duration_sec else None,
        "distance_km": w.distance_km,
        "pace": str(w.pace) if w.pace else None,
        "hr_avg": w.hr_avg,
        "hr_max": w.hr_max,
        "hr_min": w.hr_min,
        "cadence_avg": w.cadence_avg,
        "rpe": w.rpe,
        "notes": w.notes,
    }

    data["laps"] = _parse_json(w.laps_json)
    data["hr_zones"] = _parse_json(w.hr_zones_json)
    data["weather"] = _parse_json(w.weather_json)
    data["air_quality"] = _parse_json(w.air_quality_json)
    data["surface"] = _parse_json(w.surface_json)
    data["location"] = w.location_name
    data["exercises"] = _parse_json(w.exercises_json)

    # Hoehenmeter aus GPS-Track
    gps = _parse_json(w.gps_track_json)
    if isinstance(gps, dict):
        data["elevation"] = {
            "ascent_m": gps.get("total_ascent_m"),
            "descent_m": gps.get("total_descent_m"),
        }

    # KI-Analyse (gecached)
    data["ai_analysis"] = _parse_json(w.ai_analysis)

    # Soll/Ist: geplante Session
    if w.planned_entry_id:
        data["planned_session"] = await _load_planned_session(w.planned_entry_id, db)

    return data


async def handle_search_sessions(args: dict, db: AsyncSession) -> dict:
    """Sucht Sessions mit Filtern."""
    query = select(WorkoutModel)

    if args.get("workout_type"):
        query = query.where(WorkoutModel.workout_type == args["workout_type"])
    if args.get("training_type"):
        tt = args["training_type"]
        query = query.where(
            or_(WorkoutModel.training_type_override == tt, WorkoutModel.training_type_auto == tt)
        )
    if args.get("date_from"):
        query = query.where(WorkoutModel.date >= datetime.fromisoformat(args["date_from"]))
    if args.get("date_to"):
        dt_to = datetime.fromisoformat(args["date_to"])
        query = query.where(WorkoutModel.date <= dt_to.replace(hour=23, minute=59, second=59))
    if args.get("min_distance_km"):
        query = query.where(WorkoutModel.distance_km >= args["min_distance_km"])
    if args.get("max_distance_km"):
        query = query.where(WorkoutModel.distance_km <= args["max_distance_km"])

    sort_col = _get_sort_column(args.get("sort_by", "date"))
    query = query.order_by(sort_col.desc() if args.get("sort_order") != "asc" else sort_col.asc())

    limit = min(args.get("limit", 10), 50)
    query = query.limit(limit)

    result = await db.execute(query)
    sessions = []
    for w in result.scalars().all():
        w_date = w.date.date() if isinstance(w.date, datetime) else w.date
        sessions.append(
            {
                "id": w.id,
                "date": str(w_date),
                "workout_type": str(w.workout_type),
                "training_type": str(w.training_type_override or w.training_type_auto or ""),
                "duration_min": round(w.duration_sec / 60) if w.duration_sec else None,
                "distance_km": w.distance_km,
                "pace": str(w.pace) if w.pace else None,
                "hr_avg": w.hr_avg,
                "rpe": w.rpe,
            }
        )

    return {"sessions": sessions, "count": len(sessions)}


async def handle_get_training_stats(args: dict, db: AsyncSession) -> dict:
    """Aggregierte Trainingsstatistiken."""
    today = date.today()
    delta = PERIOD_MAP.get(args["period"], timedelta(weeks=4))
    start = datetime.combine(today - delta, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())

    stats = await _compute_period_stats(start, end, db)

    result: dict = {"period": args["period"], "from": str(start.date()), "to": str(today), **stats}

    # Vergleich mit vorherigem Zeitraum
    if args.get("compare_previous", True):
        prev_end = start
        prev_start = datetime.combine(start.date() - delta, datetime.min.time())
        prev_stats = await _compute_period_stats(prev_start, prev_end, db)
        result["previous_period"] = {
            "from": str(prev_start.date()),
            "to": str(prev_end.date()),
            **prev_stats,
        }

    return result


async def handle_get_plan_details(args: dict, db: AsyncSession) -> dict:
    """Laedt aktiven Trainingsplan mit Phasen und Wochenstruktur."""
    today = date.today()
    plan_result = await db.execute(
        select(TrainingPlanModel)
        .where(
            TrainingPlanModel.status == "active",
            TrainingPlanModel.start_date <= today,
            TrainingPlanModel.end_date >= today,
        )
        .limit(1)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        return {"error": "Kein aktiver Trainingsplan gefunden"}

    # Phasen laden
    phases_result = await db.execute(
        select(TrainingPhaseModel)
        .where(TrainingPhaseModel.training_plan_id == plan.id)
        .order_by(TrainingPhaseModel.start_week)
    )
    phases = [
        {
            "name": p.name,
            "phase_type": str(p.phase_type),
            "start_week": p.start_week,
            "end_week": p.end_week,
            "focus": _parse_json(p.focus_json),
            "target_metrics": _parse_json(p.target_metrics_json),
            "notes": p.notes,
        }
        for p in phases_result.scalars().all()
    ]

    # Geplante Sessions fuer die angefragte Woche
    week_offset = args.get("week_offset", 0)
    target_week = today + timedelta(weeks=week_offset)
    week_start = target_week - timedelta(days=target_week.weekday())
    week_sessions = await _load_week_planned_sessions(plan.id, week_start, db)

    return {
        "plan_name": plan.name,
        "description": plan.description,
        "start_date": str(plan.start_date),
        "end_date": str(plan.end_date),
        "current_week": max(1, (today - plan.start_date).days // 7 + 1),
        "total_weeks": (plan.end_date - plan.start_date).days // 7 + 1,
        "phases": phases,
        "week_sessions": week_sessions,
        "week_start": str(week_start),
    }


async def handle_get_plan_compliance(args: dict, db: AsyncSession) -> dict:
    """Soll/Ist-Vergleich fuer eine Woche."""
    today = date.today()
    week_offset = args.get("week_offset", 0)
    target_date = today + timedelta(weeks=week_offset)
    week_start = target_date - timedelta(days=target_date.weekday())
    week_end = week_start + timedelta(days=6)

    # Geplante Sessions
    plan_result = await db.execute(
        select(TrainingPlanModel)
        .where(
            TrainingPlanModel.status == "active",
            TrainingPlanModel.start_date <= today,
            TrainingPlanModel.end_date >= today,
        )
        .limit(1)
    )
    plan = plan_result.scalar_one_or_none()
    planned = await _load_week_planned_sessions(plan.id, week_start, db) if plan else []

    # Tatsaechliche Sessions
    actual_result = await db.execute(
        select(WorkoutModel)
        .where(
            WorkoutModel.date >= datetime.combine(week_start, datetime.min.time()),
            WorkoutModel.date <= datetime.combine(week_end, datetime.max.time()),
        )
        .order_by(WorkoutModel.date)
    )
    actual = []
    for w in actual_result.scalars().all():
        w_date = w.date.date() if isinstance(w.date, datetime) else w.date
        actual.append(
            {
                "id": w.id,
                "date": str(w_date),
                "workout_type": str(w.workout_type),
                "training_type": str(w.training_type_override or w.training_type_auto or ""),
                "duration_min": round(w.duration_sec / 60) if w.duration_sec else None,
                "distance_km": w.distance_km,
                "pace": str(w.pace) if w.pace else None,
                "planned_entry_id": w.planned_entry_id,
            }
        )

    planned_count = len([p for p in planned if p.get("type") != "Ruhetag"])
    actual_count = len(actual)
    compliance = round(actual_count / planned_count * 100) if planned_count > 0 else 0

    return {
        "week_start": str(week_start),
        "week_end": str(week_end),
        "planned_sessions": planned,
        "actual_sessions": actual,
        "planned_count": planned_count,
        "actual_count": actual_count,
        "compliance_pct": min(compliance, 100),
    }


async def handle_get_personal_records(_args: dict, db: AsyncSession) -> dict:
    """Persoenliche Bestleistungen."""
    # Schnellste Pace (nur Laeufe mit Pace-Wert)
    pace_result = await db.execute(
        select(WorkoutModel)
        .where(WorkoutModel.workout_type == "running", WorkoutModel.pace.is_not(None))
        .order_by(WorkoutModel.pace.asc())
        .limit(5)
    )
    fastest = [
        {
            "id": w.id,
            "date": str(w.date.date() if isinstance(w.date, datetime) else w.date),
            "pace": str(w.pace),
            "distance_km": w.distance_km,
            "training_type": str(w.training_type_override or w.training_type_auto or ""),
        }
        for w in pace_result.scalars().all()
    ]

    # Laengster Lauf
    dist_result = await db.execute(
        select(WorkoutModel)
        .where(WorkoutModel.workout_type == "running", WorkoutModel.distance_km.is_not(None))
        .order_by(WorkoutModel.distance_km.desc())
        .limit(3)
    )
    longest = [
        {
            "id": w.id,
            "date": str(w.date.date() if isinstance(w.date, datetime) else w.date),
            "distance_km": w.distance_km,
            "duration_min": round(w.duration_sec / 60) if w.duration_sec else None,
        }
        for w in dist_result.scalars().all()
    ]

    # Hoechstes Wochenvolumen
    weekly_vol = await db.execute(
        select(
            func.date_trunc("week", WorkoutModel.date).label("week"),
            func.sum(WorkoutModel.distance_km).label("total_km"),
            func.count(WorkoutModel.id).label("sessions"),
        )
        .where(WorkoutModel.workout_type == "running")
        .group_by("week")
        .order_by(func.sum(WorkoutModel.distance_km).desc())
        .limit(3)
    )
    best_weeks = [
        {
            "week": str(row.week.date() if row.week else ""),
            "total_km": round(row.total_km, 1),
            "sessions": row.sessions,
        }
        for row in weekly_vol.all()
    ]

    return {
        "fastest_pace": fastest,
        "longest_runs": longest,
        "best_weekly_volume": best_weeks,
    }


async def handle_get_exercises(args: dict, db: AsyncSession) -> dict:
    """Durchsucht die Uebungsdatenbank."""
    query = select(ExerciseModel)

    if args.get("category"):
        query = query.where(ExerciseModel.category == args["category"])
    if args.get("equipment"):
        query = query.where(ExerciseModel.equipment == args["equipment"])
    if args.get("level"):
        query = query.where(ExerciseModel.level == args["level"])
    if args.get("muscle_group"):
        query = query.where(ExerciseModel.primary_muscles_json.contains(args["muscle_group"]))
    if args.get("search"):
        query = query.where(ExerciseModel.name.ilike(f"%{args['search']}%"))

    limit = min(args.get("limit", 20), 50)
    query = query.order_by(ExerciseModel.usage_count.desc()).limit(limit)

    result = await db.execute(query)
    exercises = [
        {
            "id": e.id,
            "name": e.name,
            "category": e.category,
            "equipment": e.equipment,
            "level": e.level,
            "primary_muscles": _parse_json(e.primary_muscles_json),
            "instructions": _parse_json(e.instructions_json),
            "usage_count": e.usage_count,
        }
        for e in result.scalars().all()
    ]

    return {"exercises": exercises, "count": len(exercises)}


async def handle_get_ai_recommendations(args: dict, db: AsyncSession) -> dict:
    """Laedt KI-Empfehlungen."""
    query = select(AIRecommendationModel)

    period = args.get("period", "4w")
    delta = PERIOD_MAP.get(period, timedelta(weeks=4))
    start = datetime.combine(date.today() - delta, datetime.min.time())
    query = query.where(AIRecommendationModel.created_at >= start)

    if args.get("status"):
        query = query.where(AIRecommendationModel.status == args["status"])

    query = query.order_by(AIRecommendationModel.created_at.desc()).limit(30)

    result = await db.execute(query)
    recs = [
        {
            "id": r.id,
            "session_id": r.session_id,
            "type": str(r.type),
            "title": r.title,
            "reasoning": r.reasoning,
            "priority": r.priority,
            "status": r.status,
            "current_value": r.current_value,
            "suggested_value": r.suggested_value,
            "created_at": str(r.created_at),
        }
        for r in result.scalars().all()
    ]

    return {"recommendations": recs, "count": len(recs)}


async def handle_get_weekly_review(args: dict, db: AsyncSession) -> dict:
    """Laedt den Wochenrueckblick."""
    today = date.today()
    week_offset = args.get("week_offset", -1)
    target_date = today + timedelta(weeks=week_offset)
    week_start = target_date - timedelta(days=target_date.weekday())

    result = await db.execute(
        select(WeeklyReviewModel).where(WeeklyReviewModel.week_start == week_start)
    )
    review = result.scalar_one_or_none()
    if not review:
        return {"error": f"Kein Wochenrueckblick fuer KW ab {week_start} vorhanden"}

    return {
        "week_start": str(review.week_start),
        "summary": review.summary,
        "overall_rating": review.overall_rating,
        "fatigue_assessment": review.fatigue_assessment,
        "session_count": review.session_count,
        "volume_comparison": _parse_json(review.volume_comparison_json),
        "highlights": _parse_json(review.highlights_json),
        "improvements": _parse_json(review.improvements_json),
        "next_week_recommendations": _parse_json(review.next_week_recommendations_json),
    }


async def handle_search_conversations(args: dict, db: AsyncSession) -> dict:
    """Durchsucht fruehere Chat-Konversationen."""
    query_text = args["query"]
    limit = min(args.get("limit", 5), 20)

    result = await db.execute(
        select(ChatMessageModel, ChatConversationModel.title)
        .join(ChatConversationModel, ChatMessageModel.conversation_id == ChatConversationModel.id)
        .where(ChatMessageModel.content.ilike(f"%{query_text}%"))
        .order_by(ChatMessageModel.created_at.desc())
        .limit(limit)
    )
    matches = [
        {
            "conversation_title": row.title,
            "conversation_id": row.ChatMessageModel.conversation_id,
            "role": row.ChatMessageModel.role,
            "content_excerpt": row.ChatMessageModel.content[:300],
            "created_at": str(row.ChatMessageModel.created_at),
        }
        for row in result.all()
    ]

    return {"matches": matches, "count": len(matches)}


async def handle_get_plan_change_log(args: dict, db: AsyncSession) -> dict:
    """Laedt Planaenderungshistorie."""
    period = args.get("period", "4w")
    delta = PERIOD_MAP.get(period, timedelta(weeks=4))
    start = datetime.combine(date.today() - delta, datetime.min.time())
    limit = min(args.get("limit", 20), 50)

    result = await db.execute(
        select(PlanChangeLogModel)
        .where(PlanChangeLogModel.created_at >= start)
        .order_by(PlanChangeLogModel.created_at.desc())
        .limit(limit)
    )
    changes = [
        {
            "id": c.id,
            "change_type": c.change_type,
            "category": c.category,
            "summary": c.summary,
            "reason": c.reason,
            "details": _parse_json(c.details_json),
            "created_by": c.created_by,
            "created_at": str(c.created_at),
        }
        for c in result.scalars().all()
    ]

    return {"changes": changes, "count": len(changes)}


# --- Helpers ---


def _parse_json(raw: str | None) -> dict | list | None:
    """Parst JSON-String, gibt None bei Fehler zurueck."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


def _get_sort_column(sort_by: str):
    """Gibt die SQLAlchemy-Spalte fuer die Sortierung zurueck."""
    mapping = {
        "date": WorkoutModel.date,
        "distance": WorkoutModel.distance_km,
        "duration": WorkoutModel.duration_sec,
        "pace": WorkoutModel.pace,
    }
    return mapping.get(sort_by, WorkoutModel.date)


async def _compute_period_stats(start: datetime, end: datetime, db: AsyncSession) -> dict:
    """Berechnet aggregierte Stats fuer einen Zeitraum."""
    result = await db.execute(
        select(
            func.count(WorkoutModel.id).label("total_sessions"),
            func.sum(WorkoutModel.distance_km).label("total_km"),
            func.sum(WorkoutModel.duration_sec).label("total_sec"),
            func.avg(WorkoutModel.hr_avg).label("avg_hr"),
            func.avg(WorkoutModel.cadence_avg).label("avg_cadence"),
        ).where(WorkoutModel.date >= start, WorkoutModel.date <= end)
    )
    row = result.one()

    # Typ-Verteilung
    type_result = await db.execute(
        select(
            func.coalesce(
                WorkoutModel.training_type_override, WorkoutModel.training_type_auto, "unknown"
            ).label("tt"),
            func.count(WorkoutModel.id).label("cnt"),
        )
        .where(
            WorkoutModel.date >= start,
            WorkoutModel.date <= end,
            WorkoutModel.workout_type == "running",
        )
        .group_by("tt")
    )
    type_dist = {str(r.tt): r.cnt for r in type_result.all()}

    total_km = round(row.total_km, 1) if row.total_km else 0
    total_sec = row.total_sec or 0

    return {
        "total_sessions": row.total_sessions or 0,
        "total_km": total_km,
        "total_duration_min": round(total_sec / 60) if total_sec else 0,
        "avg_hr": round(row.avg_hr) if row.avg_hr else None,
        "avg_cadence": round(row.avg_cadence) if row.avg_cadence else None,
        "type_distribution": type_dist,
    }


async def _load_planned_session(planned_id: int, db: AsyncSession) -> dict | None:
    """Laedt eine geplante Session fuer Soll/Ist."""
    result = await db.execute(
        select(PlannedSessionModel).where(PlannedSessionModel.id == planned_id)
    )
    ps = result.scalar_one_or_none()
    if not ps:
        return None

    data: dict = {
        "training_type": str(ps.training_type),
        "notes": str(ps.notes) if ps.notes else None,
    }
    if ps.run_details_json:
        rd = _parse_json(ps.run_details_json)
        if rd:
            data["run_details"] = rd
    if ps.exercises_json:
        ex = _parse_json(ps.exercises_json)
        if ex:
            data["exercises"] = ex
    return data


async def _load_week_planned_sessions(
    plan_id: int, week_start: date, db: AsyncSession
) -> list[dict]:
    """Laedt geplante Sessions fuer eine Woche."""
    day_result = await db.execute(
        select(WeeklyPlanDayModel)
        .where(
            WeeklyPlanDayModel.plan_id == plan_id,
            WeeklyPlanDayModel.week_start == week_start,
        )
        .order_by(WeeklyPlanDayModel.day_of_week)
    )
    days = day_result.scalars().all()

    sessions: list[dict] = []
    for day in days:
        actual_date = day.week_start + timedelta(days=day.day_of_week)
        if day.is_rest_day:
            sessions.append({"date": str(actual_date), "type": "Ruhetag"})
            continue

        ps_result = await db.execute(
            select(PlannedSessionModel)
            .where(
                PlannedSessionModel.day_id == day.id,
                PlannedSessionModel.status == "active",
            )
            .order_by(PlannedSessionModel.position)
        )
        for ps in ps_result.scalars().all():
            entry: dict = {
                "date": str(actual_date),
                "training_type": str(ps.training_type),
                "notes": str(ps.notes) if ps.notes else None,
            }
            if ps.run_details_json:
                rd = _parse_json(ps.run_details_json)
                if rd:
                    entry["run_details"] = rd
            if ps.exercises_json:
                ex = _parse_json(ps.exercises_json)
                if ex:
                    entry["exercises"] = ex
            sessions.append(entry)

    return sessions
