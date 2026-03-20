"""Chat Notifications Service — Proaktive KI-Hinweise (#392).

Analysiert Trainingsdaten und erzeugt Benachrichtigungen,
wenn relevante Situationen erkannt werden (z.B. lange Pause,
hoher Ruhepuls, Volumensprung).
"""

import logging
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import WorkoutModel

logger = logging.getLogger(__name__)


async def get_notifications(db: AsyncSession) -> list[dict]:
    """Prueft aktuelle Trainingsdaten und generiert Benachrichtigungen."""
    today = date.today()
    notifications: list[dict] = []

    # Check 1: Trainingspause (>3 Tage kein Training)
    pause_note = await _check_training_pause(db, today)
    if pause_note:
        notifications.append(pause_note)

    # Check 2: Volumensprung (>30% mehr als letzte Woche)
    volume_note = await _check_volume_spike(db, today)
    if volume_note:
        notifications.append(volume_note)

    # Check 3: Monotones Training (nur ein Trainingstyp)
    mono_note = await _check_monotony(db, today)
    if mono_note:
        notifications.append(mono_note)

    return notifications


async def _check_training_pause(db: AsyncSession, today: date) -> dict | None:
    """Prueft ob der Athlet >3 Tage nicht trainiert hat."""
    result = await db.execute(select(WorkoutModel.date).order_by(WorkoutModel.date.desc()).limit(1))
    last_date_row = result.scalar_one_or_none()
    if not last_date_row:
        return None

    last_date = last_date_row.date() if isinstance(last_date_row, datetime) else last_date_row
    days_since = (today - last_date).days

    if days_since >= 3:
        return {
            "type": "training_pause",
            "severity": "warning" if days_since >= 5 else "info",
            "title": f"{days_since} Tage ohne Training",
            "message": (
                f"Dein letztes Training war am {last_date.strftime('%d.%m.')}. "
                "Soll ich den Plan anpassen oder einen leichten Wiedereinstieg vorschlagen?"
            ),
            "suggested_question": "Was soll ich nach meiner Trainingspause trainieren?",
        }
    return None


async def _check_volume_spike(db: AsyncSession, today: date) -> dict | None:
    """Prueft ob das Volumen dieser Woche >30% ueber letzter Woche liegt."""
    week_start = today - timedelta(days=today.weekday())
    prev_week_start = week_start - timedelta(weeks=1)

    this_week = await _week_volume(db, week_start, today)
    last_week = await _week_volume(db, prev_week_start, prev_week_start + timedelta(days=6))

    if last_week > 0 and this_week > last_week * 1.3:
        pct = round((this_week / last_week - 1) * 100)
        return {
            "type": "volume_spike",
            "severity": "warning",
            "title": f"Volumen +{pct}% zur Vorwoche",
            "message": (
                f"Diese Woche: {this_week:.1f} km vs. letzte Woche: {last_week:.1f} km. "
                "Ein Anstieg über 10-15% erhöht das Verletzungsrisiko."
            ),
            "suggested_question": "Ist mein Trainingsvolumen diese Woche zu hoch?",
        }
    return None


async def _check_monotony(db: AsyncSession, _today: date) -> dict | None:
    """Prueft ob die letzten 7 Sessions nur einen Trainingstyp haben."""
    result = await db.execute(
        select(
            func.coalesce(
                WorkoutModel.training_type_override,
                WorkoutModel.training_type_auto,
                "unknown",
            )
        )
        .where(WorkoutModel.workout_type == "running")
        .order_by(WorkoutModel.date.desc())
        .limit(7)
    )
    types = [str(r) for r in result.scalars().all()]

    if len(types) >= 5 and len(set(types)) == 1:
        return {
            "type": "monotony",
            "severity": "info",
            "title": "Einseitiges Training erkannt",
            "message": (
                f"Deine letzten {len(types)} Läufe waren alle vom Typ '{types[0]}'. "
                "Abwechslung verbessert die Leistungsentwicklung."
            ),
            "suggested_question": "Wie kann ich mehr Abwechslung in mein Training bringen?",
        }
    return None


async def _week_volume(db: AsyncSession, start: date, end: date) -> float:
    """Berechnet das Wochenvolumen in km."""
    result = await db.execute(
        select(func.sum(WorkoutModel.distance_km)).where(
            WorkoutModel.date >= datetime.combine(start, datetime.min.time()),
            WorkoutModel.date <= datetime.combine(end, datetime.max.time()),
        )
    )
    return float(result.scalar() or 0)
