"""KI-Trainingsempfehlungen Service (E06-S02).

Generiert strukturierte Empfehlungen basierend auf der Session-Analyse
und dem Trainingsplan-Kontext. Nutzt die bereits gecachte Analyse aus
E06-S01 als Input.
"""

import json
import logging
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key_resolver import resolve_claude_api_key
from app.infrastructure.ai.ai_service import ai_service
from app.infrastructure.database.models import (
    AIRecommendationModel,
    PlannedSessionModel,
    RaceGoalModel,
    TrainingPhaseModel,
    TrainingPlanModel,
    WeeklyPlanDayModel,
    WorkoutModel,
)
from app.models.ai_recommendation import (
    RecommendationPriority,
    RecommendationResponse,
    RecommendationsListResponse,
    RecommendationStatus,
    RecommendationType,
)
from app.services.ai_log_service import AICallData, log_ai_call
from app.services.session_analysis_service import analyze_session

logger = logging.getLogger(__name__)

VALID_TYPES = {t.value for t in RecommendationType}
VALID_PRIORITIES = {p.value for p in RecommendationPriority}


@dataclass
class RecommendationContext:
    """Kontext fuer die Empfehlungsgenerierung."""

    analysis_summary: str
    intensity_rating: str
    fatigue_indicators: str | None
    plan_comparison: str | None
    analysis_recommendations: list[str]
    race_goal: dict | None
    current_phase: dict | None
    upcoming_sessions: list[dict]
    weekly_volume: dict
    recent_recommendations: list[dict]


async def generate_recommendations(
    session_id: int,
    db: AsyncSession,
    *,
    force_refresh: bool = False,
) -> RecommendationsListResponse:
    """Generiert KI-Empfehlungen fuer eine Session (Cache-First)."""
    workout = await _load_workout(session_id, db)

    # Cache: bestehende pending Empfehlungen zurueckgeben
    if not force_refresh:
        cached = await _load_cached_recommendations(session_id, db)
        if cached:
            return _build_response(cached, session_id, cached[0].provider, is_cached=True)

    # Session-Analyse sicherstellen (Voraussetzung)
    analysis = await _ensure_analysis(session_id, db)

    # Kontext laden
    context = await _load_recommendation_context(workout, analysis, db)

    # Prompt bauen und AI aufrufen
    prompt = _build_recommendation_prompt(context)
    system_prompt = _build_system_prompt(context)
    api_key = await resolve_claude_api_key(db)

    t0 = time.monotonic()
    raw = await ai_service.chat(prompt, {"system_prompt": system_prompt}, api_key)
    duration_ms = int((time.monotonic() - t0) * 1000)
    provider = ai_service.get_active_provider() or "unknown"

    # Parsen
    parsed = _parse_recommendations_json(raw)

    # Alte pending Empfehlungen loeschen, neue speichern
    await _delete_pending(session_id, db)
    models = await _save_recommendations(session_id, parsed, provider, db)

    # Log schreiben
    parsed_ok = len(parsed) > 0
    await log_ai_call(
        db,
        AICallData(
            use_case="recommendations",
            provider=provider,
            system_prompt=system_prompt,
            user_prompt=prompt,
            raw_response=raw,
            parsed_ok=parsed_ok,
            duration_ms=duration_ms,
            workout_id=session_id,
        ),
    )
    await db.commit()

    return _build_response(models, session_id, provider, is_cached=False)


async def get_recommendations(
    session_id: int,
    db: AsyncSession,
) -> RecommendationsListResponse:
    """Laedt gespeicherte Empfehlungen fuer eine Session."""
    models = await _load_all_recommendations(session_id, db)
    provider = models[0].provider if models else "none"
    return _build_response(models, session_id, provider, is_cached=True)


async def update_recommendation_status(
    recommendation_id: int,
    new_status: RecommendationStatus,
    db: AsyncSession,
) -> RecommendationResponse:
    """Aktualisiert den Status einer Empfehlung."""
    result = await db.execute(
        select(AIRecommendationModel).where(AIRecommendationModel.id == recommendation_id)
    )
    model = result.scalar_one_or_none()
    if not model:
        raise ValueError(f"Empfehlung {recommendation_id} nicht gefunden")

    model.status = new_status.value
    await db.commit()
    await db.refresh(model)
    return _model_to_response(model)


# ---------------------------------------------------------------------------
# Interne Hilfsfunktionen
# ---------------------------------------------------------------------------


async def _load_workout(session_id: int, db: AsyncSession) -> WorkoutModel:
    """Laedt Workout oder wirft ValueError."""
    result = await db.execute(select(WorkoutModel).where(WorkoutModel.id == session_id))
    workout = result.scalar_one_or_none()
    if not workout:
        raise ValueError(f"Session {session_id} nicht gefunden")
    return workout


async def _ensure_analysis(session_id: int, db: AsyncSession) -> dict:
    """Stellt sicher, dass eine Session-Analyse existiert."""
    result = await db.execute(select(WorkoutModel).where(WorkoutModel.id == session_id))
    workout = result.scalar_one_or_none()
    if not workout:
        raise ValueError(f"Session {session_id} nicht gefunden")

    if workout.ai_analysis:
        try:
            return json.loads(workout.ai_analysis)
        except json.JSONDecodeError:
            pass

    # Analyse noch nicht vorhanden — jetzt ausfuehren
    analysis_response = await analyze_session(session_id, db)
    return analysis_response.model_dump()


async def _load_cached_recommendations(
    session_id: int,
    db: AsyncSession,
) -> list[AIRecommendationModel]:
    """Laedt alle pending Empfehlungen fuer eine Session."""
    result = await db.execute(
        select(AIRecommendationModel)
        .where(
            AIRecommendationModel.session_id == session_id,
            AIRecommendationModel.status == "pending",
        )
        .order_by(AIRecommendationModel.priority.desc(), AIRecommendationModel.id)
    )
    return list(result.scalars().all())


async def _load_all_recommendations(
    session_id: int,
    db: AsyncSession,
) -> list[AIRecommendationModel]:
    """Laedt alle Empfehlungen fuer eine Session (alle Status)."""
    result = await db.execute(
        select(AIRecommendationModel)
        .where(AIRecommendationModel.session_id == session_id)
        .order_by(AIRecommendationModel.created_at.desc())
    )
    return list(result.scalars().all())


async def _delete_pending(session_id: int, db: AsyncSession) -> None:
    """Loescht alle pending Empfehlungen fuer eine Session."""
    await db.execute(
        delete(AIRecommendationModel).where(
            AIRecommendationModel.session_id == session_id,
            AIRecommendationModel.status == "pending",
        )
    )


async def _save_recommendations(
    session_id: int,
    parsed: list[dict],
    provider: str,
    db: AsyncSession,
) -> list[AIRecommendationModel]:
    """Speichert geparste Empfehlungen in der DB."""
    models = []
    for rec in parsed:
        model = AIRecommendationModel(
            session_id=session_id,
            type=rec["type"],
            title=rec["title"][:200],
            target_session_id=rec.get("target_session_id"),
            current_value=rec.get("current_value"),
            suggested_value=rec.get("suggested_value"),
            reasoning=rec["reasoning"],
            priority=rec["priority"],
            status="pending",
            provider=provider,
        )
        db.add(model)
        models.append(model)

    await db.flush()
    for m in models:
        await db.refresh(m)
    return models


async def _load_recommendation_context(
    workout: WorkoutModel,
    analysis: dict,
    db: AsyncSession,
) -> RecommendationContext:
    """Laedt den vollstaendigen Kontext fuer die Empfehlungsgenerierung."""
    workout_date = workout.date.date() if isinstance(workout.date, datetime) else workout.date

    # Aktives Wettkampfziel
    goal_result = await db.execute(
        select(RaceGoalModel).where(RaceGoalModel.is_active.is_(True)).limit(1)
    )
    goal_model = goal_result.scalar_one_or_none()
    race_goal = _goal_to_dict(goal_model) if goal_model else None

    # Aktuelle Trainingsphase
    current_phase = await _load_current_phase(workout_date, db)

    # Naechste 7 Tage geplante Sessions
    upcoming = await _load_upcoming_sessions(workout_date, db)

    # Wochenvolumen
    weekly_volume = await _load_weekly_volume(workout_date, db)

    # Letzte 10 Empfehlungen (Duplikat-Vermeidung)
    recent = await _load_recent_recommendations(db)

    return RecommendationContext(
        analysis_summary=analysis.get("summary", ""),
        intensity_rating=analysis.get("intensity_rating", "moderat"),
        fatigue_indicators=analysis.get("fatigue_indicators"),
        plan_comparison=analysis.get("plan_comparison"),
        analysis_recommendations=analysis.get("recommendations", []),
        race_goal=race_goal,
        current_phase=current_phase,
        upcoming_sessions=upcoming,
        weekly_volume=weekly_volume,
        recent_recommendations=recent,
    )


def _goal_to_dict(g: RaceGoalModel) -> dict:
    """RaceGoal in Dict."""
    target_pace = None
    if g.target_time_seconds and g.distance_km and g.distance_km > 0:
        pace_min = (g.target_time_seconds / 60) / g.distance_km
        m = int(pace_min)
        s = int((pace_min - m) * 60)
        target_pace = f"{m}:{s:02d}"

    return {
        "title": g.title,
        "date": str(g.race_date.date() if isinstance(g.race_date, datetime) else g.race_date),
        "distance_km": g.distance_km,
        "target_pace": target_pace,
    }


async def _load_current_phase(
    ref_date: object,
    db: AsyncSession,
) -> dict | None:
    """Laedt die aktuelle Trainingsphase basierend auf dem Datum."""
    # Aktiven Plan finden
    plan_result = await db.execute(
        select(TrainingPlanModel)
        .where(TrainingPlanModel.status == "active")
        .order_by(TrainingPlanModel.start_date.desc())
        .limit(1)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        return None

    # Aktuelle Woche im Plan berechnen
    days_since_start = (ref_date - plan.start_date).days  # type: ignore[operator]
    current_week = (days_since_start // 7) + 1

    # Phase finden
    phase_result = await db.execute(
        select(TrainingPhaseModel)
        .where(
            TrainingPhaseModel.training_plan_id == plan.id,
            TrainingPhaseModel.start_week <= current_week,
            TrainingPhaseModel.end_week >= current_week,
        )
        .limit(1)
    )
    phase = phase_result.scalar_one_or_none()
    if not phase:
        return {"plan_name": plan.name, "week": current_week}

    return {
        "plan_name": plan.name,
        "phase_name": phase.name,
        "phase_type": phase.phase_type,
        "week": current_week,
    }


async def _load_upcoming_sessions(
    ref_date: date,
    db: AsyncSession,
) -> list[dict]:
    """Laedt geplante Sessions der naechsten 7 Tage."""
    next_week = ref_date + timedelta(days=7)

    day_result = await db.execute(
        select(WeeklyPlanDayModel)
        .where(
            WeeklyPlanDayModel.week_start >= ref_date,
            WeeklyPlanDayModel.week_start <= next_week,
        )
        .order_by(WeeklyPlanDayModel.week_start, WeeklyPlanDayModel.day_of_week)
    )
    days = day_result.scalars().all()

    upcoming = []
    for day in days:
        session_date = day.week_start + timedelta(days=day.day_of_week)

        if day.is_rest_day:
            upcoming.append({"date": str(session_date), "type": "Ruhetag"})
            continue

        # Geplante Sessions fuer diesen Tag laden
        ps_result = await db.execute(
            select(PlannedSessionModel)
            .where(PlannedSessionModel.day_id == day.id)
            .order_by(PlannedSessionModel.position)
        )
        for ps in ps_result.scalars().all():
            entry: dict = {
                "date": str(session_date),
                "id": ps.id,
                "type": ps.training_type,
            }
            if ps.run_details_json:
                try:
                    rd = json.loads(str(ps.run_details_json))
                    entry["run_type"] = rd.get("run_type")
                    entry["target_duration_min"] = rd.get("target_duration_minutes")
                    entry["target_pace"] = rd.get("target_pace_min")
                except json.JSONDecodeError:
                    pass
            upcoming.append(entry)

    return upcoming[:10]


async def _load_weekly_volume(ref_date: date, db: AsyncSession) -> dict:
    """Berechnet das Wochenvolumen (aktuelle Woche)."""
    # Montag der aktuellen Woche
    weekday = ref_date.weekday()
    week_start = ref_date - timedelta(days=weekday)
    week_end = week_start + timedelta(days=6)

    result = await db.execute(
        select(WorkoutModel).where(
            WorkoutModel.date >= datetime.combine(week_start, datetime.min.time()),
            WorkoutModel.date <= datetime.combine(week_end, datetime.max.time()),
        )
    )
    workouts = result.scalars().all()

    total_km = sum(w.distance_km or 0 for w in workouts)
    total_min = sum((w.duration_sec or 0) / 60 for w in workouts)
    run_count = sum(1 for w in workouts if w.workout_type == "running")
    strength_count = sum(1 for w in workouts if w.workout_type == "strength")

    return {
        "total_km": round(total_km, 1),
        "total_hours": round(total_min / 60, 1),
        "session_count": len(workouts),
        "run_count": run_count,
        "strength_count": strength_count,
    }


async def _load_recent_recommendations(db: AsyncSession) -> list[dict]:
    """Laedt die letzten 10 Empfehlungen (alle Sessions)."""
    result = await db.execute(
        select(AIRecommendationModel).order_by(AIRecommendationModel.created_at.desc()).limit(10)
    )
    return [{"type": r.type, "title": r.title, "status": r.status} for r in result.scalars().all()]


# ---------------------------------------------------------------------------
# Prompt-Builder
# ---------------------------------------------------------------------------


def _build_system_prompt(ctx: RecommendationContext) -> str:
    """System-Prompt fuer Empfehlungsgenerierung."""
    parts = [
        "Du bist ein erfahrener Lauf- und Krafttrainer.",
        "Deine Aufgabe: Generiere konkrete, umsetzbare Trainingsempfehlungen.",
        "",
        "Regeln:",
        "- Priorisiere Gesundheit vor Performance",
        "- Achte auf Uebertraining-Signale",
        "- Empfehlungen muessen spezifisch und actionable sein",
        "- Beruecksichtige die Trainingsphase und das Wettkampfziel",
        "- Vermeide generische Ratschlaege",
    ]

    if ctx.race_goal:
        g = ctx.race_goal
        parts.append("")
        parts.append(f"Wettkampfziel: {g['title']} ({g['distance_km']} km)")
        if g.get("target_pace"):
            parts.append(f"Zielpace: {g['target_pace']} min/km")
        if g.get("date"):
            parts.append(f"Wettkampf am: {g['date']}")

    if ctx.current_phase:
        p = ctx.current_phase
        parts.append("")
        parts.append(f"Trainingsplan: {p.get('plan_name', '?')}")
        if p.get("phase_name"):
            parts.append(f"Phase: {p['phase_name']} ({p.get('phase_type', '?')})")
        parts.append(f"Woche: {p.get('week', '?')}")

    return "\n".join(parts)


def _build_recommendation_prompt(ctx: RecommendationContext) -> str:
    """User-Prompt fuer Empfehlungsgenerierung."""
    parts: list[str] = []

    # Session-Analyse (bereits durchgefuehrt)
    parts.append("## Session-Analyse (bereits durchgefuehrt)")
    parts.append(f"- Zusammenfassung: {ctx.analysis_summary}")
    parts.append(f"- Intensitaet: {ctx.intensity_rating}")
    if ctx.fatigue_indicators:
        parts.append(f"- Ermuedungssignale: {ctx.fatigue_indicators}")
    if ctx.plan_comparison:
        parts.append(f"- Soll/Ist: {ctx.plan_comparison}")
    if ctx.analysis_recommendations:
        parts.append("- Bisherige Kurzempfehlungen:")
        for rec in ctx.analysis_recommendations:
            parts.append(f"  - {rec}")

    # Wochenvolumen
    parts.append("")
    parts.append("## Wochenvolumen (aktuelle Woche)")
    wv = ctx.weekly_volume
    parts.append(
        f"- Sessions: {wv['session_count']} ({wv['run_count']} Lauf, {wv['strength_count']} Kraft)"
    )
    parts.append(f"- Distanz: {wv['total_km']} km")
    parts.append(f"- Dauer: {wv['total_hours']} Stunden")

    # Geplante Sessions
    if ctx.upcoming_sessions:
        parts.append("")
        parts.append("## Geplante Sessions (naechste 7 Tage)")
        for s in ctx.upcoming_sessions:
            label = s.get("run_type") or s["type"]
            dur = f", {s['target_duration_min']}min" if s.get("target_duration_min") else ""
            pace = f", Pace {s['target_pace']}" if s.get("target_pace") else ""
            parts.append(f"- {s['date']}: {label}{dur}{pace}")

    # Bereits gegebene Empfehlungen (Duplikat-Vermeidung)
    if ctx.recent_recommendations:
        parts.append("")
        parts.append("## Bereits gegebene Empfehlungen (nicht wiederholen)")
        for r in ctx.recent_recommendations:
            parts.append(f"- [{r['type']}] {r['title']} (Status: {r['status']})")

    # Anweisungen
    parts.append("")
    parts.append(_build_instructions())

    return "\n".join(parts)


def _build_instructions() -> str:
    """Anweisungen fuer die KI."""
    valid_types = ", ".join(sorted(VALID_TYPES))
    return f"""## Anweisungen
Generiere 2-5 konkrete Trainingsempfehlungen. Antworte NUR mit einem JSON-Array (ohne Markdown-Codeblock):

[
  {{
    "type": "EMPFEHLUNG_TYP",
    "title": "Kurzer Titel (max 60 Zeichen)",
    "current_value": "Aktueller Wert oder null",
    "suggested_value": "Vorgeschlagener Wert oder null",
    "reasoning": "1-3 Saetze Begruendung warum diese Aenderung sinnvoll ist",
    "priority": "high|medium|low"
  }}
]

Gueltige Typen: {valid_types}

Regeln:
- Auf Deutsch antworten
- 2-5 Empfehlungen, sortiert nach Prioritaet (high zuerst)
- Jede Empfehlung muss spezifisch und umsetzbar sein
- current_value/suggested_value: konkrete Werte wenn moeglich (z.B. "5:20 min/km" -> "5:40 min/km")
- Bei add_rest: current_value = geplante Session, suggested_value = "Ruhetag"
- Bei skip_session: current_value = geplante Session, suggested_value = "Ueberspringen"
- Keine generischen Empfehlungen wie "Hoer auf deinen Koerper"
- NICHT die bereits gegebenen Empfehlungen wiederholen"""


# ---------------------------------------------------------------------------
# JSON-Parsing
# ---------------------------------------------------------------------------


def _parse_recommendations_json(raw: str) -> list[dict]:
    """Parst die AI-Antwort als JSON-Array von Empfehlungen."""
    text = raw.strip()

    # Provider-Prefix entfernen
    if text.startswith("[") and "]" in text and not text.startswith("[["):
        # Koennte ein JSON-Array sein, versuche direkt zu parsen
        pass
    elif text.startswith("[") and "]" in text:
        bracket_idx = text.index("]")
        remaining = text[bracket_idx + 1 :].strip()
        if remaining.startswith("["):
            text = remaining

    # Provider-Tag am Anfang: "[Claude (...)] [...]"
    if text.startswith("[") and not text.startswith("[["):
        try:
            json.loads(text)
        except json.JSONDecodeError:
            # Wahrscheinlich Provider-Tag
            close_bracket = text.index("]")
            text = text[close_bracket + 1 :].strip()

    # Markdown-Codeblock entfernen
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Empfehlungen konnten nicht geparst werden: %s", text[:200])
        return [_fallback_recommendation()]

    if not isinstance(data, list):
        data = [data]

    results = []
    for item in data:
        if not isinstance(item, dict):
            continue
        results.append(_normalize_recommendation(item))

    return results if results else [_fallback_recommendation()]


def _normalize_recommendation(item: dict) -> dict:
    """Normalisiert eine einzelne Empfehlung."""
    rec_type = str(item.get("type", "general")).lower()
    if rec_type not in VALID_TYPES:
        rec_type = "general"

    priority = str(item.get("priority", "medium")).lower()
    if priority not in VALID_PRIORITIES:
        priority = "medium"

    return {
        "type": rec_type,
        "title": str(item.get("title", "Trainingsempfehlung"))[:200],
        "current_value": item.get("current_value"),
        "suggested_value": item.get("suggested_value"),
        "reasoning": str(item.get("reasoning", "Keine Begruendung verfuegbar.")),
        "priority": priority,
    }


def _fallback_recommendation() -> dict:
    """Erstellt eine Fallback-Empfehlung bei Parse-Fehler."""
    return {
        "type": "general",
        "title": "Analyse erneut durchfuehren",
        "current_value": None,
        "suggested_value": None,
        "reasoning": "Die KI-Antwort konnte nicht strukturiert verarbeitet werden. "
        "Bitte versuche es erneut.",
        "priority": "low",
    }


# ---------------------------------------------------------------------------
# Response-Builder
# ---------------------------------------------------------------------------


def _model_to_response(m: AIRecommendationModel) -> RecommendationResponse:
    """Konvertiert DB-Model in Response."""
    return RecommendationResponse(
        id=m.id,
        session_id=m.session_id,
        type=RecommendationType(m.type),
        title=m.title,
        target_session_id=m.target_session_id,
        current_value=m.current_value,
        suggested_value=m.suggested_value,
        reasoning=m.reasoning,
        priority=RecommendationPriority(m.priority),
        status=RecommendationStatus(m.status),
        created_at=m.created_at.isoformat() if m.created_at else "",
    )


def _build_response(
    models: list[AIRecommendationModel],
    session_id: int,
    provider: str,
    *,
    is_cached: bool,
) -> RecommendationsListResponse:
    """Baut die API-Response."""
    # Sortierung: high > medium > low
    priority_order = {"high": 0, "medium": 1, "low": 2}
    sorted_models = sorted(models, key=lambda m: priority_order.get(m.priority, 9))

    return RecommendationsListResponse(
        recommendations=[_model_to_response(m) for m in sorted_models],
        session_id=session_id,
        provider=provider,
        cached=is_cached,
    )
