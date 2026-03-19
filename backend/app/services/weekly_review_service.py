"""Wöchentliches KI-Trainingsreview Service (E06-S06).

Aggregiert alle Sessions einer Woche und generiert ein strukturiertes
Review mit Zusammenfassung, Highlights, Verbesserungspotenzial und
Empfehlungen für die nächste Woche.
"""

import json
import logging
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key_resolver import resolve_claude_api_key
from app.infrastructure.ai.ai_service import ai_service
from app.infrastructure.database.models import (
    RaceGoalModel,
    TrainingPhaseModel,
    TrainingPlanModel,
    WeeklyReviewModel,
    WorkoutModel,
)
from app.models.weekly_review import (
    FatigueLevel,
    OverallRating,
    VolumeComparison,
    WeeklyReviewResponse,
)
from app.services.ai_log_service import AICallData, log_ai_call

logger = logging.getLogger(__name__)

VALID_RATINGS = {r.value for r in OverallRating}
VALID_FATIGUE = {f.value for f in FatigueLevel}


@dataclass
class WeeklyContext:
    """Kontext für die Wochen-Review-Generierung."""

    week_start: date
    sessions: list[dict]
    volume: dict
    race_goal: dict | None
    current_phase: dict | None
    session_analyses: list[dict]


async def generate_weekly_review(
    week_start: date,
    db: AsyncSession,
    *,
    force_refresh: bool = False,
) -> WeeklyReviewResponse:
    """Generiert ein wöchentliches KI-Trainingsreview."""
    _validate_week_start(week_start)

    # Cache prüfen
    if not force_refresh:
        cached = await _load_cached_review(week_start, db)
        if cached:
            return _model_to_response(cached, is_cached=True)

    # Kontext laden
    context = await _load_weekly_context(week_start, db)

    # Prompt bauen und AI aufrufen
    prompt = _build_review_prompt(context)
    system_prompt = _build_system_prompt(context)
    api_key = await resolve_claude_api_key(db)

    t0 = time.monotonic()
    raw = await ai_service.chat(prompt, {"system_prompt": system_prompt}, api_key)
    duration_ms = int((time.monotonic() - t0) * 1000)
    provider = ai_service.get_active_provider() or "unknown"

    # Parsen
    parsed = _parse_review_json(raw, context)

    # Altes Review löschen, neues speichern
    await _delete_existing_review(week_start, db)
    model = await _save_review(week_start, parsed, provider, context, db)

    # Log
    await log_ai_call(
        db,
        AICallData(
            use_case="weekly_review",
            provider=provider,
            system_prompt=system_prompt,
            user_prompt=prompt,
            raw_response=raw,
            parsed_ok=True,
            duration_ms=duration_ms,
        ),
    )
    await db.commit()

    return _model_to_response(model, is_cached=False)


async def get_weekly_review(
    week_start: date,
    db: AsyncSession,
) -> WeeklyReviewResponse | None:
    """Lädt ein gespeichertes Wochen-Review."""
    _validate_week_start(week_start)
    model = await _load_cached_review(week_start, db)
    if not model:
        return None
    return _model_to_response(model, is_cached=True)


# ---------------------------------------------------------------------------
# Validierung
# ---------------------------------------------------------------------------


def _weeks_until_race(week_start: date, race_date_str: str) -> int | None:
    """Berechnet die Wochen zwischen Wochenstart und Wettkampfdatum."""
    try:
        race_date = date.fromisoformat(race_date_str)
    except (ValueError, TypeError):
        return None
    delta_days = (race_date - week_start).days
    if delta_days < 0:
        return 0
    return delta_days // 7


def _validate_week_start(week_start: date) -> None:
    """Stellt sicher, dass week_start ein Montag ist."""
    if week_start.weekday() != 0:
        raise ValueError(
            f"week_start muss ein Montag sein, ist aber {week_start.strftime('%A')} ({week_start})"
        )


# ---------------------------------------------------------------------------
# Kontext laden
# ---------------------------------------------------------------------------


async def _load_weekly_context(week_start: date, db: AsyncSession) -> WeeklyContext:
    """Lädt den vollständigen Kontext für eine Trainingswoche."""
    week_end = week_start + timedelta(days=6)

    # Alle Sessions der Woche
    sessions = await _load_week_sessions(week_start, week_end, db)

    # Volumen berechnen
    volume = _calculate_volume(sessions)

    # Wettkampfziel
    race_goal = await _load_race_goal(db)

    # Trainingsphase
    current_phase = await _load_current_phase(week_start, db)

    # Session-Analysen (sofern vorhanden)
    analyses = _extract_analyses(sessions)

    return WeeklyContext(
        week_start=week_start,
        sessions=[_session_to_dict(s) for s in sessions],
        volume=volume,
        race_goal=race_goal,
        current_phase=current_phase,
        session_analyses=analyses,
    )


async def _load_week_sessions(
    week_start: date,
    week_end: date,
    db: AsyncSession,
) -> list[WorkoutModel]:
    """Lädt alle Sessions einer Woche."""
    result = await db.execute(
        select(WorkoutModel)
        .where(
            WorkoutModel.date >= datetime.combine(week_start, datetime.min.time()),
            WorkoutModel.date <= datetime.combine(week_end, datetime.max.time()),
        )
        .order_by(WorkoutModel.date)
    )
    return list(result.scalars().all())


def _calculate_volume(sessions: list[WorkoutModel]) -> dict:
    """Berechnet Wochenvolumen aus Sessions."""
    total_km = sum(s.distance_km or 0 for s in sessions)
    total_min = sum((s.duration_sec or 0) / 60 for s in sessions)
    run_count = sum(1 for s in sessions if s.workout_type == "running")
    strength_count = sum(1 for s in sessions if s.workout_type == "strength")

    return {
        "total_km": round(total_km, 1),
        "total_hours": round(total_min / 60, 1),
        "session_count": len(sessions),
        "run_count": run_count,
        "strength_count": strength_count,
    }


def _session_to_dict(s: WorkoutModel) -> dict:
    """Konvertiert WorkoutModel in kompaktes Dict für den Prompt."""
    d: dict = {
        "date": s.date.strftime("%Y-%m-%d"),
        "type": s.workout_type,
        "subtype": s.subtype,
    }
    if s.distance_km:
        d["distance_km"] = round(s.distance_km, 1)
    if s.duration_sec:
        d["duration_min"] = round(s.duration_sec / 60, 1)
    if s.pace:
        d["pace"] = s.pace
    if s.hr_avg:
        d["hr_avg"] = s.hr_avg
    if s.hr_max:
        d["hr_max"] = s.hr_max
    if s.rpe:
        d["rpe"] = s.rpe
    if s.notes:
        d["notes"] = s.notes[:200]

    # Enrichment-Daten
    if s.weather_json:
        try:
            wx = json.loads(str(s.weather_json))
            d["weather"] = (
                f"{wx.get('weather_label', '?')}, {wx.get('temperature_c', '?')}°C, "
                f"Wind {wx.get('wind_speed_kmh', '?')} km/h"
            )
        except json.JSONDecodeError:
            pass
    if s.air_quality_json:
        try:
            aq = json.loads(str(s.air_quality_json))
            d["aqi"] = f"AQI {aq.get('european_aqi', '?')} ({aq.get('aqi_label', '?')})"
        except json.JSONDecodeError:
            pass
    if s.location_name:
        d["location"] = s.location_name

    return d


def _extract_analyses(sessions: list[WorkoutModel]) -> list[dict]:
    """Extrahiert vorhandene KI-Analysen aus Sessions."""
    analyses = []
    for s in sessions:
        if not s.ai_analysis:
            continue
        try:
            analysis = json.loads(s.ai_analysis)
            analyses.append(
                {
                    "date": s.date.strftime("%Y-%m-%d"),
                    "type": s.subtype or s.workout_type,
                    "summary": analysis.get("summary", ""),
                    "intensity_rating": analysis.get("intensity_rating", ""),
                }
            )
        except json.JSONDecodeError:
            continue
    return analyses


async def _load_race_goal(db: AsyncSession) -> dict | None:
    """Lädt das aktive Wettkampfziel."""
    result = await db.execute(
        select(RaceGoalModel).where(RaceGoalModel.is_active.is_(True)).limit(1)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        return None

    target_pace = None
    if goal.target_time_seconds and goal.distance_km and goal.distance_km > 0:
        pace_min = (goal.target_time_seconds / 60) / goal.distance_km
        m = int(pace_min)
        s = int((pace_min - m) * 60)
        target_pace = f"{m}:{s:02d}"

    return {
        "title": goal.title,
        "date": str(
            goal.race_date.date() if isinstance(goal.race_date, datetime) else goal.race_date
        ),
        "distance_km": goal.distance_km,
        "target_pace": target_pace,
    }


async def _load_current_phase(ref_date: date, db: AsyncSession) -> dict | None:
    """Lädt die aktuelle Trainingsphase."""
    plan_result = await db.execute(
        select(TrainingPlanModel)
        .where(TrainingPlanModel.status == "active")
        .order_by(TrainingPlanModel.start_date.desc())
        .limit(1)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        return None

    days_since_start = (ref_date - plan.start_date).days  # type: ignore[operator]
    current_week = (days_since_start // 7) + 1

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


# ---------------------------------------------------------------------------
# Cache / DB
# ---------------------------------------------------------------------------


async def _load_cached_review(
    week_start: date,
    db: AsyncSession,
) -> WeeklyReviewModel | None:
    """Lädt ein gecachtes Review für eine Woche."""
    result = await db.execute(
        select(WeeklyReviewModel).where(WeeklyReviewModel.week_start == week_start)
    )
    return result.scalar_one_or_none()


async def _delete_existing_review(week_start: date, db: AsyncSession) -> None:
    """Löscht ein bestehendes Review für eine Woche."""
    from sqlalchemy import delete

    await db.execute(delete(WeeklyReviewModel).where(WeeklyReviewModel.week_start == week_start))


async def _save_review(
    week_start: date,
    parsed: dict,
    provider: str,
    context: WeeklyContext,
    db: AsyncSession,
) -> WeeklyReviewModel:
    """Speichert ein geparstes Review in der DB."""
    model = WeeklyReviewModel(
        week_start=week_start,
        summary=parsed["summary"],
        volume_comparison_json=json.dumps(parsed["volume_comparison"]),
        highlights_json=json.dumps(parsed["highlights"]),
        improvements_json=json.dumps(parsed["improvements"]),
        next_week_recommendations_json=json.dumps(parsed["next_week_recommendations"]),
        overall_rating=parsed["overall_rating"],
        fatigue_assessment=parsed["fatigue_assessment"],
        session_count=context.volume["session_count"],
        provider=provider,
    )
    db.add(model)
    await db.flush()
    await db.refresh(model)
    return model


# ---------------------------------------------------------------------------
# Prompt-Builder
# ---------------------------------------------------------------------------


def _build_system_prompt(ctx: WeeklyContext) -> str:
    """System-Prompt für Wochen-Review."""
    parts = [
        "Du bist ein erfahrener Lauf- und Krafttrainer.",
        "Deine Aufgabe: Erstelle ein umfassendes Wochen-Review des Trainings.",
        "",
        "Regeln:",
        "- Analysiere die gesamte Trainingswoche holistisch",
        "- Bewerte Balance zwischen Belastung und Erholung",
        "- Erkenne Muster (z.B. zu viel Intensitaet, fehlende Variation)",
        "- Empfehlungen muessen spezifisch und fuer die naechste Woche umsetzbar sein",
        "- Beruecksichtige Umgebungsbedingungen (Wetter, Temperatur, Luftqualitaet) im Review",
        "- Erklaere Leistungsschwankungen durch Wetter (Hitze, Wind, Regen, schlechte Luft)",
        "- Auf Deutsch antworten",
    ]

    if ctx.race_goal:
        g = ctx.race_goal
        parts.append("")
        parts.append(f"Wettkampfziel: {g['title']} ({g['distance_km']} km)")
        if g.get("target_pace"):
            parts.append(f"Zielpace: {g['target_pace']} min/km")
        if g.get("date"):
            parts.append(f"Wettkampf am: {g['date']}")
            weeks_until = _weeks_until_race(ctx.week_start, g["date"])
            if weeks_until is not None:
                parts.append(f"Wochen bis Wettkampf: {weeks_until}")
                if weeks_until <= 3:
                    parts.append(
                        "WICHTIG: Tapering-Phase! Umfang reduzieren, keine neuen Reize, "
                        "Erholung priorisieren. Keine langen Läufe (>10 km) mehr empfehlen."
                    )
                elif weeks_until <= 6:
                    parts.append(
                        "Wettkampf-spezifische Phase: Intensität beibehalten, "
                        "aber Umfang langsam reduzieren. Long Runs verkürzen."
                    )

    if ctx.current_phase:
        p = ctx.current_phase
        parts.append("")
        parts.append(f"Trainingsplan: {p.get('plan_name', '?')}")
        if p.get("phase_name"):
            parts.append(f"Phase: {p['phase_name']} ({p.get('phase_type', '?')})")
        parts.append(f"Woche: {p.get('week', '?')}")

    return "\n".join(parts)


def _format_session_line(s: dict) -> list[str]:
    """Formatiert eine Session als Prompt-Zeilen."""
    label = s.get("subtype") or s["type"]
    details = []
    for key, fmt in [
        ("distance_km", "{} km"),
        ("duration_min", "{} min"),
        ("pace", "Pace {}"),
        ("hr_avg", "HF Ø{}"),
        ("rpe", "RPE {}"),
    ]:
        if s.get(key):
            details.append(fmt.format(s[key]))
    detail_str = ", ".join(details) if details else ""
    lines = [f"- {s['date']}: {label} ({detail_str})"]
    for key, prefix in [
        ("weather", "Wetter"),
        ("aqi", "Luft"),
        ("location", "Ort"),
        ("notes", "Notizen"),
    ]:
        if s.get(key):
            lines.append(f"  {prefix}: {s[key]}")
    return lines


def _build_review_prompt(ctx: WeeklyContext) -> str:
    """User-Prompt für Wochen-Review."""
    parts: list[str] = []

    parts.append(
        f"## Trainingswoche {ctx.week_start.strftime('%d.%m.%Y')} "
        f"– {(ctx.week_start + timedelta(days=6)).strftime('%d.%m.%Y')}"
    )

    # Sessions auflisten
    parts.append("")
    parts.append("## Durchgeführte Sessions")
    if not ctx.sessions:
        parts.append("Keine Sessions in dieser Woche.")
    else:
        for s in ctx.sessions:
            parts.extend(_format_session_line(s))

    # Wochenvolumen
    parts.append("")
    parts.append("## Wochenvolumen")
    v = ctx.volume
    parts.append(
        f"- Sessions: {v['session_count']} ({v['run_count']} Lauf, {v['strength_count']} Kraft)"
    )
    parts.append(f"- Distanz: {v['total_km']} km")
    parts.append(f"- Dauer: {v['total_hours']} Stunden")

    # Session-Analysen
    if ctx.session_analyses:
        parts.append("")
        parts.append("## Bisherige KI-Analysen der einzelnen Sessions")
        for a in ctx.session_analyses:
            parts.append(
                f"- {a['date']} ({a['type']}): {a['summary'][:150]} "
                f"[Intensitaet: {a['intensity_rating']}]"
            )

    # Anweisungen
    parts.append("")
    parts.append(_build_review_instructions())

    return "\n".join(parts)


def _build_review_instructions() -> str:
    """Anweisungen für die KI."""
    return """## Anweisungen
Erstelle ein Wochen-Review. Antworte NUR mit einem JSON-Objekt (ohne Markdown-Codeblock):

{
  "summary": "2-4 Saetze Zusammenfassung der Trainingswoche",
  "volume_comparison": {
    "actual_km": 42.0,
    "actual_sessions": 4,
    "actual_hours": 5.5
  },
  "highlights": ["Positiv-Punkt 1", "Positiv-Punkt 2"],
  "improvements": ["Verbesserung 1", "Verbesserung 2"],
  "next_week_recommendations": ["Konkrete Empfehlung 1", "Konkrete Empfehlung 2"],
  "overall_rating": "good",
  "fatigue_assessment": "moderate"
}

Regeln:
- summary: 2-4 Saetze, nicht laenger
- highlights: 2-4 positive Aspekte der Woche
- improvements: 1-3 Verbesserungsvorschlaege
- next_week_recommendations: 2-4 konkrete Empfehlungen fuer die naechste Woche
- overall_rating: "excellent", "good", "moderate", oder "poor"
- fatigue_assessment: "low", "moderate", "high", oder "critical"
- volume_comparison.actual_km/actual_sessions/actual_hours: Echte Werte aus den Daten
- Auf Deutsch antworten
- Keine generischen Ratschlaege
- Empfehlungen MUESSEN zur aktuellen Trainingsphase und Wettkampfnaehe passen
- Bei Tapering (<=3 Wochen vor Wettkampf): KEINE langen Laeufe, Umfang reduzieren, Erholung betonen
- Bei wettkampfspezifischer Phase (<=6 Wochen): Intensitaet halten, Umfang moderat reduzieren"""


# ---------------------------------------------------------------------------
# JSON-Parsing
# ---------------------------------------------------------------------------


def _parse_review_json(raw: str, context: WeeklyContext) -> dict:
    """Parst die AI-Antwort als JSON-Objekt."""
    text = raw.strip()

    # Markdown-Codeblock entfernen
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    # Provider-Tag entfernen: "[Claude ...] {...}"
    if text.startswith("[") and "{" in text:
        brace_idx = text.index("{")
        text = text[brace_idx:]

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Wochen-Review konnte nicht geparst werden: %s", text[:200])
        return _fallback_review(context)

    if not isinstance(data, dict):
        return _fallback_review(context)

    return _normalize_review(data, context)


def _normalize_review(data: dict, context: WeeklyContext) -> dict:
    """Normalisiert ein geparstes Review."""
    rating = str(data.get("overall_rating", "moderate")).lower()
    if rating not in VALID_RATINGS:
        rating = "moderate"

    fatigue = str(data.get("fatigue_assessment", "moderate")).lower()
    if fatigue not in VALID_FATIGUE:
        fatigue = "moderate"

    vol = data.get("volume_comparison", {})
    if not isinstance(vol, dict):
        vol = {}

    return {
        "summary": str(data.get("summary", "Keine Zusammenfassung verfügbar.")),
        "volume_comparison": {
            "actual_km": float(vol.get("actual_km", context.volume["total_km"])),
            "actual_sessions": int(vol.get("actual_sessions", context.volume["session_count"])),
            "actual_hours": float(vol.get("actual_hours", context.volume["total_hours"])),
        },
        "highlights": _ensure_str_list(data.get("highlights", [])),
        "improvements": _ensure_str_list(data.get("improvements", [])),
        "next_week_recommendations": _ensure_str_list(data.get("next_week_recommendations", [])),
        "overall_rating": rating,
        "fatigue_assessment": fatigue,
    }


def _ensure_str_list(value: object) -> list[str]:
    """Stellt sicher, dass der Wert eine Liste von Strings ist."""
    if not isinstance(value, list):
        return [str(value)] if value else []
    return [str(v) for v in value if v]


def _fallback_review(context: WeeklyContext) -> dict:
    """Fallback bei Parse-Fehler."""
    return {
        "summary": "Das Wochen-Review konnte nicht generiert werden. Bitte erneut versuchen.",
        "volume_comparison": {
            "actual_km": context.volume["total_km"],
            "actual_sessions": context.volume["session_count"],
            "actual_hours": context.volume["total_hours"],
        },
        "highlights": [],
        "improvements": [],
        "next_week_recommendations": [],
        "overall_rating": "moderate",
        "fatigue_assessment": "moderate",
    }


# ---------------------------------------------------------------------------
# Response-Builder
# ---------------------------------------------------------------------------


def _model_to_response(
    model: WeeklyReviewModel,
    *,
    is_cached: bool,
) -> WeeklyReviewResponse:
    """Konvertiert DB-Model in Response."""
    vol_data = json.loads(model.volume_comparison_json)

    return WeeklyReviewResponse(
        id=model.id,
        week_start=str(model.week_start),
        summary=model.summary,
        volume_comparison=VolumeComparison(
            actual_km=vol_data.get("actual_km", 0),
            actual_sessions=vol_data.get("actual_sessions", 0),
            actual_hours=vol_data.get("actual_hours", 0),
        ),
        highlights=json.loads(model.highlights_json),
        improvements=json.loads(model.improvements_json),
        next_week_recommendations=json.loads(model.next_week_recommendations_json),
        overall_rating=OverallRating(model.overall_rating),
        fatigue_assessment=FatigueLevel(model.fatigue_assessment),
        session_count=model.session_count,
        provider=model.provider,
        cached=is_cached,
        created_at=model.review_created_at.isoformat() if model.review_created_at else "",
    )
