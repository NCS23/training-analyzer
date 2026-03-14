"""KI Session-Analyse Service.

Baut strukturierten Prompt mit vollem Session-Kontext und parst
die JSON-Antwort des AI-Providers.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key_resolver import resolve_claude_api_key
from app.infrastructure.ai.ai_service import ai_service
from app.infrastructure.database.models import (
    PlannedSessionModel,
    RaceGoalModel,
    WorkoutModel,
)
from app.models.ai_analysis import SessionAnalysisResponse

logger = logging.getLogger(__name__)


@dataclass
class AnalysisContext:
    """Kontext-Daten für die Analyse."""

    history: list[dict]
    race_goal: dict | None
    planned_session: dict | None


async def analyze_session(
    session_id: int,
    db: AsyncSession,
    *,
    force_refresh: bool = False,
) -> SessionAnalysisResponse:
    """Analysiert eine Session mit KI (Cache-First)."""
    workout = await _load_workout(session_id, db)

    # Cache prüfen
    if not force_refresh and workout.ai_analysis:
        return _from_cache(session_id, workout.ai_analysis)

    # Kontext laden, Prompt bauen, AI aufrufen
    context = await _load_analysis_context(workout, db)
    prompt = _build_analysis_prompt(workout, context)
    api_key = await resolve_claude_api_key(db)

    raw = await ai_service.chat(prompt, {}, api_key)
    provider = ai_service.get_active_provider() or "unknown"

    # Parsen + Cache speichern
    analysis = _parse_analysis_json(raw, session_id, provider)
    workout.ai_analysis = json.dumps(analysis.model_dump())
    await db.commit()

    return analysis


async def _load_workout(session_id: int, db: AsyncSession) -> WorkoutModel:
    """Lädt Workout oder wirft ValueError."""
    result = await db.execute(select(WorkoutModel).where(WorkoutModel.id == session_id))
    workout = result.scalar_one_or_none()
    if not workout:
        raise ValueError(f"Session {session_id} nicht gefunden")
    return workout


def _from_cache(session_id: int, raw: str) -> SessionAnalysisResponse:
    """Liest gecachte Analyse aus dem DB-Feld."""
    try:
        data = json.loads(raw)
        data["cached"] = True
        data["session_id"] = session_id
        return SessionAnalysisResponse(**data)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        raise ValueError("Cache ungültig") from e


async def _load_analysis_context(workout: WorkoutModel, db: AsyncSession) -> AnalysisContext:
    """Lädt Trainingshistorie, Ziel und geplante Session."""
    workout_date = workout.date.date() if isinstance(workout.date, datetime) else workout.date
    four_weeks_ago = datetime.combine(workout_date - timedelta(weeks=4), datetime.min.time())

    # Letzte 20 Sessions (4 Wochen)
    hist_result = await db.execute(
        select(WorkoutModel)
        .where(
            WorkoutModel.date >= four_weeks_ago,
            WorkoutModel.id != workout.id,
        )
        .order_by(WorkoutModel.date.desc())
        .limit(20)
    )
    history = [_workout_to_summary(w) for w in hist_result.scalars().all()]

    # Aktives Wettkampfziel
    goal_result = await db.execute(
        select(RaceGoalModel).where(RaceGoalModel.is_active.is_(True)).limit(1)
    )
    goal_model = goal_result.scalar_one_or_none()
    race_goal = _goal_to_dict(goal_model) if goal_model else None

    # Geplante Session
    planned = None
    if workout.planned_entry_id:
        ps_result = await db.execute(
            select(PlannedSessionModel).where(PlannedSessionModel.id == workout.planned_entry_id)
        )
        ps = ps_result.scalar_one_or_none()
        if ps:
            planned = _planned_to_dict(ps)

    return AnalysisContext(history=history, race_goal=race_goal, planned_session=planned)


def _workout_to_summary(w: WorkoutModel) -> dict:
    """Workout in Kurz-Dict für History."""
    w_date = w.date.date() if isinstance(w.date, datetime) else w.date
    return {
        "date": str(w_date),
        "type": str(w.workout_type),
        "duration_min": round(w.duration_sec / 60) if w.duration_sec else None,
        "distance_km": w.distance_km,
        "pace": str(w.pace) if w.pace else None,
        "hr_avg": w.hr_avg,
    }


def _goal_to_dict(g: RaceGoalModel) -> dict:
    """RaceGoal in Dict für Prompt."""
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
        "target_time_min": round(g.target_time_seconds / 60) if g.target_time_seconds else None,
        "target_pace": target_pace,
    }


def _planned_to_dict(ps: PlannedSessionModel) -> dict:
    """PlannedSession in Dict für Prompt."""
    segments = None
    if ps.run_details_json:
        try:
            rd = json.loads(str(ps.run_details_json))
            segments = rd.get("segments")
        except json.JSONDecodeError:
            pass
    return {
        "training_type": str(ps.training_type),
        "segments": segments,
        "notes": str(ps.notes) if ps.notes else None,
    }


def _build_analysis_prompt(workout: WorkoutModel, ctx: AnalysisContext) -> str:
    """Baut den vollständigen Analyse-Prompt."""
    parts: list[str] = []

    # Session-Daten
    parts.append(_build_session_section(workout))

    # Laps
    if workout.laps_json:
        parts.append(_build_laps_section(workout.laps_json))

    # HF-Zonen
    if workout.hr_zones_json:
        parts.append(_build_hr_zones_section(workout.hr_zones_json))

    # Trainingshistorie
    if ctx.history:
        parts.append(_build_history_section(ctx.history))

    # Wettkampfziel
    if ctx.race_goal:
        parts.append(_build_goal_section(ctx.race_goal))

    # Geplante Session (Soll/Ist)
    if ctx.planned_session:
        parts.append(_build_planned_section(ctx.planned_session))

    # Anweisungen
    parts.append(_build_instructions())

    return "\n\n".join(parts)


def _build_session_section(w: WorkoutModel) -> str:
    """Session-Kerndaten."""
    w_date = w.date.date() if isinstance(w.date, datetime) else w.date
    dur_min = round(w.duration_sec / 60) if w.duration_sec else "?"
    effective_type = str(w.training_type_override or w.training_type_auto or w.workout_type)

    return f"""## Aktuelle Session
- Datum: {w_date}
- Typ: {w.workout_type}, Trainingsart: {effective_type}
- Dauer: {dur_min} min
- Distanz: {w.distance_km or "?"} km
- Pace: {w.pace or "?"}
- HF Ø/Max/Min: {w.hr_avg or "?"}/{w.hr_max or "?"}/{w.hr_min or "?"} bpm
- Kadenz: {w.cadence_avg or "?"} spm
- RPE: {w.rpe or "nicht angegeben"}"""


def _build_laps_section(laps_json: str) -> str:
    """Laps-Tabelle."""
    try:
        laps = json.loads(laps_json)
    except json.JSONDecodeError:
        return ""

    lines = [
        "## Laps",
        "| # | Typ | Dauer | Distanz | Pace | HF Ø |",
        "|---|-----|-------|---------|------|------|",
    ]
    for lap in laps:
        typ = lap.get("user_override") or lap.get("suggested_type") or "-"
        dur = lap.get("duration_formatted", "?")
        dist = f"{lap.get('distance_km', 0):.2f}" if lap.get("distance_km") else "-"
        pace = lap.get("pace_formatted") or "-"
        hr = str(lap.get("avg_hr_bpm", "-"))
        lines.append(f"| {lap.get('lap_number', '?')} | {typ} | {dur} | {dist} | {pace} | {hr} |")
    return "\n".join(lines)


def _build_hr_zones_section(hr_zones_json: str) -> str:
    """HF-Zonen-Verteilung."""
    try:
        zones = json.loads(hr_zones_json)
    except json.JSONDecodeError:
        return ""

    lines = ["## HF-Zonen"]
    for key, zone in zones.items():
        if isinstance(zone, dict):
            label = zone.get("label", key)
            pct = zone.get("percentage", 0)
            secs = zone.get("seconds", 0)
            lines.append(f"- {label}: {pct:.0f}% ({secs}s)")
    return "\n".join(lines)


def _build_history_section(history: list[dict]) -> str:
    """Trainingshistorie der letzten 4 Wochen."""
    lines = ["## Trainingshistorie (letzte 4 Wochen)"]
    for h in history[:10]:
        dur = f"{h['duration_min']}min" if h.get("duration_min") else "?"
        dist = f"{h['distance_km']:.1f}km" if h.get("distance_km") else ""
        pace = h.get("pace") or ""
        lines.append(f"- {h['date']}: {h['type']} — {dur} {dist} {pace}")
    return "\n".join(lines)


def _build_goal_section(goal: dict) -> str:
    """Wettkampfziel."""
    return f"""## Wettkampfziel
- {goal["title"]} am {goal["date"]}
- Distanz: {goal["distance_km"]} km
- Zielzeit: {goal.get("target_time_min", "?")} min
- Zielpace: {goal.get("target_pace", "?")} min/km"""


def _build_planned_section(planned: dict) -> str:
    """Geplante Session für Soll/Ist-Vergleich."""
    lines = ["## Geplante Session (Soll)", f"- Typ: {planned['training_type']}"]
    if planned.get("notes"):
        lines.append(f"- Hinweis: {planned['notes']}")
    if planned.get("segments"):
        lines.append("- Segmente:")
        for seg in planned["segments"]:
            lines.append(
                f"  - {seg.get('type', '?')}: {seg.get('duration_minutes', '?')}min, Pace {seg.get('target_pace', '?')}"
            )
    return "\n".join(lines)


def _build_instructions() -> str:
    """Anweisungen für die KI."""
    return """## Anweisungen
Analysiere diese Trainingseinheit als erfahrener Lauftrainer. Antworte NUR mit validem JSON (ohne Markdown-Codeblock):

{
  "summary": "2-3 Sätze Gesamtbewertung der Einheit",
  "intensity_rating": "leicht|moderat|intensiv|zu_intensiv",
  "intensity_text": "Kurze Begründung der Intensitätsbewertung",
  "hr_zone_assessment": "Bewertung der HF-Zonen-Verteilung im Kontext des Trainingstyps",
  "plan_comparison": "Soll/Ist-Vergleich (null wenn kein Plan vorhanden)",
  "fatigue_indicators": "Ermüdungs-Hinweise (null wenn keine erkennbar)",
  "recommendations": ["Empfehlung 1", "Empfehlung 2", "Empfehlung 3"]
}

Regeln:
- Sachlich, konkret, auf Deutsch
- 2-4 Empfehlungen
- intensity_rating MUSS einer der 4 Werte sein
- Wenn kein Plan vorhanden: plan_comparison = null
- Wenn keine Ermüdung erkennbar: fatigue_indicators = null"""


def _parse_analysis_json(raw: str, session_id: int, provider: str) -> SessionAnalysisResponse:
    """Parst die AI-Antwort als JSON, mit Fallback bei ungültigem Format."""
    # Provider-Prefix entfernen (z.B. "[Claude (claude-sonnet-4-20250514)] {...}")
    text = raw.strip()
    if text.startswith("[") and "]" in text:
        text = text[text.index("]") + 1 :].strip()

    # Markdown-Codeblock entfernen falls vorhanden
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(text)
        return SessionAnalysisResponse(
            session_id=session_id,
            provider=provider,
            summary=data.get("summary", ""),
            intensity_rating=data.get("intensity_rating", "moderat"),
            intensity_text=data.get("intensity_text", ""),
            hr_zone_assessment=data.get("hr_zone_assessment", ""),
            plan_comparison=data.get("plan_comparison"),
            fatigue_indicators=data.get("fatigue_indicators"),
            recommendations=data.get("recommendations", []),
        )
    except (json.JSONDecodeError, TypeError):
        logger.warning("AI-Antwort konnte nicht als JSON geparst werden: %s", text[:200])
        return SessionAnalysisResponse(
            session_id=session_id,
            provider=provider,
            summary=text[:500],
            intensity_rating="moderat",
            intensity_text="Konnte nicht automatisch bestimmt werden.",
            hr_zone_assessment="Keine strukturierte Bewertung verfügbar.",
            recommendations=["Analyse erneut durchführen für detaillierte Ergebnisse."],
        )
