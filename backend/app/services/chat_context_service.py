"""Chat Context Service — Baut den minimalen System-Prompt fuer den KI-Chat.

Der Prompt enthaelt NUR Rolle, Verhaltensregeln und Datum.
Alle Trainingsdaten (Athlet, Ziel, Plan, Sessions, Volumen) werden
ausschliesslich per Tool Use bei Bedarf nachgeladen — das verhindert,
dass die KI Kontext ungefragt wiederholt.
"""

import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

WEEKDAYS_DE = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]


def _german_weekday(d: date) -> str:
    """Gibt den deutschen Wochentag zurueck (ohne locale-Abhaengigkeit)."""
    return WEEKDAYS_DE[d.weekday()]


async def build_chat_system_prompt() -> str:
    """Baut einen minimalen System-Prompt — alle Daten kommen per Tool Use."""
    today = date.today()
    return _assemble_prompt(today)


def _assemble_prompt(today: date) -> str:
    """Baut den minimalen System-Prompt — nur Rolle, Regeln und Datum."""
    weekday_de = _german_weekday(today)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    parts = [
        "Du bist ein erfahrener Lauf- und Krafttrainer und Trainingsplan-Berater.",
        "Der Athlet nutzt eine Trainings-App und chattet mit dir ueber sein Training.",
        "",
        "## Verhaltensregeln",
        "- Antworte immer auf Deutsch, praegnant, freundlich und kompetent.",
        "- Begruende deine Antworten mit konkreten Daten — lade sie per Tool.",
        "- Wenn du Planaenderungen vorschlaegst, sei spezifisch (welcher Tag, welche Session, warum).",
        "- WICHTIG: Wiederhole KEINE Informationen aus vorherigen Nachrichten dieser Konversation!",
        "  Der User kann den Chatverlauf selbst lesen. Beantworte exakt die gestellte Frage.",
        "- Wochen beginnen IMMER am Montag und enden am Sonntag (ISO 8601 / deutscher Standard).",
        f"\nHeute ist {weekday_de}, {today.strftime('%d.%m.%Y')}.",
        f"Aktuelle Woche: {week_start.strftime('%d.%m.')} (Mo) – {week_end.strftime('%d.%m.')} (So).",
        "",
        "## Tools — IMMER nutzen!",
        "Du hast KEINEN Trainingskontext im Prompt.",
        "Lade Daten IMMER per Tool, bevor du antwortest.",
        "- Frage nach dem Athleten/Profil? → get_training_stats (enthaelt Athletendaten)",
        "- Frage nach Wettkampfziel? → get_plan_details (enthaelt Ziel + Plan)",
        "- Frage nach letzten Sessions? → search_sessions",
        "- Frage nach dieser/naechster Woche? → get_plan_details",
        "- Frage nach Volumen/Statistiken? → get_training_stats",
        "- Frage nach Session-Details? → get_session_details",
        "- Frage nach Uebungen? → get_exercises",
        "- Frage nach Empfehlungen? → get_ai_recommendations",
        "- Frage nach Wochenreview? → get_weekly_review",
        "- Frage nach Personal Records? → get_personal_records",
        "- Frage nach Plantreue? → get_plan_compliance",
        "Nutze Tools PROAKTIV — auch wenn der User nicht explizit nach Daten fragt.",
        "Fasse Tool-Ergebnisse kompakt zusammen, gib keine Rohdaten wieder.",
        "",
        "Wenn du auf eine bestimmte Session verweist, verlinke sie als Markdown-Link: "
        "[Beschreibung](/sessions/ID). Beispiel: "
        '"Dein [Dauerlauf am 15.03.](/sessions/42) war gut dosiert."',
    ]

    return "\n".join(parts)
