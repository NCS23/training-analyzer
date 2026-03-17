"""Service: Konvertiert KI-Review-Empfehlungen in strukturierte Plan-Sessions.

Nimmt Freitext-Empfehlungen aus dem Wochen-Review und konvertiert sie via
KI-Call in strukturierte WeeklyPlanEntry-Objekte, die in den Wochenplan
der Folgewoche eingefügt werden können.
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
    """Konvertiert Empfehlungen in Plan-Sessions für die Folgewoche.

    Returns dict with: target_week_start, entries (list[WeeklyPlanEntry]), applied_count.
    """
    target_week = review_week_start + timedelta(days=7)

    # Bestehenden Plan laden
    existing = await _load_existing_entries(target_week, db)

    # Kontext laden
    templates = await _load_strength_templates(db)
    race_goal = await _load_race_goal(db)

    # Prompt bauen und KI aufrufen
    system_prompt = _build_system_prompt(race_goal, target_week)
    user_prompt = _build_user_prompt(recommendations, existing, templates)
    api_key = await resolve_claude_api_key(db)

    t0 = time.monotonic()
    raw = await ai_service.chat(user_prompt, {"system_prompt": system_prompt}, api_key)
    duration_ms = int((time.monotonic() - t0) * 1000)
    provider = ai_service.get_active_provider() or "unknown"

    # Parsen und mergen
    new_sessions = _parse_sessions(raw)
    merged = _merge_into_plan(existing, new_sessions)

    # Neue Sessions in DB persistieren
    await _persist_new_sessions(target_week, existing, new_sessions, db)

    # Log
    await log_ai_call(
        db,
        AICallData(
            use_case="apply_recommendations",
            provider=provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            raw_response=raw,
            parsed_ok=len(new_sessions) > 0,
            duration_ms=duration_ms,
        ),
    )
    await db.commit()

    return {
        "target_week_start": str(target_week),
        "entries": [e.model_dump() for e in merged],
        "applied_count": len(new_sessions),
    }


# ---------------------------------------------------------------------------
# Kontext laden
# ---------------------------------------------------------------------------


async def _load_existing_entries(week_start: date, db: AsyncSession) -> list[dict]:
    """Lädt bestehende Plan-Tage als kompakte Dicts."""
    result = await db.execute(
        select(WeeklyPlanDayModel)
        .where(WeeklyPlanDayModel.week_start == week_start)
        .order_by(WeeklyPlanDayModel.day_of_week)
    )
    days = result.scalars().all()
    entries = []
    for d in days:
        entries.append(
            {
                "day_of_week": int(d.day_of_week),
                "is_rest_day": bool(d.is_rest_day),
                "has_sessions": True,  # Vereinfachung — Tag existiert = hat Inhalt
            }
        )
    return entries


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
    """System-Prompt für Empfehlungs-Konvertierung."""
    parts = [
        "Du bist ein Trainingsplaner.",
        "Deine Aufgabe: Konvertiere natürlichsprachige Trainingsempfehlungen in "
        "strukturierte Plan-Sessions (JSON).",
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
    existing: list[dict],
    templates: list[dict],
) -> str:
    """User-Prompt mit Empfehlungen und Kontext."""
    parts: list[str] = []

    parts.append("## Empfehlungen zum Konvertieren")
    for i, rec in enumerate(recommendations, 1):
        parts.append(f"{i}. {rec}")

    # Belegte Tage
    if existing:
        parts.append("")
        parts.append("## Bereits belegte Tage (NICHT belegen)")
        for e in existing:
            day_name = DAY_NAMES[e["day_of_week"]]
            status = "Ruhetag" if e["is_rest_day"] else "hat Sessions"
            parts.append(f"- {day_name} ({status})")

    # Freie Tage
    occupied = {e["day_of_week"] for e in existing}
    free_days = [DAY_NAMES[d] for d in range(7) if d not in occupied]
    if free_days:
        parts.append("")
        parts.append(f"## Freie Tage: {', '.join(free_days)}")

    # Kraft-Templates
    if templates:
        parts.append("")
        parts.append("## Verfügbare Kraft-Templates")
        for t in templates:
            parts.append(f"- ID {t['id']}: {t['name']}")

    parts.append("")
    parts.append(_build_instructions())

    return "\n".join(parts)


def _build_instructions() -> str:
    """JSON-Anweisungen."""
    return """## Anweisungen
Konvertiere die Empfehlungen in Plan-Sessions. Antworte NUR mit einem JSON-Array (ohne Markdown-Codeblock):

[
  {
    "day_of_week": 0,
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
- day_of_week: 0=Montag bis 6=Sonntag — NUR freie Tage verwenden
- training_type: "running" oder "strength"
- Bei Lauf: run_details mit run_type (aus der gültigen Liste), Dauer, Pace
- Bei Kraft: template_id setzen falls passend, sonst weglassen
- notes: Kurze Erklärung der Empfehlung
- Pace im Format "M:SS" (z.B. "5:30")
- target_pace_min = schnellere Pace, target_pace_max = langsamere Pace
- Ignoriere Empfehlungen die keine konkreten Sessions sind (z.B. "mehr schlafen")
- Maximal eine Session pro Tag"""


# ---------------------------------------------------------------------------
# JSON-Parsing
# ---------------------------------------------------------------------------


def _parse_sessions(raw: str) -> list[dict]:
    """Parst KI-Antwort als JSON-Array von Sessions."""
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
        session = _normalize_session(item)
        if session:
            valid.append(session)

    return valid


def _parse_run_details_from_ai(rd_raw: object) -> dict:
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


def _normalize_session(item: dict) -> dict | None:
    """Normalisiert und validiert eine einzelne Session."""
    day = item.get("day_of_week")
    if not isinstance(day, int) or day < 0 or day > 6:
        return None

    training_type = str(item.get("training_type", "")).lower()
    if training_type not in ("running", "strength"):
        return None

    result: dict = {
        "day_of_week": day,
        "training_type": training_type,
    }

    if item.get("notes"):
        result["notes"] = str(item["notes"])[:500]

    if training_type == "running":
        result["run_details"] = _parse_run_details_from_ai(item.get("run_details", {}))

    if training_type == "strength" and item.get("template_id"):
        with contextlib.suppress(ValueError, TypeError):
            result["template_id"] = int(item["template_id"])

    return result


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------


def _merge_into_plan(
    existing: list[dict],
    new_sessions: list[dict],
) -> list[WeeklyPlanEntry]:
    """Merged neue Sessions in den bestehenden 7-Tage-Plan."""
    occupied = {e["day_of_week"] for e in existing}

    # Bestehende Tage als Entries (mit is_rest_day)
    existing_map: dict[int, dict] = {e["day_of_week"]: e for e in existing}

    # Neue Sessions einfügen (nur auf freie Tage)
    new_by_day: dict[int, dict] = {}
    for s in new_sessions:
        day = s["day_of_week"]
        if day in occupied:
            # Freien Tag suchen
            day = _find_free_day(occupied | set(new_by_day.keys()), day)
            if day is None:
                continue
        new_by_day[day] = s

    # 7-Tage-Plan bauen
    entries: list[WeeklyPlanEntry] = []
    for dow in range(7):
        if dow in existing_map:
            # Bestehender Tag — unverändert lassen (leerer Platzhalter)
            e = existing_map[dow]
            entries.append(
                WeeklyPlanEntry(
                    day_of_week=dow,
                    is_rest_day=e.get("is_rest_day", False),
                )
            )
        elif dow in new_by_day:
            s = new_by_day[dow]
            sessions = [_dict_to_planned_session(s, position=0)]
            entries.append(
                WeeklyPlanEntry(
                    day_of_week=dow,
                    sessions=sessions,
                )
            )
        else:
            entries.append(WeeklyPlanEntry(day_of_week=dow))

    return entries


async def _persist_new_sessions(
    target_week: date,
    existing: list[dict],
    new_sessions: list[dict],
    db: AsyncSession,
) -> None:
    """Persistiert neue KI-Sessions als WeeklyPlanDay + PlannedSession in der DB."""
    occupied = {e["day_of_week"] for e in existing}

    # Welche Tage wurden tatsächlich belegt? (gleiche Logik wie _merge_into_plan)
    placed: dict[int, dict] = {}
    for s in new_sessions:
        day = s["day_of_week"]
        if day in occupied or day in placed:
            day = _find_free_day(occupied | set(placed.keys()), day)
            if day is None:
                continue
        placed[day] = s

    for day, session_data in placed.items():
        db_day = WeeklyPlanDayModel(
            week_start=target_week,
            day_of_week=day,
            is_rest_day=False,
        )
        db.add(db_day)
        await db.flush()

        run_details_str: str | None = None
        if session_data.get("run_details"):
            run_details_str = json.dumps(session_data["run_details"])

        db_session = PlannedSessionModel(
            day_id=db_day.id,
            position=0,
            training_type=session_data["training_type"],
            template_id=session_data.get("template_id"),
            run_details_json=run_details_str,
            notes=session_data.get("notes"),
        )
        db.add(db_session)


def _find_free_day(occupied: set[int], preferred: int) -> int | None:
    """Sucht den nächsten freien Tag ab preferred."""
    for offset in range(1, 7):
        candidate = (preferred + offset) % 7
        if candidate not in occupied:
            return candidate
    return None


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
