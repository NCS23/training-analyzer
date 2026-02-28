"""Batch-Übersetzung aller Übungsanleitungen aus free-exercise-db ins Deutsche.

Nutzt die Anthropic API (Claude) um Anleitungen zu übersetzen.
Ergebnis wird in data/exercise_instructions_de.json gespeichert.

Usage:
    ANTHROPIC_API_KEY=sk-... python scripts/translate_exercises.py
"""

import json
import os
import sys
import time
from pathlib import Path

import anthropic

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "free_exercise_db.json"
OUTPUT_PATH = DATA_DIR / "exercise_instructions_de.json"

BATCH_SIZE = 15  # Übungen pro API-Call


def load_exercise_db() -> list[dict]:
    """Alle Übungen laden."""
    with open(DB_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_existing_translations() -> dict[str, list[str]]:
    """Bereits vorhandene Übersetzungen laden."""
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def build_translation_prompt(exercises: list[dict]) -> str:
    """Prompt für die Batch-Übersetzung erstellen."""
    parts = []
    for ex in exercises:
        instructions = ex.get("instructions", [])
        if not instructions:
            continue
        steps = "\n".join(f"  {i+1}. {step}" for i, step in enumerate(instructions))
        parts.append(f'### {ex["id"]}\n{steps}')

    exercises_text = "\n\n".join(parts)

    return f"""Übersetze die folgenden Übungsanleitungen vom Englischen ins Deutsche.

REGELN:
- Verwende die Du-Form (informell)
- Fachbegriffe korrekt übersetzen (barbell=Langhantel, dumbbell=Kurzhantel, bench=Bank, rack=Ablage/Rack, rep=Wiederholung, set=Satz, grip=Griff)
- Atme ein/aus statt Einatmen/Ausatmen
- Natürliches, flüssiges Deutsch — keine wörtliche Übersetzung
- Tipps beibehalten als "Tipp: ..."
- Halte die Nummerierung der Schritte bei
- WICHTIG: Gib das Ergebnis als JSON-Objekt zurück, wobei der Schlüssel die exercise ID ist und der Wert ein Array von Strings (die übersetzten Schritte)

{exercises_text}

Antworte NUR mit dem JSON-Objekt, ohne Markdown-Codeblöcke oder sonstigen Text."""


def translate_batch(
    client: anthropic.Anthropic, exercises: list[dict], batch_num: int, total_batches: int
) -> dict[str, list[str]]:
    """Einen Batch von Übungen übersetzen."""
    prompt = build_translation_prompt(exercises)

    for attempt in range(3):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}],
            )

            text = response.content[0].text.strip()
            # JSON aus der Antwort extrahieren (falls in Codeblock)
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
                text = text.rsplit("```", 1)[0]
            text = text.strip()

            result = json.loads(text)
            print(
                f"  Batch {batch_num}/{total_batches}: "
                f"{len(result)} Übungen übersetzt "
                f"(Tokens: {response.usage.input_tokens}+{response.usage.output_tokens})"
            )
            return result

        except json.JSONDecodeError as e:
            print(f"  Batch {batch_num}: JSON-Fehler (Versuch {attempt+1}/3): {e}")
            if attempt < 2:
                time.sleep(2)
        except anthropic.RateLimitError:
            wait = 30 * (attempt + 1)
            print(f"  Rate Limit — warte {wait}s...")
            time.sleep(wait)
        except anthropic.APIError as e:
            print(f"  API-Fehler (Versuch {attempt+1}/3): {e}")
            if attempt < 2:
                time.sleep(5)

    print(f"  WARNUNG: Batch {batch_num} fehlgeschlagen!")
    return {}


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Fehler: ANTHROPIC_API_KEY nicht gesetzt!")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    # Übungen laden
    exercises = load_exercise_db()
    print(f"Gesamt: {len(exercises)} Übungen in der DB")

    # Bereits übersetzte laden
    translations = load_existing_translations()
    print(f"Bereits übersetzt: {len(translations)} Übungen")

    # Nur Übungen mit Anleitungen und ohne Übersetzung
    to_translate = [
        ex
        for ex in exercises
        if ex["id"] not in translations and ex.get("instructions")
    ]
    print(f"Zu übersetzen: {len(to_translate)} Übungen")

    if not to_translate:
        print("Alles bereits übersetzt!")
        return

    # In Batches aufteilen
    batches = []
    for i in range(0, len(to_translate), BATCH_SIZE):
        batches.append(to_translate[i : i + BATCH_SIZE])

    total = len(batches)
    print(f"Starte Übersetzung in {total} Batches à {BATCH_SIZE} Übungen...\n")

    for i, batch in enumerate(batches, 1):
        result = translate_batch(client, batch, i, total)
        translations.update(result)

        # Nach jedem Batch speichern (Fortschritt sichern)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(translations, f, ensure_ascii=False, indent=2)

        # Rate Limiting
        if i < total:
            time.sleep(1)

    print(f"\nFertig! {len(translations)} Übungen in {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
