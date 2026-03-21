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
    """Erstellt einen echten Trainingsplan in der Datenbank.

    Die KI liefert phase_templates mit der Trainingsstruktur pro Phase.
    Der Algorithmus berechnet daraus Volumen und Pace-Zonen.
    """
    goal_text = args.get("goal", "Trainingsplan")
    weeks = min(max(args.get("weeks", 12), 4), 52)
    sessions_per_week = min(max(args.get("sessions_per_week", 4), 3), 7)
    include_strength = args.get("include_strength", True)
    current_km = args.get("current_weekly_km", 20.0)
    race_date_str = args.get("race_date")
    start_date_str = args.get("start_date")
    ki_phase_templates = args.get("phase_templates", [])

    today = date.today()
    start_date = _resolve_start_date(start_date_str, today)
    race_date = _parse_date_safe(race_date_str)

    # Wenn race_date und start_date gegeben: Wochen aus der Differenz berechnen
    if race_date and start_date < race_date:
        weeks = max(4, (race_date - start_date).days // 7 + 1)

    end_date = start_date + timedelta(weeks=weeks) - timedelta(days=1)
    goal_id = await _create_race_goal(db, goal_text, race_date)

    rest_days = _extract_rest_days(ki_phase_templates)
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
        distance_km=_parse_goal_distance(goal_text),
        ki_phase_templates=ki_phase_templates,
    )
    weeks_generated = await _generate_and_save_weekly_plans(
        db,
        plan.id,
        rest_days,
    )

    # Fehlende Übungen automatisch anlegen
    exercises_created = await _ensure_exercises_exist(db, plan.id)
    if exercises_created:
        logger.info("%d Übungen automatisch angelegt für Plan %d", exercises_created, plan.id)

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
                "exercises_created": exercises_created,
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


def _resolve_start_date(start_date_str: str | None, today: date) -> date:
    """Berechnet das Startdatum — auf nächsten Montag aufgerundet.

    Wenn kein Startdatum angegeben wird, wird der nächste Montag verwendet.
    """
    if start_date_str:
        parsed = _parse_date_safe(start_date_str)
        if parsed and parsed > today:
            # Auf nächsten Montag aufrunden
            days_to_monday = (7 - parsed.weekday()) % 7
            return parsed + timedelta(days=days_to_monday) if days_to_monday else parsed
    # Default: nächster Montag
    days_to_next_monday = (7 - today.weekday()) % 7 or 7
    return today + timedelta(days=days_to_next_monday)


def _extract_rest_days(ki_phase_templates: list[dict]) -> list[int]:
    """Ermittelt Ruhetage aus den KI-Templates (erster Phase als Referenz).

    Gibt [0, 6] (Mo+So) als Default zurück wenn keine Templates vorhanden.
    """
    if not ki_phase_templates:
        return [0, 6]
    first_tpl = ki_phase_templates[0]
    days = first_tpl.get("days", [])
    rest = [d["day_of_week"] for d in days if d.get("is_rest_day")]
    return rest if rest else [0, 6]


def _convert_ki_template(ki_template: dict | None) -> str | None:
    """Konvertiert ein KI-Phase-Template in weekly_template_json.

    Wandelt das KI-Format (phase_type + days mit sessions) in das
    PhaseWeeklyTemplate-Format um, das der plan_generator versteht.
    """
    if not ki_template:
        return None

    days = ki_template.get("days", [])
    if not days:
        return None

    template_days = []
    for day in days:
        dow = day.get("day_of_week", 0)
        is_rest = day.get("is_rest_day", False)
        sessions_data = []

        for i, sess in enumerate(day.get("sessions", [])):
            training_type = sess.get("training_type", "running")
            entry: dict = {
                "position": i + 1,
                "training_type": training_type,
            }

            run_type = sess.get("run_type")
            if run_type and training_type == "running":
                entry["run_type"] = run_type
                entry["run_details"] = {"run_type": run_type}

            notes = sess.get("notes")
            if notes:
                entry["notes"] = notes

            sessions_data.append(entry)

        template_days.append(
            {
                "day_of_week": dow,
                "is_rest_day": is_rest,
                "sessions": sessions_data,
            }
        )

    # Fehlende Tage als Ruhetage auffüllen
    existing = {d["day_of_week"] for d in template_days}
    for dow in range(7):
        if dow not in existing:
            template_days.append(
                {
                    "day_of_week": dow,
                    "is_rest_day": True,
                    "sessions": [],
                }
            )
    template_days.sort(key=lambda d: d["day_of_week"])

    return json.dumps({"days": template_days})


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


def _estimate_peak_volume(distance_km: float, current_km: float) -> float:
    """Schätzt das Peak-Wochenvolumen basierend auf Wettkampfdistanz.

    Faustregel: Peak-Volumen = ca. 2.5x Wettkampfdistanz (min. current + 30%).
    """
    target_by_distance = {
        42.195: 65.0,  # Marathon: 55-75 km/Woche Peak
        21.0975: 45.0,  # HM: 35-55 km/Woche Peak
        10.0: 35.0,  # 10k: 30-40 km/Woche Peak
        5.0: 30.0,  # 5k: 25-35 km/Woche Peak
    }
    # Nächste bekannte Distanz finden
    closest = min(target_by_distance.keys(), key=lambda d: abs(d - distance_km))
    target_peak = target_by_distance[closest]

    # Nicht unter dem aktuellen Volumen + 30% starten
    return max(target_peak, current_km * 1.3)


# Mapping: phase_type → (Name, Strength-Sessions, Quality-Sessions, Focus-Primary, Focus-Secondary)
_PHASE_META: dict[str, tuple[str, int, int, list[str], list[str]]] = {
    "recovery": (
        "Erholung",
        0,
        0,
        ["Regeneration", "Aktive Erholung"],
        ["Mobilität", "Verletzungsprävention"],
    ),
    "base": (
        "Grundlagen",
        2,
        0,
        ["Aerobe Grundlagenausdauer", "Lauftechnik"],
        ["Kraftaufbau", "Beweglichkeit", "Lauf-ABC"],
    ),
    "build": (
        "Aufbau",
        1,
        1,
        ["Tempohärte", "Laktatschwelle"],
        ["Wettkampfspezifik", "Kraftausdauer"],
    ),
    "peak": (
        "Spitze",
        1,
        2,
        ["Wettkampftempo", "VO2max"],
        ["Intervalltraining", "Schnellkraft"],
    ),
    "taper": (
        "Tapering",
        0,
        1,
        ["Frische", "Wettkampfvorbereitung"],
        ["Intensität erhalten", "Volumen reduzieren"],
    ),
    "transition": (
        "Übergang",
        1,
        0,
        ["Allgemeine Fitness", "Regeneration"],
        ["Koordination", "Ausgleichssport"],
    ),
}

# Volumen-Faktor relativ zum Peak-Volumen pro Phase-Typ
_VOLUME_FACTORS: dict[str, float] = {
    "recovery": 0.35,
    "base": 0.6,
    "build": 0.8,
    "peak": 1.0,
    "taper": 0.5,
    "transition": 0.4,
}


def _build_phase_defs(
    total_weeks: int,
    ki_phase_templates: list[dict] | None,
    peak_vol: float,
    current_km: float,
    sessions_per_week: int,
) -> list[dict]:
    """Baut die Phasen-Definition aus KI-Templates oder Default-Verteilung.

    Wenn KI-Templates Wochen-Angaben enthalten, werden diese verwendet.
    Sonst: 40% base, 30% build, 15% peak, Rest taper.
    """
    if ki_phase_templates and any(t.get("weeks") for t in ki_phase_templates):
        return _phases_from_ki_templates(
            ki_phase_templates,
            peak_vol,
            current_km,
            sessions_per_week,
        )

    return _phases_default_distribution(
        total_weeks,
        peak_vol,
        current_km,
        sessions_per_week,
    )


def _phases_from_ki_templates(
    templates: list[dict],
    peak_vol: float,
    current_km: float,
    sessions_per_week: int,
) -> list[dict]:
    """Erzeugt Phasen-Definitionen aus KI-Templates mit Wochen-Angaben."""
    defs = []
    current_week = 1
    for tpl in templates:
        ptype = tpl.get("phase_type", "base")
        w = tpl.get("weeks", 2)
        meta = _PHASE_META.get(ptype, ("Phase", 1, 0, ["Training"], []))
        vol_factor = _VOLUME_FACTORS.get(ptype, 0.6)
        vol = max(current_km * 0.5, peak_vol * vol_factor)

        sess = sessions_per_week
        if ptype == "taper":
            sess = max(3, sessions_per_week - 1)
        elif ptype == "recovery":
            sess = min(3, sessions_per_week)

        defs.append(
            {
                "name": meta[0],
                "type": ptype,
                "start_week": current_week,
                "end_week": current_week + w - 1,
                "volume": vol,
                "sessions": sess,
                "strength": meta[1],
                "quality": meta[2],
                "focus_primary": meta[3],
                "focus_secondary": meta[4] if len(meta) > 4 else [],
            }
        )
        current_week += w
    return defs


def _phases_default_distribution(
    total_weeks: int,
    peak_vol: float,
    current_km: float,
    sessions_per_week: int,
) -> list[dict]:
    """Fallback: Standard-Phasenverteilung (40/30/15/15)."""
    base_w = max(2, round(total_weeks * 0.4))
    build_w = max(2, round(total_weeks * 0.3))
    peak_w = max(1, round(total_weeks * 0.15))
    base_vol = max(current_km, peak_vol * 0.6)

    def _focus(ptype: str) -> tuple[list[str], list[str]]:
        meta = _PHASE_META.get(ptype)
        if meta and len(meta) > 3:
            return (meta[3], meta[4] if len(meta) > 4 else [])
        return (["Training"], [])

    return [
        {
            "name": "Grundlagen",
            "type": "base",
            "start_week": 1,
            "end_week": base_w,
            "volume": base_vol,
            "sessions": sessions_per_week,
            "strength": 2,
            "quality": 0,
            "focus_primary": _focus("base")[0],
            "focus_secondary": _focus("base")[1],
        },
        {
            "name": "Aufbau",
            "type": "build",
            "start_week": base_w + 1,
            "end_week": base_w + build_w,
            "volume": peak_vol * 0.8,
            "sessions": sessions_per_week,
            "strength": 1,
            "quality": 1,
            "focus_primary": _focus("build")[0],
            "focus_secondary": _focus("build")[1],
        },
        {
            "name": "Spitze",
            "type": "peak",
            "start_week": base_w + build_w + 1,
            "end_week": base_w + build_w + peak_w,
            "volume": peak_vol,
            "sessions": sessions_per_week,
            "strength": 1,
            "quality": 2,
            "focus_primary": _focus("peak")[0],
            "focus_secondary": _focus("peak")[1],
        },
        {
            "name": "Tapering",
            "type": "taper",
            "start_week": base_w + build_w + peak_w + 1,
            "end_week": total_weeks,
            "volume": peak_vol * 0.5,
            "sessions": max(3, sessions_per_week - 1),
            "strength": 0,
            "quality": 1,
            "focus_primary": _focus("taper")[0],
            "focus_secondary": _focus("taper")[1],
        },
    ]


async def _create_plan_phases(
    db: AsyncSession,
    plan_id: int,
    weeks: int,
    current_km: float,
    sessions_per_week: int,
    include_strength: bool,
    distance_km: float = 21.0975,
    ki_phase_templates: list[dict] | None = None,
) -> list[dict]:
    """Erstellt die Trainingsphasen für den Plan.

    Phasen-Aufteilung wird aus den KI-Templates abgeleitet (weeks pro Phase).
    Wenn keine KI-Templates vorhanden → Default-Verteilung (40/30/15/15).
    """
    peak_vol = _estimate_peak_volume(distance_km, current_km)
    phase_defs = _build_phase_defs(
        weeks,
        ki_phase_templates,
        peak_vol,
        current_km,
        sessions_per_week,
    )

    # KI-Templates nach phase_type indizieren
    ki_templates_by_type = {}
    for tpl in ki_phase_templates or []:
        ptype = tpl.get("phase_type")
        if ptype:
            ki_templates_by_type[ptype] = tpl

    phases_created = []
    for pdef in phase_defs:
        strength_count = pdef["strength"] if include_strength else 0
        template_json = _convert_ki_template(ki_templates_by_type.get(pdef["type"]))

        phase = TrainingPhaseModel(
            training_plan_id=plan_id,
            name=pdef["name"],
            phase_type=pdef["type"],
            start_week=pdef["start_week"],
            end_week=pdef["end_week"],
            focus_json=json.dumps(
                {
                    "primary": pdef.get("focus_primary", [pdef["name"]]),
                    "secondary": pdef.get("focus_secondary", []),
                }
            ),
            weekly_template_json=template_json,
            target_metrics_json=json.dumps(
                {
                    "weekly_volume_min": round(pdef["volume"] * 0.9, 1),
                    "weekly_volume_max": round(pdef["volume"] * 1.1, 1),
                    "quality_sessions_per_week": pdef["quality"],
                    "strength_sessions_per_week": strength_count,
                }
            ),
        )
        db.add(phase)
        await db.flush()
        phases_created.append(
            {
                "name": pdef["name"],
                "type": pdef["type"],
                "weeks": f"KW {pdef['start_week']}–{pdef['end_week']}",
                "volume_km": round(pdef["volume"], 1),
                "sessions": pdef["sessions"],
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
                exercises_json = None
                if sess.exercises:
                    exercises_json = json.dumps([e.model_dump() for e in sess.exercises])
                ps = PlannedSessionModel(
                    day_id=day.id,
                    position=sess.position,
                    training_type=sess.training_type,
                    template_id=sess.template_id,
                    run_details_json=(
                        json.dumps(sess.run_details.model_dump()) if sess.run_details else None
                    ),
                    exercises_json=exercises_json,
                    notes=sess.notes,
                )
                db.add(ps)
        weeks_generated += 1

    # Phasen-Templates aus den generierten Daten ableiten
    await _backfill_phase_templates(db, db_phases, weekly_data)

    return weeks_generated


async def _backfill_phase_templates(
    db: AsyncSession,
    phases: list[TrainingPhaseModel],
    weekly_data: list[tuple[date, list]],
) -> None:
    """Schreibt enriched per-week Templates in die Phasen zurück.

    Die generierten Wochenpläne enthalten angereicherte Segmente (Intervalle,
    Tempo, Pace-Zonen etc.). Diese werden als weekly_templates_json (pro Woche)
    UND als weekly_template_json (erste Woche als Shared-Template) gespeichert,
    damit die Planübersicht (/plan/programs/:id) die echten Trainingsdaten zeigt.
    """
    if not phases or not weekly_data:
        return

    for phase in phases:
        phase_weeks: dict[str, dict] = {}
        shared_template = None

        for week_num in range(phase.start_week, phase.end_week + 1):
            week_idx = week_num - 1
            if week_idx >= len(weekly_data):
                break

            _, entries = weekly_data[week_idx]
            week_template = _entries_to_template_dict(entries)
            phase_weeks[str(week_num - phase.start_week + 1)] = week_template
            if shared_template is None:
                shared_template = week_template

        if phase_weeks:
            phase.weekly_templates_json = json.dumps({"weeks": phase_weeks})
        if shared_template:
            phase.weekly_template_json = json.dumps(shared_template)

    await db.flush()


def _entries_to_template_dict(entries: list) -> dict:
    """Konvertiert generierte WeeklyPlanEntry-Liste in ein Template-Dict."""
    template_days = []
    for entry in sorted(entries, key=lambda e: e.day_of_week):
        sessions_data = []
        for s in entry.sessions:
            sess_entry: dict = {
                "position": s.position,
                "training_type": s.training_type,
            }
            if s.run_details:
                sess_entry["run_type"] = s.run_details.run_type
                sess_entry["run_details"] = s.run_details.model_dump()
            if s.notes:
                sess_entry["notes"] = s.notes
            if s.exercises:
                sess_entry["exercises"] = [e.model_dump() for e in s.exercises]
            sessions_data.append(sess_entry)

        template_days.append(
            {
                "day_of_week": entry.day_of_week,
                "is_rest_day": entry.is_rest_day,
                "sessions": sessions_data,
                **({"notes": entry.notes} if entry.notes else {}),
            }
        )

    # Fehlende Tage auffüllen (auf 7 Tage)
    existing_days = {d["day_of_week"] for d in template_days}
    for dow in range(7):
        if dow not in existing_days:
            template_days.append({"day_of_week": dow, "is_rest_day": True, "sessions": []})
    template_days.sort(key=lambda d: d["day_of_week"])

    return {"days": template_days}


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


def _collect_exercise_names_from_json(json_str: str | None, key: str) -> set[str]:
    """Extrahiert Übungsnamen aus einem JSON-String (segments oder exercises)."""
    if not json_str:
        return set()
    try:
        data = json.loads(json_str)
        items = data.get("segments", []) if key == "exercise_name" else data
        if not isinstance(items, list):
            return set()
        return {item[key] for item in items if item.get(key)}
    except (json.JSONDecodeError, TypeError):
        return set()


# Kategorie-Mapping für Kraft-Übungen aus plan_generator
_EXERCISE_CATEGORY_HINTS: dict[str, str] = {
    "Plank": "core",
    "Seitstütz": "core",
    "Hüftbrücke": "legs",
    "Ausfallschritt": "legs",
    "Step-Ups": "legs",
    "Wadenheben einbeinig": "legs",
    "Plank mit Arm heben": "core",
    "Einbeinige Kniebeuge": "legs",
    "Box Jumps": "legs",
    "Bergsteiger": "core",
}


async def _ensure_exercises_exist(db: AsyncSession, plan_id: int) -> int:
    """Stellt sicher, dass alle referenzierten Übungen in der DB existieren.

    Sammelt Übungsnamen aus Segmenten und Kraft-Sessions,
    legt fehlende automatisch mit Enrichment an.
    """
    from app.api.v1.exercise_library import _DRILL_ENRICHMENT, _apply_enrichment
    from app.services.exercise_enrichment import enrich_exercise_model

    sessions_result = await db.execute(
        select(PlannedSessionModel)
        .join(WeeklyPlanDayModel)
        .where(WeeklyPlanDayModel.plan_id == plan_id)
    )
    sessions = sessions_result.scalars().all()

    exercise_names: set[str] = set()
    for sess in sessions:
        exercise_names |= _collect_exercise_names_from_json(sess.run_details_json, "exercise_name")
        exercise_names |= _collect_exercise_names_from_json(sess.exercises_json, "name")

    if not exercise_names:
        return 0

    existing_result = await db.execute(
        select(ExerciseModel.name).where(ExerciseModel.name.in_(exercise_names))
    )
    existing_names = {str(n) for n in existing_result.scalars().all()}
    missing_names = exercise_names - existing_names

    if not missing_names:
        return 0

    created = 0
    for name in sorted(missing_names):
        category = _EXERCISE_CATEGORY_HINTS.get(name, "drills")
        model = ExerciseModel(name=name, category=category, is_custom=False, is_favorite=False)
        enrichment = _DRILL_ENRICHMENT.get(name) or enrich_exercise_model(name)
        if enrichment:
            _apply_enrichment(model, enrichment)
        db.add(model)
        created += 1
        logger.info("Übung auto-erstellt: %s (Kategorie: %s)", name, category)

    await db.flush()
    return created
