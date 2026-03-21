"""Chat Tool Handlers — DB-Queries fuer die KI-Chat-Tools.

Jeder Handler bekommt die Tool-Argumente und eine DB-Session,
fuehrt die Abfrage durch und gibt ein JSON-serialisierbares Dict zurueck.
"""

import json
import logging
from datetime import date, datetime, timedelta

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    AIRecommendationModel,
    AthleteModel,
    ChatConversationModel,
    ChatMessageModel,
    ExerciseModel,
    PlanChangeLogModel,
    PlannedSessionModel,
    RaceGoalModel,
    TrainingPhaseModel,
    TrainingPlanModel,
    WeeklyPlanDayModel,
    WeeklyReviewModel,
    WorkoutModel,
)
from app.services.session_analysis_service import (
    _athlete_to_dict,
    _goal_to_dict,
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
        "propose_plan_change": handle_propose_plan_change,
        "generate_training_plan": handle_generate_training_plan,
        "search_training_knowledge": handle_search_training_knowledge,
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
    """Aggregierte Trainingsstatistiken + Athletenprofil."""
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

    # Athletenprofil anhaengen
    athlete_result = await db.execute(select(AthleteModel).limit(1))
    athlete = athlete_result.scalar_one_or_none()
    if athlete:
        result["athlete"] = _athlete_to_dict(athlete)

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

    # Aktive Wettkampfziele
    goal_result = await db.execute(
        select(RaceGoalModel)
        .where(RaceGoalModel.is_active.is_(True))
        .order_by(RaceGoalModel.race_date.asc())
    )
    goals = [_goal_to_dict(g) for g in goal_result.scalars().all()]

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
        "race_goals": goals,
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


async def handle_propose_plan_change(args: dict, db: AsyncSession) -> dict:
    """Formatiert einen Plan-Vorschlag als strukturierten Block.

    Ermittelt die betroffene Woche aus dem Datum und lädt den aktuellen
    Wochenplan, damit das Frontend die Änderung direkt anwenden kann.
    """
    target_date = args.get("date")
    week_start_str = None

    if target_date:
        try:
            d = datetime.strptime(target_date, "%Y-%m-%d").date()
            week_start = d - timedelta(days=d.weekday())
            week_start_str = str(week_start)
        except ValueError:
            pass

    # Plan-ID ermitteln für Changelog
    plan_id = await _get_active_plan_id(db)

    return {
        "rendered": True,
        "block": (
            "```plan-change\n"
            + json.dumps(
                {
                    "action": args.get("action", "replace"),
                    "day": args.get("day", ""),
                    "date": args.get("date"),
                    "week_start": week_start_str,
                    "plan_id": plan_id,
                    "description": args.get("description", ""),
                    "reason": args.get("reason", ""),
                    "from": args.get("from_value"),
                    "to": args.get("to_value"),
                },
                ensure_ascii=False,
            )
            + "\n```"
        ),
        "instruction": (
            "Fuege den obigen ```plan-change``` Block UNMODIFIZIERT in deine Antwort ein. "
            "Das Frontend rendert ihn automatisch als interaktive Karte mit Uebernehmen-Button."
        ),
    }


async def handle_generate_training_plan(args: dict, db: AsyncSession) -> dict:
    """Erstellt einen echten Trainingsplan in der Datenbank."""
    goal_text = args.get("goal", "Trainingsplan")
    weeks = min(max(args.get("weeks", 12), 4), 24)
    sessions_per_week = min(max(args.get("sessions_per_week", 4), 3), 7)
    include_strength = args.get("include_strength", True)
    current_km = args.get("current_weekly_km", 20.0)
    race_date_str = args.get("race_date")

    today = date.today()
    start_date = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
    end_date = start_date + timedelta(weeks=weeks) - timedelta(days=1)

    race_date = _parse_date_safe(race_date_str)
    goal_id = await _create_race_goal(db, goal_text, race_date)

    rest_days = [0, 6]
    plan = await _create_plan_model(
        db,
        goal_text,
        goal_id,
        start_date,
        end_date,
        race_date,
        rest_days,
        today,
    )
    phases_created = await _create_plan_phases(
        db,
        plan.id,
        weeks,
        current_km,
        sessions_per_week,
        include_strength,
    )
    weeks_generated = await _generate_and_save_weekly_plans(
        db,
        plan.id,
        rest_days,
    )

    changelog = PlanChangeLogModel(
        plan_id=plan.id,
        change_type="plan_created",
        category="structure",
        summary=f"Plan '{goal_text}' mit {weeks} Wochen per KI-Chat erstellt",
        details_json=json.dumps(
            {
                "source": "ki_chat",
                "phases": phases_created,
                "weeks_generated": weeks_generated,
            }
        ),
    )
    db.add(changelog)
    await db.commit()

    plan_status = str(plan.status)
    plan_data = {
        "plan_id": plan.id,
        "plan_name": goal_text,
        "status": plan_status,
        "weeks": weeks,
        "weeks_generated": weeks_generated,
        "phases": phases_created,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "race_date": race_date_str,
    }

    plan_block = f"```plan-created\n{json.dumps(plan_data)}\n```"

    draft_hint = (
        " Der Plan wurde als Entwurf erstellt, da bereits ein aktiver Plan existiert. "
        "Weise den User darauf hin, dass er den Plan unter Plandetails aktivieren kann."
        if plan_status == "draft"
        else ""
    )

    return {
        **plan_data,
        "instruction": (
            f"Der Plan wurde erfolgreich erstellt (Status: {plan_status}).{draft_hint} "
            "Fasse den Plan kurz zusammen (Wochen, Phasen, Zeitraum). "
            "Bette dann GENAU diesen Block in deine Antwort ein, damit "
            "der User direkt zum Plan navigieren kann:\n\n"
            f"{plan_block}"
        ),
    }


def _parse_date_safe(date_str: str | None) -> date | None:
    """Parst ein Datum sicher, gibt None bei Fehler zurück."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


async def _create_race_goal(
    db: AsyncSession,
    goal_text: str,
    race_date: date | None,
) -> int | None:
    """Erstellt ein Wettkampfziel wenn ein Datum vorhanden ist."""
    if not race_date:
        return None
    goal_model = RaceGoalModel(
        title=goal_text,
        race_date=race_date,
        distance_km=_parse_goal_distance(goal_text),
        target_time_seconds=_parse_goal_time(goal_text),
        is_active=True,
    )
    db.add(goal_model)
    await db.flush()
    return goal_model.id


async def _create_plan_model(
    db: AsyncSession,
    goal_text: str,
    goal_id: int | None,
    start_date: date,
    end_date: date,
    race_date: date | None,
    rest_days: list[int],
    today: date,
) -> TrainingPlanModel:
    """Erstellt das TrainingPlan-Modell in der DB.

    Abgelaufene aktive Pläne werden auf "completed" gesetzt.
    Status wird nur auf "active" gesetzt wenn kein anderer aktiver Plan existiert,
    sonst "draft".
    """
    # Abgelaufene aktive Pläne automatisch auf "completed" setzen
    from sqlalchemy import update

    await db.execute(
        update(TrainingPlanModel)
        .where(
            TrainingPlanModel.status == "active",
            TrainingPlanModel.end_date < today,
        )
        .values(status="completed")
    )

    active_count = await db.execute(
        select(func.count(TrainingPlanModel.id)).where(TrainingPlanModel.status == "active")
    )
    has_active = (active_count.scalar() or 0) > 0
    status = "draft" if has_active else "active"

    plan = TrainingPlanModel(
        name=goal_text,
        description=f"Generiert per KI-Chat am {today.strftime('%d.%m.%Y')}",
        goal_id=goal_id,
        start_date=start_date,
        end_date=end_date,
        target_event_date=race_date,
        weekly_structure_json=json.dumps({"rest_days": rest_days}),
        status=status,
    )
    db.add(plan)
    await db.flush()
    return plan


async def _create_plan_phases(
    db: AsyncSession,
    plan_id: int,
    weeks: int,
    current_km: float,
    sessions_per_week: int,
    include_strength: bool,
) -> list[dict]:
    """Erstellt die Trainingsphasen für den Plan."""
    base_w = max(2, round(weeks * 0.4))
    build_w = max(2, round(weeks * 0.3))
    peak_w = max(1, round(weeks * 0.15))

    phase_defs = [
        ("Grundlagen", "base", 1, base_w, current_km * 1.1, sessions_per_week, 2),
        ("Aufbau", "build", base_w + 1, base_w + build_w, current_km * 1.3, sessions_per_week, 1),
        (
            "Spitze",
            "peak",
            base_w + build_w + 1,
            base_w + build_w + peak_w,
            current_km * 1.4,
            sessions_per_week,
            1,
        ),
        (
            "Tapering",
            "taper",
            base_w + build_w + peak_w + 1,
            weeks,
            current_km * 0.6,
            max(3, sessions_per_week - 1),
            0,
        ),
    ]

    phases_created = []
    for name, ptype, sw, ew, vol, sess, strength in phase_defs:
        strength_count = strength if include_strength else 0
        phase = TrainingPhaseModel(
            training_plan_id=plan_id,
            name=name,
            phase_type=ptype,
            start_week=sw,
            end_week=ew,
            focus_json=json.dumps({"primary": [name], "secondary": []}),
            target_metrics_json=json.dumps(
                {
                    "weekly_volume_min": round(vol * 0.9, 1),
                    "weekly_volume_max": round(vol * 1.1, 1),
                    "quality_sessions_per_week": min(2, sess - 1),
                    "strength_sessions_per_week": strength_count,
                }
            ),
        )
        db.add(phase)
        await db.flush()
        phases_created.append(
            {
                "name": name,
                "type": ptype,
                "weeks": f"KW {sw}–{ew}",
                "volume_km": round(vol, 1),
                "sessions": sess,
                "strength": strength_count,
            }
        )
    return phases_created


async def _generate_and_save_weekly_plans(
    db: AsyncSession,
    plan_id: int,
    rest_days: list[int],
) -> int:
    """Generiert Wochenpläne und speichert sie in der DB."""
    from app.services.plan_generator import generate_weekly_plans

    plan = await db.get(TrainingPlanModel, plan_id)
    if not plan:
        return 0

    phases_result = await db.execute(
        select(TrainingPhaseModel)
        .where(TrainingPhaseModel.training_plan_id == plan_id)
        .order_by(TrainingPhaseModel.start_week)
    )
    db_phases = list(phases_result.scalars().all())

    # Wettkampfziel für Pace-Berechnung
    goal = None
    if plan.goal_id:
        goal = await db.get(RaceGoalModel, plan.goal_id)

    weekly_data = generate_weekly_plans(
        plan=plan,
        phases=db_phases,
        rest_days=rest_days,
        goal=goal,
    )

    # Alte Wochenplandaten löschen die im selben Zeitraum liegen
    # (UniqueConstraint auf week_start + day_of_week)
    await _remove_overlapping_weekly_plans(db, weekly_data)

    weeks_generated = 0
    for week_start_date, entries in weekly_data:
        for entry in entries:
            day = WeeklyPlanDayModel(
                plan_id=plan_id,
                week_start=week_start_date,
                day_of_week=entry.day_of_week,
                is_rest_day=entry.is_rest_day,
                notes=entry.notes,
            )
            db.add(day)
            await db.flush()
            for sess in entry.sessions:
                ps = PlannedSessionModel(
                    day_id=day.id,
                    position=sess.position,
                    training_type=sess.training_type,
                    template_id=sess.template_id,
                    run_details_json=(
                        json.dumps(sess.run_details.model_dump()) if sess.run_details else None
                    ),
                    notes=sess.notes,
                )
                db.add(ps)
        weeks_generated += 1
    return weeks_generated


async def _remove_overlapping_weekly_plans(
    db: AsyncSession,
    weekly_data: list[tuple[date, list]],
) -> None:
    """Löscht bestehende Wochenplandaten die mit dem neuen Plan kollidieren."""
    week_starts = [ws for ws, _ in weekly_data]
    if not week_starts:
        return

    # IDs der betroffenen Tage finden
    day_ids_result = await db.execute(
        select(WeeklyPlanDayModel.id).where(WeeklyPlanDayModel.week_start.in_(week_starts))
    )
    day_ids = list(day_ids_result.scalars().all())

    if day_ids:
        # Erst geplante Sessions löschen, dann die Tage
        await db.execute(delete(PlannedSessionModel).where(PlannedSessionModel.day_id.in_(day_ids)))
        await db.execute(
            delete(WeeklyPlanDayModel).where(WeeklyPlanDayModel.week_start.in_(week_starts))
        )
        await db.flush()


async def _get_active_plan_id(db: AsyncSession) -> int | None:
    """Gibt die ID des aktiven Trainingsplans zurück."""
    today = date.today()
    result = await db.execute(
        select(TrainingPlanModel.id)
        .where(
            TrainingPlanModel.status == "active",
            TrainingPlanModel.start_date <= today,
            TrainingPlanModel.end_date >= today,
        )
        .limit(1)
    )
    return result.scalar_one_or_none()


def _parse_goal_distance(goal_text: str) -> float:
    """Extrahiert die Wettkampfdistanz aus dem Zieltext."""
    text = goal_text.lower()
    if "marathon" in text and "halb" not in text and "half" not in text:
        return 42.195
    if "halb" in text or "half" in text or "hm" in text:
        return 21.0975
    if "10k" in text or "10 km" in text:
        return 10.0
    if "5k" in text or "5 km" in text:
        return 5.0
    return 21.0975  # Default: Halbmarathon


def _parse_goal_time(goal_text: str) -> int:
    """Extrahiert die Zielzeit in Sekunden aus dem Zieltext."""
    import re

    text = goal_text.lower()
    # "sub-2h", "unter 2 stunden", "sub 1:45"
    match = re.search(r"sub[- ]?(\d+)[:\.]?(\d{2})?(?:h|$|\s)", text)
    if match:
        hours = int(match.group(1))
        mins = int(match.group(2)) if match.group(2) else 0
        return hours * 3600 + mins * 60

    match = re.search(r"(\d+):(\d{2}):(\d{2})", text)
    if match:
        return int(match.group(1)) * 3600 + int(match.group(2)) * 60 + int(match.group(3))

    match = re.search(r"(\d+):(\d{2})", text)
    if match:
        h_or_m = int(match.group(1))
        rest = int(match.group(2))
        if h_or_m <= 6:
            return h_or_m * 3600 + rest * 60
        return h_or_m * 60 + rest

    # Default: ~2h für HM
    return 7200


async def handle_search_training_knowledge(args: dict, _db: AsyncSession) -> dict:
    """Durchsucht die Trainingswissen-Datenbank."""
    from app.services.training_knowledge import search_knowledge

    results = search_knowledge(
        query=args["query"],
        category=args.get("category"),
        limit=3,
    )

    if not results:
        return {"results": [], "message": "Kein passendes Trainingswissen gefunden."}

    return {"results": results, "count": len(results)}
