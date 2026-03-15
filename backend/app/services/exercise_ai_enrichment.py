"""Claude API Fallback für Übungs-Anreicherung.

Wenn free-exercise-db keinen Match liefert, generiert Claude
Anleitungen, Muskelgruppen und Metadaten für eine Übung.
"""

import json
import logging
from typing import Optional

import anthropic

from app.core.config import settings
from app.services.exercise_enrichment import VALID_MUSCLES

logger = logging.getLogger(__name__)

# Erlaubte Werte für strukturierte Felder
_VALID_EQUIPMENT = {
    "barbell",
    "dumbbell",
    "cable",
    "machine",
    "kettlebell",
    "body_only",
    "bands",
    "medicine_ball",
    "exercise_ball",
    "foam_roll",
    "e-z_curl_bar",
    "other",
}
_VALID_LEVELS = {"beginner", "intermediate", "advanced"}
_VALID_FORCE = {"push", "pull", "static"}
_VALID_MECHANIC = {"compound", "isolation"}


def _build_prompt(exercise_name: str, category: str) -> str:
    """Erstelle den Prompt für die Übungs-Anreicherung."""
    muscles_list = ", ".join(sorted(VALID_MUSCLES))
    equipment_list = ", ".join(sorted(_VALID_EQUIPMENT))

    return f"""Du bist ein Fitness-Experte. Generiere detaillierte Informationen für folgende Übung:

Name: {exercise_name}
Kategorie: {category}

Antworte ausschließlich mit validem JSON (kein Markdown, keine Erklärung).
Das JSON muss exakt dieses Schema haben:

{{
  "instructions": ["Schritt 1...", "Schritt 2...", "Schritt 3..."],
  "primary_muscles": ["muscle1", "muscle2"],
  "secondary_muscles": ["muscle3"],
  "equipment": "equipment_type",
  "level": "beginner|intermediate|advanced",
  "force": "push|pull|static",
  "mechanic": "compound|isolation"
}}

Regeln:
- "instructions": 3-6 Schritte auf Deutsch, präzise Ausführungsbeschreibung
- "primary_muscles": Hauptmuskeln (englisch), erlaubt: {muscles_list}
- "secondary_muscles": Hilfsmuskeln (englisch), erlaubt: {muscles_list}
- "equipment": eines von: {equipment_list}
- "level": eines von: beginner, intermediate, advanced
- "force": eines von: push, pull, static
- "mechanic": eines von: compound, isolation

Nur valides JSON ausgeben, nichts anderes."""


def _validate_and_normalize(data: dict) -> Optional[dict]:
    """Validiere und normalisiere die Claude-Antwort."""
    # instructions: muss Liste von Strings sein
    instructions = data.get("instructions")
    if not isinstance(instructions, list) or len(instructions) == 0:
        logger.warning("Claude-Antwort: instructions fehlt oder leer")
        return None
    instructions = [str(s) for s in instructions if s]
    if not instructions:
        return None

    # primary_muscles: muss Liste sein, nur gültige Werte
    primary = data.get("primary_muscles", [])
    if not isinstance(primary, list):
        primary = []
    primary = [m for m in primary if m in VALID_MUSCLES]
    if not primary:
        logger.warning("Claude-Antwort: keine gültigen primary_muscles")
        return None

    # secondary_muscles: optional, nur gültige Werte
    secondary = data.get("secondary_muscles", [])
    if not isinstance(secondary, list):
        secondary = []
    secondary = [m for m in secondary if m in VALID_MUSCLES]

    # Skalare Felder validieren
    equipment = data.get("equipment")
    if equipment not in _VALID_EQUIPMENT:
        equipment = None

    level = data.get("level")
    if level not in _VALID_LEVELS:
        level = None

    force = data.get("force")
    if force not in _VALID_FORCE:
        force = None

    mechanic = data.get("mechanic")
    if mechanic not in _VALID_MECHANIC:
        mechanic = None

    return {
        "instructions_json": json.dumps(instructions),
        "primary_muscles_json": json.dumps(primary),
        "secondary_muscles_json": json.dumps(secondary),
        "image_urls_json": json.dumps([]),
        "equipment": equipment,
        "level": level,
        "force": force,
        "mechanic": mechanic,
        "exercise_db_id": None,
    }


async def generate_exercise_enrichment(
    exercise_name: str,
    category: str,
    api_key: str = "",
) -> Optional[dict[str, Optional[str]]]:
    """Generiere Übungs-Anreicherung über Claude API.

    Fallback wenn free-exercise-db keinen Match hat.
    Gibt DB-ready Column-Values zurück (gleiches Format wie
    ``exercise_enrichment._to_db_columns``), oder ``None`` bei Fehler.

    Args:
        api_key: Resolved API-Key (via ``resolve_claude_api_key``).
    """
    if not api_key:
        logger.debug("Claude API Key nicht konfiguriert — Fallback übersprungen")
        return None

    prompt = _build_prompt(exercise_name, category)

    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=1000,
            temperature=0.2,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text = response.content[0].text  # type: ignore[union-attr]
    except Exception:
        logger.exception("Claude API Fehler bei Übungs-Anreicherung für '%s'", exercise_name)
        return None

    # JSON parsen
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.warning(
            "Claude-Antwort ist kein valides JSON für '%s': %s",
            exercise_name,
            raw_text[:200],
        )
        return None

    result = _validate_and_normalize(data)
    if result:
        logger.info("Claude AI Enrichment erfolgreich für '%s'", exercise_name)
    return result
