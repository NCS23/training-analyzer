"""Service: Passt den bestehenden Wochenplan anhand von KI-Review-Empfehlungen an.

Nimmt Freitext-Empfehlungen aus dem Wochen-Review und lässt die KI den
bestehenden Plan der Folgewoche entsprechend anpassen — Sessions werden
modifiziert, hinzugefügt oder entfernt.
"""

import contextlib
import json
import logging
import time
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key_resolver import resolve_claude_api_key
from app.infrastructure.ai.ai_service import ai_service
from app.infrastructure.database.models import (
    PlannedSessionModel,
    RaceGoalModel,
    SessionTemplateModel,
    WeeklyPlanDayModel,
)
from app.models.taxonomy import SESSION_TYPES
from app.models.weekly_plan import PlannedSession, RunDetails, WeeklyPlanEntry
from app.services.ai_log_service import AICallData, log_ai_call

logger = logging.getLogger(__name__)

VALID_RUN_TYPES = sorted(SESSION_TYPES)
DAY_NAMES = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


async def apply_recommendations(
    review_week_start: date,
    recommendations: list[str],
    db: AsyncSession,
) -> dict:
    """Passt den Plan der Folgewoche anhand von Empfehlungen an.

    Returns dict with: target_week_start, entries (list[WeeklyPlanEntry]), applied_count.
    """
    target_week = review_week_start + timedelta(days=7)

    # Bestehenden Plan mit vollen Details laden
    existing_plan = await _load_full_plan(target_week, db)

    # Kontext laden
    templates = await _load_strength_templates(db)
    race_goal = await _load_race_goal(db)

    # Prompt bauen und KI aufrufen
    system_prompt = _build_system_prompt(race_goal, target_week)
    user_prompt = _build_user_prompt(recommendations, existing_plan, templates)
    api_key = await resolve_claude_api_key(db)

    t0 = time.monotonic()
    raw = await ai_service.chat(user_prompt, {"system_prompt": system_prompt}, api_key)
    duration_ms = int((time.monotonic() - t0) * 1000)
    provider = ai_service.get_active_provider() or "unknown"

    # KI-Antwort parsen → vollständiger 7-Tage-Plan
    ai_days = _parse_plan(raw)
    entries = _build_entries(ai_days)

    # Bestehende Einträge löschen und neue persistieren
    if ai_days:
        await _replace_plan(target_week, existing_plan, ai_days, db)

    # Log
    await log_ai_call(
        db,
        AICallData(
            use_case="apply_recommendations",
            provider=provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            raw_response=raw,
            parsed_ok=len(ai_days) > 0,
            duration_ms=duration_ms,
        ),
    )
    await db.commit()

    return {
        "target_week_start": str(target_week),
        "entries": [e.model_dump() for e in entries],
        "applied_count": len([d for d in ai_days if not d.get("is_rest_day", False)]),
    }


# ---------------------------------------------------------------------------
# Plan laden (mit vollen Session-Details)
# ---------------------------------------------------------------------------


async def _load_full_plan(week_start: date, db: AsyncSession) -> list[dict]:
    """Lädt den bestehenden Plan mit vollen Session-Details für den KI-Prompt."""
    day_result = await db.execute(
        select(WeeklyPlanDayModel)
        .where(WeeklyPlanDayModel.week_start == week_start)
        .order_by(WeeklyPlanDayModel.day_of_week)
    )
    days = day_result.scalars().all()
    if not days:
        return []

    day_ids = [d.id for d in days]
    session_result = await db.execute(
        select(PlannedSessionModel)
        .where(PlannedSessionModel.day_id.in_(day_ids))
        .order_by(PlannedSessionModel.day_id, PlannedSessionModel.position)
    )
    sessions_by_day: dict[int, list[PlannedSessionModel]] = {}
    for s in session_result.scalars().all():
        sessions_by_day.setdefault(s.day_id, []).append(s)

    plan: list[dict] = []
    for d in days:
        day_sessions = sessions_by_day.get(d.id, [])
        entry: dict = {
            "day_of_week": int(d.day_of_week),
            "is_rest_day": bool(d.is_rest_day),
            "notes": d.notes,
            "plan_id": d.plan_id,
            "sessions": [],
        }
        for s in day_sessions:
            sess: dict = {
                "training_type": s.training_type,
                "notes": s.notes,
            }
            if s.run_details_json:
                with contextlib.suppress(json.JSONDecodeError):
                    sess["run_details"] = json.loads(s.run_details_json)
            if s.template_id:
                sess["template_id"] = s.template_id
            entry["sessions"].append(sess)
        plan.append(entry)

    return plan


async def _load_strength_templates(db: AsyncSession) -> list[dict]:
    """Lädt verfügbare Kraft-Templates (Name + ID)."""
    result = await db.execute(select(SessionTemplateModel.id, SessionTemplateModel.name).limit(20))
    return [{"id": row.id, "name": str(row.name)} for row in result.all()]


async def _load_race_goal(db: AsyncSession) -> dict | None:
    """Lädt das aktive Wettkampfziel."""
    result = await db.execute(
        select(RaceGoalModel).where(RaceGoalModel.is_active.is_(True)).limit(1)
    )
    goal = result.scalar_one_or_none()
    if not goal:
        return None
    return {
        "title": goal.title,
        "date": str(goal.race_date.date() if hasattr(goal.race_date, "date") else goal.race_date),
        "distance_km": goal.distance_km,
    }


# ---------------------------------------------------------------------------
# Prompt-Builder
# ---------------------------------------------------------------------------


def _build_system_prompt(race_goal: dict | None, target_week: date) -> str:
    """System-Prompt für Plan-Anpassung."""
    parts = [
        "Du bist ein erfahrener Trainingsplaner.",
        "Deine Aufgabe: Passe einen bestehenden Wochenplan anhand von Empfehlungen an.",
        "Du gibst den KOMPLETTEN angepassten 7-Tage-Plan als JSON zurück.",
        "",
        "Gültige Lauf-Typen (run_type):",
        ", ".join(VALID_RUN_TYPES),
        "",
        "Trainingstypen (training_type): 'running' oder 'strength'",
        "",
        f"Zielwoche: {target_week.strftime('%d.%m.%Y')} – "
        f"{(target_week + timedelta(days=6)).strftime('%d.%m.%Y')}",
    ]

    if race_goal:
        parts.append("")
        parts.append(f"Wettkampfziel: {race_goal['title']} ({race_goal['distance_km']} km)")
        parts.append(f"Wettkampfdatum: {race_goal['date']}")

    return "\n".join(parts)


def _build_user_prompt(
    recommendations: list[str],
    existing_plan: list[dict],
    templates: list[dict],
) -> str:
    """User-Prompt mit bestehendem Plan und Empfehlungen."""
    parts: list[str] = []

    # Bestehender Plan
    parts.append("## Aktueller Plan der Zielwoche")
    if existing_plan:
        for e in existing_plan:
            day_name = DAY_NAMES[e["day_of_week"]]
            parts.append(_format_plan_day(day_name, e))
    else:
        parts.append("Kein bestehender Plan vorhanden.")

    # Empfehlungen
    parts.append("")
    parts.append("## Empfehlungen zur Anpassung")
    for i, rec in enumerate(recommendations, 1):
        parts.append(f"{i}. {rec}")

    # Kraft-Templates
    if templates:
        parts.append("")
        parts.append("## Verfügbare Kraft-Templates")
        for t in templates:
            parts.append(f"- ID {t['id']}: {t['name']}")

    parts.append("")
    parts.append(_build_instructions())

    return "\n".join(parts)


def _format_plan_day(day_name: str, entry: dict) -> str:
    """Formatiert einen Plan-Tag für den Prompt."""
    if entry["is_rest_day"]:
        return f"- {day_name}: Ruhetag"

    sessions = entry.get("sessions", [])
    if not sessions:
        return f"- {day_name}: (leer)"

    session_parts: list[str] = []
    for s in sessions:
        tt = s.get("training_type", "?")
        rd = s.get("run_details", {})
        rt = rd.get("run_type", "") if rd else ""
        dur = rd.get("target_duration_minutes", "") if rd else ""
        notes = s.get("notes", "") or ""
        desc = f"{tt}"
        if rt:
            desc += f" ({rt})"
        if dur:
            desc += f" {dur}min"
        if notes:
            desc += f" — {notes[:80]}"
        session_parts.append(desc)

    day_notes = entry.get("notes", "") or ""
    line = f"- {day_name}: {'; '.join(session_parts)}"
    if day_notes:
        line += f" | Notiz: {day_notes[:80]}"
    return line


def _build_instructions() -> str:
    """JSON-Anweisungen für die Plan-Anpassung."""
    return """## Anweisungen
Passe den bestehenden Plan gemäß den Empfehlungen an. Antworte NUR mit einem JSON-Array \
(ohne Markdown-Codeblock) für alle 7 Tage (0=Montag bis 6=Sonntag):

[
  {
    "day_of_week": 0,
    "is_rest_day": true
  },
  {
    "day_of_week": 1,
    "training_type": "running",
    "run_details": {
      "run_type": "easy",
      "target_duration_minutes": 45,
      "target_pace_min": "6:30",
      "target_pace_max": "7:00"
    },
    "notes": "Lockerer Lauf zur Erholung"
  }
]

Regeln:
- Gib ALLE 7 Tage zurück (day_of_week 0-6), auch Ruhetage
- Ruhetage: nur day_of_week + is_rest_day: true
- Trainingstage: training_type + run_details/template_id + notes
- Passe bestehende Sessions an (Umfang, Pace, Dauer, Typ), entferne oder füge hinzu
- Behalte die Grundstruktur bei, wenn die Empfehlungen keine Änderung erfordern
- Bei Lauf: run_details mit run_type (aus der gültigen Liste), Dauer, Pace
- Bei Kraft: template_id setzen falls passend, sonst weglassen
- notes: Kurze Erklärung was geändert wurde und warum
- Pace im Format "M:SS" (z.B. "5:30")
- target_pace_min = schnellere Pace, target_pace_max = langsamere Pace
- Maximal eine Session pro Tag"""


# ---------------------------------------------------------------------------
# JSON-Parsing
# ---------------------------------------------------------------------------


def _parse_plan(raw: str) -> list[dict]:
    """Parst KI-Antwort als JSON-Array des kompletten 7-Tage-Plans."""
    text = raw.strip()

    # Markdown-Codeblock entfernen
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Apply-Recommendations JSON konnte nicht geparst werden: %s", text[:200])
        return []

    if not isinstance(data, list):
        return []

    valid: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        day = _normalize_day(item)
        if day:
            valid.append(day)

    return valid


def _normalize_day(item: dict) -> dict | None:
    """Normalisiert und validiert einen einzelnen Tag aus der KI-Antwort."""
    day = item.get("day_of_week")
    if not isinstance(day, int) or day < 0 or day > 6:
        return None

    # Ruhetag
    if item.get("is_rest_day"):
        return {"day_of_week": day, "is_rest_day": True}

    training_type = str(item.get("training_type", "")).lower()
    if training_type not in ("running", "strength"):
        # Wenn kein gültiger training_type → als Ruhetag behandeln
        return {"day_of_week": day, "is_rest_day": True}

    result: dict = {
        "day_of_week": day,
        "is_rest_day": False,
        "training_type": training_type,
    }

    if item.get("notes"):
        result["notes"] = str(item["notes"])[:500]

    if training_type == "running":
        result["run_details"] = _parse_run_details(item.get("run_details", {}))

    if training_type == "strength" and item.get("template_id"):
        with contextlib.suppress(ValueError, TypeError):
            result["template_id"] = int(item["template_id"])

    return result


def _parse_run_details(rd_raw: object) -> dict:
    """Parst run_details aus der KI-Antwort."""
    if not isinstance(rd_raw, dict):
        return {"run_type": "easy"}

    run_type = str(rd_raw.get("run_type", "easy")).lower()
    if run_type not in SESSION_TYPES:
        run_type = "easy"

    details: dict = {"run_type": run_type}
    if rd_raw.get("target_duration_minutes"):
        dur = int(rd_raw["target_duration_minutes"])
        if 5 <= dur <= 360:
            details["target_duration_minutes"] = dur
    if rd_raw.get("target_pace_min"):
        details["target_pace_min"] = str(rd_raw["target_pace_min"])
    if rd_raw.get("target_pace_max"):
        details["target_pace_max"] = str(rd_raw["target_pace_max"])

    return details


# ---------------------------------------------------------------------------
# Entries bauen + DB-Persistierung
# ---------------------------------------------------------------------------


def _build_entries(ai_days: list[dict]) -> list[WeeklyPlanEntry]:
    """Baut WeeklyPlanEntry-Objekte aus den KI-Tagen."""
    day_map = {d["day_of_week"]: d for d in ai_days}

    entries: list[WeeklyPlanEntry] = []
    for dow in range(7):
        if dow in day_map:
            d = day_map[dow]
            if d.get("is_rest_day"):
                entries.append(WeeklyPlanEntry(day_of_week=dow, is_rest_day=True))
            else:
                session = _dict_to_planned_session(d, position=0)
                entries.append(WeeklyPlanEntry(day_of_week=dow, sessions=[session]))
        else:
            entries.append(WeeklyPlanEntry(day_of_week=dow))

    return entries


async def _replace_plan(
    target_week: date,
    existing_plan: list[dict],
    ai_days: list[dict],
    db: AsyncSession,
) -> None:
    """Löscht bestehende Einträge und erstellt den angepassten Plan."""
    # Bestehende Tage + Sessions löschen
    day_result = await db.execute(
        select(WeeklyPlanDayModel).where(WeeklyPlanDayModel.week_start == target_week)
    )
    old_days = day_result.scalars().all()

    if old_days:
        old_day_ids = [d.id for d in old_days]
        session_result = await db.execute(
            select(PlannedSessionModel).where(PlannedSessionModel.day_id.in_(old_day_ids))
        )
        for s in session_result.scalars().all():
            await db.delete(s)

    # plan_id aus bestehendem Plan übernehmen (falls vorhanden)
    plan_id = None
    for e in existing_plan:
        if e.get("plan_id"):
            plan_id = e["plan_id"]
            break

    # Alte Days löschen (nach Sessions!)
    for d in old_days:
        await db.delete(d)
    await db.flush()

    # Neue Tage + Sessions erstellen
    for ai_day in ai_days:
        await _create_plan_day(target_week, ai_day, plan_id, db)


async def _create_plan_day(
    target_week: date,
    ai_day: dict,
    plan_id: int | None,
    db: AsyncSession,
) -> None:
    """Erstellt einen einzelnen Plan-Tag mit Session in der DB."""
    is_rest = ai_day.get("is_rest_day", False)

    db_day = WeeklyPlanDayModel(
        week_start=target_week,
        day_of_week=ai_day["day_of_week"],
        is_rest_day=is_rest,
        notes=ai_day.get("notes"),
        plan_id=plan_id,
        edited=True,  # KI-Anpassung = editiert
    )
    db.add(db_day)
    await db.flush()

    if is_rest or "training_type" not in ai_day:
        return

    run_details_str: str | None = None
    if ai_day.get("run_details"):
        run_details_str = json.dumps(ai_day["run_details"])

    db_session = PlannedSessionModel(
        day_id=db_day.id,
        position=0,
        training_type=ai_day["training_type"],
        template_id=ai_day.get("template_id"),
        run_details_json=run_details_str,
        notes=ai_day.get("notes"),
    )
    db.add(db_session)


def _dict_to_planned_session(s: dict, position: int) -> PlannedSession:
    """Konvertiert ein normalisiertes Dict in ein PlannedSession-Objekt."""
    rd = None
    if s.get("run_details"):
        rd = RunDetails(**s["run_details"])

    return PlannedSession(
        position=position,
        training_type=s["training_type"],
        template_id=s.get("template_id"),
        notes=s.get("notes"),
        run_details=rd,
    )
