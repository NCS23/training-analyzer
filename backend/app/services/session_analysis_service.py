"""KI Session-Analyse Service.

Baut strukturierten Prompt mit vollem Session-Kontext und parst
die JSON-Antwort des AI-Providers.
"""

import contextlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key_resolver import resolve_claude_api_key
from app.infrastructure.ai.ai_service import ai_service
from app.infrastructure.database.models import (
    AthleteModel,
    PlannedSessionModel,
    RaceGoalModel,
    WorkoutModel,
)
from app.models.ai_analysis import SessionAnalysisResponse

logger = logging.getLogger(__name__)


@dataclass
class AnalysisContext:
    """Kontext-Daten fuer die Analyse."""

    history: list[dict]
    race_goal: dict | None
    planned_session: dict | None
    athlete: dict | None


async def analyze_session(
    session_id: int,
    db: AsyncSession,
    *,
    force_refresh: bool = False,
) -> SessionAnalysisResponse:
    """Analysiert eine Session mit KI (Cache-First)."""
    workout = await _load_workout(session_id, db)

    # Cache pruefen
    if not force_refresh and workout.ai_analysis:
        return _from_cache(session_id, workout.ai_analysis)

    # Kontext laden, Prompt bauen, AI aufrufen
    context = await _load_analysis_context(workout, db)
    prompt = _build_analysis_prompt(workout, context)
    system_prompt = _build_system_prompt(context)
    api_key = await resolve_claude_api_key(db)

    raw = await ai_service.chat(prompt, {"system_prompt": system_prompt}, api_key)
    provider = ai_service.get_active_provider() or "unknown"

    # Parsen + Cache speichern
    analysis = _parse_analysis_json(raw, session_id, provider)
    workout.ai_analysis = json.dumps(analysis.model_dump())
    await db.commit()

    return analysis


async def _load_workout(session_id: int, db: AsyncSession) -> WorkoutModel:
    """Laedt Workout oder wirft ValueError."""
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
        raise ValueError("Cache ungueltig") from e


async def _load_analysis_context(workout: WorkoutModel, db: AsyncSession) -> AnalysisContext:
    """Laedt Trainingshistorie, Ziel, geplante Session und Athleten-Daten."""
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

    # Athleten-Daten
    athlete_result = await db.execute(select(AthleteModel).limit(1))
    athlete_model = athlete_result.scalar_one_or_none()
    athlete = _athlete_to_dict(athlete_model) if athlete_model else None

    return AnalysisContext(
        history=history,
        race_goal=race_goal,
        planned_session=planned,
        athlete=athlete,
    )


def _workout_to_summary(w: WorkoutModel) -> dict:
    """Workout in Kurz-Dict fuer History."""
    w_date = w.date.date() if isinstance(w.date, datetime) else w.date
    effective_type = str(w.training_type_override or w.training_type_auto or "")
    return {
        "date": str(w_date),
        "type": str(w.workout_type),
        "training_type": effective_type,
        "duration_min": round(w.duration_sec / 60) if w.duration_sec else None,
        "distance_km": w.distance_km,
        "pace": str(w.pace) if w.pace else None,
        "hr_avg": w.hr_avg,
        "hr_max": w.hr_max,
        "rpe": w.rpe,
    }


def _goal_to_dict(g: RaceGoalModel) -> dict:
    """RaceGoal in Dict fuer Prompt."""
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


def _athlete_to_dict(a: AthleteModel) -> dict:
    """AthleteModel in Dict fuer Prompt."""
    return {
        "resting_hr": a.resting_hr,
        "max_hr": a.max_hr,
    }


def _planned_to_dict(ps: PlannedSessionModel) -> dict:
    """PlannedSession in Dict fuer Prompt — vollstaendig."""
    result: dict = {
        "training_type": str(ps.training_type),
        "notes": str(ps.notes) if ps.notes else None,
    }

    if ps.run_details_json:
        try:
            rd = json.loads(str(ps.run_details_json))
            result["run_type"] = rd.get("run_type")
            result["target_duration_minutes"] = rd.get("target_duration_minutes")
            result["target_pace_min"] = rd.get("target_pace_min")
            result["target_pace_max"] = rd.get("target_pace_max")
            result["target_hr_min"] = rd.get("target_hr_min")
            result["target_hr_max"] = rd.get("target_hr_max")
            result["segments"] = rd.get("segments")
        except json.JSONDecodeError:
            pass

    if ps.exercises_json:
        with contextlib.suppress(json.JSONDecodeError):
            result["exercises"] = json.loads(str(ps.exercises_json))

    return result


# --- Prompt-Builder ---


def _build_system_prompt(ctx: AnalysisContext) -> str:
    """Baut dynamischen System-Prompt aus Athleten-Daten und Wettkampfziel."""
    parts = [
        "Du bist ein erfahrener Lauf- und Krafttrainer.",
        "",
        "Dein Athlet:",
    ]

    # Athleten-Daten
    if ctx.athlete:
        if ctx.athlete.get("resting_hr"):
            parts.append(f"- Ruhe-HF: {ctx.athlete['resting_hr']} bpm")
        if ctx.athlete.get("max_hr"):
            parts.append(f"- Max-HF: {ctx.athlete['max_hr']} bpm")

    # Wettkampfziel
    if ctx.race_goal:
        g = ctx.race_goal
        parts.append(f"- Ziel: {g['title']} ({g['distance_km']} km)")
        if g.get("target_pace"):
            parts.append(f"- Zielpace: {g['target_pace']} min/km")
        if g.get("date"):
            parts.append(f"- Wettkampfdatum: {g['date']}")

    # Trainingsvolumen letzte 4 Wochen
    if ctx.history:
        run_sessions = [h for h in ctx.history if h["type"] == "running"]
        total_km = sum(h.get("distance_km") or 0 for h in run_sessions)
        total_sessions = len(ctx.history)
        if total_km > 0:
            parts.append(f"- Letzte 4 Wochen: {total_sessions} Sessions, {total_km:.0f} km Lauf")

    if len(parts) == 3:
        # Keine Athleten-Daten vorhanden
        parts.append("- Keine spezifischen Daten hinterlegt")

    parts.extend(
        [
            "",
            "Deine Aufgabe:",
            "- Analysiere Trainingseinheiten sachlich und fundiert",
            "- Gib konkrete, umsetzbare Empfehlungen",
            "- Achte auf Uebertraining-Signale",
            "- Priorisiere Gesundheit vor Performance",
            "",
            "Antworte praegnant, freundlich und kompetent.",
        ]
    )

    return "\n".join(parts)


def _build_analysis_prompt(workout: WorkoutModel, ctx: AnalysisContext) -> str:
    """Baut den vollstaendigen Analyse-Prompt."""
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
    """Session-Kerndaten inkl. Hoehenmeter und Notizen."""
    w_date = w.date.date() if isinstance(w.date, datetime) else w.date
    dur_min = round(w.duration_sec / 60) if w.duration_sec else "?"
    effective_type = str(w.training_type_override or w.training_type_auto or w.workout_type)

    lines = [
        "## Aktuelle Session",
        f"- Datum: {w_date}",
        f"- Typ: {w.workout_type}, Trainingsart: {effective_type}",
        f"- Dauer: {dur_min} min",
        f"- Distanz: {w.distance_km or '?'} km",
        f"- Pace: {w.pace or '?'}",
        f"- HF Ø/Max/Min: {w.hr_avg or '?'}/{w.hr_max or '?'}/{w.hr_min or '?'} bpm",
        f"- Kadenz: {w.cadence_avg or '?'} spm",
        f"- RPE: {w.rpe or 'nicht angegeben'}",
    ]

    # Hoehenmeter aus GPS-Track
    if w.gps_track_json:
        try:
            track = json.loads(str(w.gps_track_json))
            ascent = track.get("total_ascent_m")
            descent = track.get("total_descent_m")
            if ascent is not None or descent is not None:
                a = f"{ascent:.0f}" if ascent is not None else "?"
                d = f"{descent:.0f}" if descent is not None else "?"
                lines.append(f"- Hoehenmeter: ↑{a}m ↓{d}m")
        except json.JSONDecodeError:
            pass

    # Notizen
    if w.notes:
        lines.append(f"- Notizen: {w.notes}")

    return "\n".join(lines)


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
        tt = h.get("training_type") or ""
        hr_avg = f"HFØ{h['hr_avg']}" if h.get("hr_avg") else ""
        rpe = f"RPE:{h['rpe']}" if h.get("rpe") else ""

        parts = [p for p in [dur, dist, pace, hr_avg, rpe] if p]
        type_label = f"{h['type']}"
        if tt:
            type_label += f" ({tt})"
        lines.append(f"- {h['date']}: {type_label} — {' '.join(parts)}")
    return "\n".join(lines)


def _build_goal_section(goal: dict) -> str:
    """Wettkampfziel."""
    return f"""## Wettkampfziel
- {goal["title"]} am {goal["date"]}
- Distanz: {goal["distance_km"]} km
- Zielzeit: {goal.get("target_time_min", "?")} min
- Zielpace: {goal.get("target_pace", "?")} min/km"""


def _build_planned_section(planned: dict) -> str:
    """Geplante Session fuer Soll/Ist-Vergleich — vollstaendig."""
    lines = ["## Geplante Session (Soll)"]

    # Typ und Run-Type
    training_type = planned.get("training_type", "?")
    run_type = planned.get("run_type")
    if run_type:
        lines.append(f"- Typ: {training_type}, Laufart: {run_type}")
    else:
        lines.append(f"- Typ: {training_type}")

    # Top-Level Zielwerte
    if planned.get("target_duration_minutes"):
        lines.append(f"- Zieldauer: {planned['target_duration_minutes']} min")

    pace_parts = []
    if planned.get("target_pace_min"):
        pace_parts.append(planned["target_pace_min"])
    if planned.get("target_pace_max"):
        pace_parts.append(planned["target_pace_max"])
    if pace_parts:
        lines.append(f"- Zielpace: {' – '.join(pace_parts)} min/km")

    hr_parts = []
    if planned.get("target_hr_min"):
        hr_parts.append(str(planned["target_hr_min"]))
    if planned.get("target_hr_max"):
        hr_parts.append(str(planned["target_hr_max"]))
    if hr_parts:
        lines.append(f"- Ziel-HF: {' – '.join(hr_parts)} bpm")

    # Notizen
    if planned.get("notes"):
        lines.append(f"- Hinweis: {planned['notes']}")

    # Segmente (Lauf)
    if planned.get("segments"):
        lines.extend(_build_segment_table(planned["segments"]))

    # Uebungen (Kraft)
    if planned.get("exercises"):
        lines.extend(_build_exercises_list(planned["exercises"]))

    return "\n".join(lines)


def _build_segment_table(segments: list[dict]) -> list[str]:
    """Segment-Tabelle mit allen Feldern."""
    lines = [
        "- Segmente:",
        "  | # | Typ | Dauer | Distanz | Pace | HF-Ziel | Wdh |",
        "  |---|-----|-------|---------|------|---------|-----|",
    ]
    for seg in segments:
        pos = seg.get("position", "?")
        typ = seg.get("segment_type") or seg.get("type", "?")
        dur = (
            f"{seg.get('target_duration_minutes', '')}min"
            if seg.get("target_duration_minutes")
            else "-"
        )
        dist = f"{seg.get('target_distance_km', '')}km" if seg.get("target_distance_km") else "-"

        pace_parts = []
        if seg.get("target_pace_min"):
            pace_parts.append(seg["target_pace_min"])
        if seg.get("target_pace_max"):
            pace_parts.append(seg["target_pace_max"])
        pace = " – ".join(pace_parts) if pace_parts else "-"

        hr_parts = []
        if seg.get("target_hr_min"):
            hr_parts.append(str(seg["target_hr_min"]))
        if seg.get("target_hr_max"):
            hr_parts.append(str(seg["target_hr_max"]))
        hr = " – ".join(hr_parts) if hr_parts else "-"

        repeats = str(seg.get("repeats", 1)) if seg.get("repeats", 1) > 1 else "-"

        lines.append(f"  | {pos} | {typ} | {dur} | {dist} | {pace} | {hr} | {repeats} |")
    return lines


def _build_exercises_list(exercises: list[dict]) -> list[str]:
    """Uebungsliste fuer Kraft-Sessions."""
    lines = ["- Uebungen:"]
    for ex in exercises:
        name = ex.get("name", "?")
        category = ex.get("category", "")
        sets = ex.get("sets", "?")
        reps = ex.get("reps", "?")
        weight = ex.get("weight_kg")
        weight_str = f" @ {weight}kg" if weight else ""
        lines.append(f"  - {name} ({category}): {sets}×{reps}{weight_str}")
    return lines


def _build_instructions() -> str:
    """Anweisungen fuer die KI."""
    return """## Anweisungen
Analysiere diese Trainingseinheit. Antworte NUR mit validem JSON (ohne Markdown-Codeblock):

{
  "summary": "2-3 Saetze Gesamtbewertung der Einheit",
  "intensity_rating": "leicht|moderat|intensiv|zu_intensiv",
  "intensity_text": "Kurze Begruendung der Intensitaetsbewertung",
  "hr_zone_assessment": "Bewertung der HF-Zonen-Verteilung im Kontext des Trainingstyps",
  "plan_comparison": "Soll/Ist-Vergleich (null wenn kein Plan vorhanden)",
  "fatigue_indicators": "Ermuedungs-Hinweise (null wenn keine erkennbar)",
  "recommendations": ["Empfehlung 1", "Empfehlung 2", "Empfehlung 3"]
}

Regeln:
- Sachlich, konkret, auf Deutsch
- 2-4 Empfehlungen
- intensity_rating MUSS einer der 4 Werte sein
- Wenn kein Plan vorhanden: plan_comparison = null
- Wenn keine Ermuedung erkennbar: fatigue_indicators = null"""


def _parse_analysis_json(raw: str, session_id: int, provider: str) -> SessionAnalysisResponse:
    """Parst die AI-Antwort als JSON, mit Fallback bei ungueltigem Format."""
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
            hr_zone_assessment="Keine strukturierte Bewertung verfuegbar.",
            recommendations=["Analyse erneut durchfuehren fuer detaillierte Ergebnisse."],
        )
