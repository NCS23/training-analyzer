"""Service: Passt den bestehenden Wochenplan anhand von KI-Review-Empfehlungen an.

Nimmt Freitext-Empfehlungen aus dem Wochen-Review und lässt die KI den
bestehenden Plan der Folgewoche entsprechend anpassen — Sessions werden
modifiziert, hinzugefügt oder entfernt. Änderungen werden bidirektional
in den Trainingsplan zurück-synchronisiert.
"""

import contextlib
import json
import logging
import time
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key_resolver import resolve_claude_api_key
from app.infrastructure.ai.ai_service import ai_service
from app.infrastructure.database.models import (
    PlanChangeLogModel,
    PlannedSessionModel,
    RaceGoalModel,
    SessionTemplateModel,
    TrainingPhaseModel,
    TrainingPlanModel,
    WeeklyPlanDayModel,
)
from app.models.taxonomy import SEGMENT_TYPES, SESSION_TYPES
from app.models.weekly_plan import PlannedSession, RunDetails, WeeklyPlanEntry
from app.services.ai_log_service import AICallData, log_ai_call

logger = logging.getLogger(__name__)

VALID_RUN_TYPES = sorted(SESSION_TYPES)
VALID_SEGMENT_TYPES = sorted(SEGMENT_TYPES)
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

    # plan_id für Sync extrahieren
    plan_id = _extract_plan_id(existing_plan)

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

    # Sync zurück zum Trainingsplan + Changelog
    if ai_days and plan_id:
        await _sync_back_to_plan(target_week, plan_id, ai_days, db)
        _log_recommendation_change(
            plan_id, target_week, recommendations, existing_plan, ai_days, db
        )

    # AI-Log
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


def _extract_plan_id(existing_plan: list[dict]) -> int | None:
    """Extrahiert die plan_id aus dem bestehenden Plan."""
    for e in existing_plan:
        if e.get("plan_id"):
            return int(e["plan_id"])
    return None


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
            sess: dict = {"training_type": s.training_type, "notes": s.notes}
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
        "Gültige Intervall-Segment-Typen:",
        ", ".join(VALID_SEGMENT_TYPES),
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

    # Bestehender Plan mit vollen Details
    parts.append("## Aktueller Plan der Zielwoche")
    if existing_plan:
        for e in existing_plan:
            day_name = DAY_NAMES[e["day_of_week"]]
            parts.extend(_format_plan_day(day_name, e))
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


def _format_plan_day(day_name: str, entry: dict) -> list[str]:
    """Formatiert einen Plan-Tag mit vollen Session-Details für den Prompt."""
    if entry["is_rest_day"]:
        return [f"- {day_name}: Ruhetag"]

    sessions = entry.get("sessions", [])
    if not sessions:
        return [f"- {day_name}: (leer)"]

    lines: list[str] = []
    for s in sessions:
        tt = s.get("training_type", "?")
        rd = s.get("run_details") or {}
        rt = rd.get("run_type", "")
        dur = rd.get("target_duration_minutes", "")
        desc = f"{tt}"
        if rt:
            desc += f" ({rt})"
        if dur:
            desc += f" {dur}min"

        day_notes = entry.get("notes", "") or ""
        line = f"- {day_name}: {desc}"
        if day_notes:
            line += f" — {day_notes[:80]}"
        lines.append(line)

        # Intervall-Details anzeigen
        intervals = rd.get("intervals", [])
        if intervals:
            lines.extend(_format_intervals(intervals))

    return lines


def _format_intervals(intervals: list[dict]) -> list[str]:
    """Formatiert Intervalle als eingerückte Zeilen für den Prompt."""
    lines: list[str] = []
    for iv in intervals:
        seg_type = iv.get("type", "?")
        dur = iv.get("duration_minutes", "")
        repeats = iv.get("repeats", 1)
        pace_min = iv.get("target_pace_min", "")
        pace_max = iv.get("target_pace_max", "")

        desc = f"    {seg_type}"
        if dur:
            desc += f" {dur}min"
        if repeats and repeats > 1:
            desc += f" x{repeats}"
        if pace_min and pace_max:
            desc += f" @{pace_min}-{pace_max}"
        elif pace_min:
            desc += f" @{pace_min}"
        lines.append(desc)
    return lines


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
      "run_type": "intervals",
      "target_duration_minutes": 30,
      "intervals": [
        {"type": "warmup", "duration_minutes": 7, "target_pace_min": "7:00", "target_pace_max": "7:20", "repeats": 1},
        {"type": "work", "duration_minutes": 2, "target_pace_min": "5:55", "target_pace_max": "6:05", "repeats": 3},
        {"type": "recovery_jog", "duration_minutes": 2, "target_pace_min": "7:00", "target_pace_max": "7:30", "repeats": 3},
        {"type": "cooldown", "duration_minutes": 5, "target_pace_min": "7:00", "target_pace_max": "7:20", "repeats": 1}
      ]
    },
    "notes": "Kurze Aktivierung mit Wettkampftempo-Abschnitten"
  },
  {
    "day_of_week": 2,
    "training_type": "running",
    "run_details": {
      "run_type": "easy",
      "target_duration_minutes": 35,
      "target_pace_min": "6:45",
      "target_pace_max": "7:15",
      "intervals": [
        {"type": "steady", "duration_minutes": 35, "target_pace_min": "6:45", "target_pace_max": "7:15", "repeats": 1}
      ]
    },
    "notes": "Lockerer Lauf"
  }
]

Regeln:
- Gib ALLE 7 Tage zurück (day_of_week 0-6), auch Ruhetage
- Ruhetage: nur day_of_week + is_rest_day: true
- Trainingstage: training_type + run_details/template_id + notes
- Passe bestehende Sessions an (Umfang, Pace, Dauer, Typ), entferne oder füge hinzu
- Behalte die Grundstruktur bei, wenn die Empfehlungen keine Änderung erfordern
- Bei Lauf: run_details mit run_type, Dauer, Pace UND intervals-Array
- intervals: IMMER angeben bei Lauf-Sessions — auch bei einfachen Läufen (ein "steady"-Segment)
- Intervall-Typen: warmup, cooldown, steady, work, recovery_jog, rest, strides, drills
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
    """Parst run_details inkl. intervals aus der KI-Antwort."""
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

    # Intervalle parsen
    raw_intervals = rd_raw.get("intervals")
    if isinstance(raw_intervals, list):
        intervals = [_parse_interval(iv) for iv in raw_intervals if isinstance(iv, dict)]
        if intervals:
            details["intervals"] = intervals

    return details


def _parse_interval(iv: dict) -> dict:
    """Parst ein einzelnes Intervall-Segment."""
    seg_type = str(iv.get("type", "steady")).lower()
    if seg_type not in SEGMENT_TYPES:
        seg_type = "steady"

    interval: dict = {
        "type": seg_type,
        "repeats": max(1, int(iv.get("repeats", 1) or 1)),
    }

    if iv.get("duration_minutes"):
        with contextlib.suppress(ValueError, TypeError):
            interval["duration_minutes"] = float(iv["duration_minutes"])
    if iv.get("target_pace_min"):
        interval["target_pace_min"] = str(iv["target_pace_min"])
    if iv.get("target_pace_max"):
        interval["target_pace_max"] = str(iv["target_pace_max"])

    return interval


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

    plan_id = _extract_plan_id(existing_plan)

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
        edited=True,
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


# ---------------------------------------------------------------------------
# Trainingsplan-Sync + Changelog
# ---------------------------------------------------------------------------


async def _sync_back_to_plan(
    target_week: date,
    plan_id: int,
    ai_days: list[dict],
    db: AsyncSession,
) -> None:
    """Synchronisiert die Änderungen zurück in den Trainingsplan (Phase-Template)."""
    plan = await db.get(TrainingPlanModel, plan_id)
    if not plan:
        return

    # Wochennummer berechnen (1-indexed)
    plan_start = plan.start_date
    plan_start_monday = plan_start - timedelta(days=plan_start.weekday())
    week_number = ((target_week - plan_start_monday).days // 7) + 1

    # Phase finden
    result = await db.execute(
        select(TrainingPhaseModel).where(
            TrainingPhaseModel.training_plan_id == plan_id,
            TrainingPhaseModel.start_week <= week_number,
            TrainingPhaseModel.end_week >= week_number,
        )
    )
    phase = result.scalar_one_or_none()
    if not phase:
        return

    # Week-Key berechnen (1-indexed innerhalb der Phase)
    week_in_phase = week_number - phase.start_week
    week_key = str(week_in_phase + 1)

    # Template aus KI-Tagen bauen
    template = _build_phase_template(ai_days)

    # Per-Week Override aktualisieren
    existing: dict = {}
    if phase.weekly_templates_json:
        with contextlib.suppress(json.JSONDecodeError):
            existing = json.loads(phase.weekly_templates_json)

    weeks = existing.get("weeks", {})
    weeks[week_key] = template
    phase.weekly_templates_json = json.dumps({"weeks": weeks})


def _build_phase_template(ai_days: list[dict]) -> dict:
    """Baut ein PhaseWeeklyTemplate-Dict aus den KI-Tagen."""
    day_map = {d["day_of_week"]: d for d in ai_days}

    days: list[dict] = []
    for dow in range(7):
        d = day_map.get(dow)
        if not d or d.get("is_rest_day"):
            days.append(
                {
                    "day_of_week": dow,
                    "sessions": [],
                    "is_rest_day": True,
                    "notes": None,
                }
            )
            continue

        rd = d.get("run_details")
        session: dict = {
            "position": 0,
            "training_type": d["training_type"],
            "run_type": rd.get("run_type") if rd else None,
            "template_id": d.get("template_id"),
            "template_name": None,
            "run_details": rd,
            "exercises": None,
            "notes": d.get("notes"),
        }
        days.append(
            {
                "day_of_week": dow,
                "sessions": [session],
                "is_rest_day": False,
                "notes": d.get("notes"),
            }
        )

    return {"days": days}


def _log_recommendation_change(
    plan_id: int,
    target_week: date,
    recommendations: list[str],
    old_plan: list[dict],
    new_days: list[dict],
    db: AsyncSession,
) -> None:
    """Erstellt einen detaillierten Changelog-Eintrag im Trainingsplan."""
    changed_days = _diff_plans(old_plan, new_days)
    change_count = len(changed_days)

    summary = (
        f"Wochenplan {target_week}: {change_count} "
        f"{'Tag' if change_count == 1 else 'Tage'} per KI-Empfehlung angepasst"
    )
    reason = "; ".join(recommendations[:10])

    details = {
        "category": "content",
        "source": "ai_recommendation",
        "week_start": str(target_week),
        "changed_days": changed_days,
    }

    entry = PlanChangeLogModel(
        plan_id=plan_id,
        change_type="back_sync",
        category="content",
        summary=summary,
        details_json=json.dumps(details),
        reason=reason,
        created_at=datetime.utcnow(),
    )
    db.add(entry)


def _diff_plans(old_plan: list[dict], new_days: list[dict]) -> list[dict]:
    """Vergleicht alten und neuen Plan und gibt geänderte Tage zurück."""
    old_map = {e["day_of_week"]: e for e in old_plan}
    new_map = {d["day_of_week"]: d for d in new_days}

    changed: list[dict] = []
    for dow in range(7):
        old = old_map.get(dow)
        new = new_map.get(dow)
        if not new:
            continue

        day_changes = _diff_day(old, new)
        if day_changes:
            changed.append(
                {
                    "day_of_week": dow,
                    "day_name": DAY_NAMES[dow],
                    "field_changes": day_changes,
                }
            )

    return changed


_FIELD_LABELS: dict[str, str] = {
    "is_rest_day": "Ruhetag",
    "training_type": "Trainingstyp",
    "run_type": "Lauftyp",
    "target_duration_minutes": "Dauer (Ziel)",
    "target_pace_min": "Ziel-Pace (schnell)",
    "target_pace_max": "Ziel-Pace (langsam)",
    "notes": "Notizen",
    "intervals": "Intervalle",
}


def _diff_day(old: dict | None, new: dict) -> list[dict]:
    """Vergleicht einen einzelnen Tag (alt vs. neu) und gibt Feld-Änderungen zurück."""
    changes: list[dict] = []

    def _add(field: str, from_val: object, to_val: object) -> None:
        if from_val != to_val:
            changes.append(
                {
                    "field": field,
                    "from": from_val,
                    "to": to_val,
                    "label": _FIELD_LABELS.get(field, field),
                }
            )

    # Ruhetag-Status
    old_rest = old.get("is_rest_day", True) if old else True
    new_rest = new.get("is_rest_day", False)
    _add("is_rest_day", old_rest, new_rest)

    # Session-Details vergleichen
    old_session = _extract_session(old) if old else {}
    new_session = _extract_session(new) if not new_rest else {}

    _add("training_type", old_session.get("training_type"), new_session.get("training_type"))

    old_rd = old_session.get("run_details") or {}
    new_rd = new_session.get("run_details") or {}

    for field in ("run_type", "target_duration_minutes", "target_pace_min", "target_pace_max"):
        _add(field, old_rd.get(field), new_rd.get(field))

    # Intervalle: Kurzform vergleichen
    old_iv = _summarize_intervals(old_rd.get("intervals", []))
    new_iv = _summarize_intervals(new_rd.get("intervals", []))
    _add("intervals", old_iv, new_iv)

    return changes


def _extract_session(day: dict) -> dict:
    """Extrahiert die erste Session eines Tages als flaches Dict."""
    sessions = day.get("sessions", [])
    if not sessions:
        return {}
    return sessions[0] if isinstance(sessions[0], dict) else {}


def _summarize_intervals(intervals: list) -> str | None:
    """Erstellt eine Kurzform der Intervalle für den Diff."""
    if not intervals:
        return None
    parts: list[str] = []
    for iv in intervals:
        seg = iv.get("type", "?")
        dur = iv.get("duration_minutes", "")
        rep = iv.get("repeats", 1)
        desc = seg
        if dur:
            desc += f" {dur}min"
        if rep and rep > 1:
            desc += f" x{rep}"
        parts.append(desc)
    return " → ".join(parts)
