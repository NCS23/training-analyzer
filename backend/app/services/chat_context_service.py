"""Chat Context Service — Baut den Trainingskontext fuer den KI-Chat-Assistenten.

Laedt Athleten-Profil, Wettkampfziel, Trainingsplan, aktuelle Phase,
letzte Sessions und kommende Woche. Nutzt Helpers aus dem Analysis-Service.
"""

import json
import logging
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    AthleteModel,
    PlannedSessionModel,
    RaceGoalModel,
    TrainingPhaseModel,
    TrainingPlanModel,
    WeeklyPlanDayModel,
    WorkoutModel,
)
from app.services.session_analysis_service import (
    _athlete_to_dict,
    _goal_to_dict,
    _workout_to_summary,
)

logger = logging.getLogger(__name__)

WEEKDAYS_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def _german_weekday(d: date) -> str:
    """Gibt den deutschen Wochentag zurueck (ohne locale-Abhaengigkeit)."""
    return WEEKDAYS_DE[d.weekday()]


async def build_chat_system_prompt(db: AsyncSession) -> str:
    """Baut einen vollstaendigen System-Prompt mit Trainingskontext."""
    today = date.today()

    athlete = await _load_athlete(db)
    race_goal = await _load_race_goal(db)
    recent_sessions = await _load_recent_sessions(db, today)
    plan_context = await _load_plan_context(db, today)
    weekly_volume = await _load_weekly_volume(db, today)

    return _assemble_prompt(athlete, race_goal, recent_sessions, plan_context, weekly_volume, today)


async def _load_athlete(db: AsyncSession) -> dict | None:
    result = await db.execute(select(AthleteModel).limit(1))
    model = result.scalar_one_or_none()
    return _athlete_to_dict(model) if model else None


async def _load_race_goal(db: AsyncSession) -> dict | None:
    result = await db.execute(
        select(RaceGoalModel).where(RaceGoalModel.is_active.is_(True)).limit(1)
    )
    model = result.scalar_one_or_none()
    return _goal_to_dict(model) if model else None


async def _load_recent_sessions(db: AsyncSession, today: date) -> list[dict]:
    two_weeks_ago = datetime.combine(today - timedelta(weeks=2), datetime.min.time())
    result = await db.execute(
        select(WorkoutModel)
        .where(WorkoutModel.date >= two_weeks_ago)
        .order_by(WorkoutModel.date.desc())
        .limit(10)
    )
    return [_workout_to_summary(w) for w in result.scalars().all()]


async def _load_plan_context(db: AsyncSession, today: date) -> dict | None:
    """Laedt aktiven Plan, aktuelle Phase und kommende geplante Sessions."""
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
        return None

    # Aktuelle Phase
    weeks_since_start = max(1, (today - plan.start_date).days // 7 + 1)
    phase_result = await db.execute(
        select(TrainingPhaseModel)
        .where(
            TrainingPhaseModel.training_plan_id == plan.id,
            TrainingPhaseModel.start_week <= weeks_since_start,
            TrainingPhaseModel.end_week >= weeks_since_start,
        )
        .limit(1)
    )
    phase = phase_result.scalar_one_or_none()

    # Kommende 7 Tage geplante Sessions
    week_start = today - timedelta(days=today.weekday())
    next_week_end = week_start + timedelta(days=13)
    day_result = await db.execute(
        select(WeeklyPlanDayModel)
        .where(
            WeeklyPlanDayModel.plan_id == plan.id,
            WeeklyPlanDayModel.week_start >= week_start,
            WeeklyPlanDayModel.week_start <= next_week_end,
        )
        .order_by(WeeklyPlanDayModel.week_start, WeeklyPlanDayModel.day_of_week)
    )
    days = day_result.scalars().all()

    upcoming: list[dict] = []
    for day in days:
        actual_date = day.week_start + timedelta(days=day.day_of_week)
        if actual_date < today:
            continue
        if day.is_rest_day:
            upcoming.append({"date": str(actual_date), "type": "Ruhetag"})
            continue
        # Geplante Sessions fuer diesen Tag
        ps_result = await db.execute(
            select(PlannedSessionModel)
            .where(PlannedSessionModel.day_id == day.id, PlannedSessionModel.status == "active")
            .order_by(PlannedSessionModel.position)
        )
        for ps in ps_result.scalars().all():
            entry: dict = {
                "date": str(actual_date),
                "type": str(ps.training_type),
                "notes": str(ps.notes) if ps.notes else None,
            }
            if ps.run_details_json:
                try:
                    rd = json.loads(str(ps.run_details_json))
                    entry["run_type"] = rd.get("run_type")
                    entry["duration_min"] = rd.get("target_duration_minutes")
                except (json.JSONDecodeError, AttributeError):
                    pass
            upcoming.append(entry)

    return {
        "plan_name": plan.name,
        "phase_name": phase.name if phase else None,
        "phase_type": str(phase.phase_type) if phase else None,
        "week": weeks_since_start,
        "upcoming_sessions": upcoming,
    }


async def _load_weekly_volume(db: AsyncSession, today: date) -> dict:
    """Laedt das Wochenvolumen (aktuelle Woche)."""
    week_start = datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
    week_end = datetime.combine(today, datetime.max.time())

    result = await db.execute(
        select(
            func.count(WorkoutModel.id),
            func.sum(WorkoutModel.distance_km),
            func.sum(WorkoutModel.duration_sec),
        ).where(
            WorkoutModel.date >= week_start,
            WorkoutModel.date <= week_end,
        )
    )
    row = result.one()
    return {
        "sessions": row[0] or 0,
        "distance_km": round(row[1], 1) if row[1] else 0,
        "duration_min": round(row[2] / 60) if row[2] else 0,
    }


def _assemble_prompt(
    athlete: dict | None,
    race_goal: dict | None,
    recent_sessions: list[dict],
    plan_context: dict | None,
    weekly_volume: dict,
    today: date,
) -> str:
    """Baut den finalen System-Prompt zusammen."""
    weekday_de = _german_weekday(today)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    parts = [
        "Du bist ein erfahrener Lauf- und Krafttrainer und Trainingsplan-Berater.",
        "Der Athlet nutzt eine Trainings-App und chattet mit dir ueber sein Training.",
        "",
        "## Verhaltensregeln",
        "- Antworte immer auf Deutsch, praegnant, freundlich und kompetent.",
        "- Begruende deine Antworten mit konkreten Daten aus dem Trainingskontext.",
        "- Wenn du Planaenderungen vorschlaegst, sei spezifisch (welcher Tag, welche Session, warum).",
        "- Wiederhole NICHT Informationen aus vorherigen Nachrichten in dieser Konversation.",
        "  Beantworte NUR die aktuelle Frage. Der User kann den Chatverlauf selbst lesen.",
        "- Wochen beginnen IMMER am Montag und enden am Sonntag (ISO 8601 / deutscher Standard).",
        "  Ordne Tage der richtigen Kalenderwoche zu.",
        f"\nHeute ist {weekday_de}, {today.strftime('%d.%m.%Y')}.",
        f"Aktuelle Woche: {week_start.strftime('%d.%m.')} (Mo) – {week_end.strftime('%d.%m.')} (So).",
    ]

    if athlete:
        hr_info = []
        if athlete.get("resting_hr"):
            hr_info.append(f"Ruhe-HF: {athlete['resting_hr']} bpm")
        if athlete.get("max_hr"):
            hr_info.append(f"Max-HF: {athlete['max_hr']} bpm")
        if hr_info:
            parts.append(f"\n## Athlet\n{', '.join(hr_info)}")

    if race_goal:
        parts.append(
            f"\n## Wettkampfziel\n"
            f"- {race_goal['title']}\n"
            f"- Datum: {race_goal['date']}\n"
            f"- Distanz: {race_goal['distance_km']} km\n"
            f"- Zielzeit: {race_goal.get('target_time_min')} min"
            f" ({race_goal.get('target_pace', '?')} min/km)"
        )

    if plan_context:
        phase = (
            f" — Phase: {plan_context['phase_name']} ({plan_context['phase_type']})"
            if plan_context.get("phase_name")
            else ""
        )
        parts.append(
            f"\n## Trainingsplan\n"
            f"- Plan: {plan_context['plan_name']}{phase}\n"
            f"- Woche: {plan_context['week']}"
        )
        if plan_context.get("upcoming_sessions"):
            lines = []
            for s in plan_context["upcoming_sessions"][:7]:
                detail = s.get("run_type") or s["type"]
                dur = f" ({s['duration_min']} min)" if s.get("duration_min") else ""
                s_date = date.fromisoformat(s["date"])
                wd = _german_weekday(s_date)
                lines.append(f"  - {wd} {s['date']}: {detail}{dur}")
            parts.append("Kommende Sessions:\n" + "\n".join(lines))

    parts.append(
        f"\n## Wochenvolumen (aktuelle Woche)\n"
        f"- Sessions: {weekly_volume['sessions']}\n"
        f"- Distanz: {weekly_volume['distance_km']} km\n"
        f"- Dauer: {weekly_volume['duration_min']} min"
    )

    if recent_sessions:
        lines = []
        for s in recent_sessions:
            pace = f", Pace {s['pace']}" if s.get("pace") else ""
            hr = f", HF {s['hr_avg']}" if s.get("hr_avg") else ""
            tt = f" [{s['training_type']}]" if s.get("training_type") else ""
            sid = s.get("id")
            link = f"[Details](/sessions/{sid})" if sid else ""
            s_date = date.fromisoformat(s["date"])
            wd = _german_weekday(s_date)[:2]  # Mo, Di, Mi...
            lines.append(
                f"  - {wd} {s['date']}: {s['type']}{tt}"
                f" — {s.get('duration_min', '?')} min"
                f", {s.get('distance_km', '?')} km"
                f"{pace}{hr}"
                f" {link}".rstrip()
            )
        parts.append("\n## Letzte Sessions (2 Wochen)\n" + "\n".join(lines))

    parts.append(
        "\n## Hinweise\n"
        "- Wenn du auf eine bestimmte Session verweist, verlinke sie als Markdown-Link: "
        "[Beschreibung](/sessions/ID). Beispiel: "
        '"Dein [Dauerlauf am 15.03.](/sessions/42) war gut dosiert."\n'
        "- Du hast Zugriff auf Tools um Details nachzuladen. "
        "Nutze sie aktiv wenn der User nach spezifischen Daten fragt "
        "(Session-Details, Statistiken, Plandetails, Uebungen etc.).\n"
        "- Fasse Tool-Ergebnisse kompakt und hilfreich zusammen — "
        "gib nicht alle Rohdaten wieder, sondern die relevanten Erkenntnisse."
    )

    return "\n".join(parts)
