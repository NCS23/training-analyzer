"""Service für Übungs-Daten-Anreicherung aus free-exercise-db."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Optional

# Mapping: deutsche Übungsnamen → free-exercise-db IDs
EXERCISE_DB_MAPPING: dict[str, str] = {
    "Bankdrücken": "Barbell_Bench_Press_-_Medium_Grip",
    "Schrägbankdrücken": "Barbell_Incline_Bench_Press_-_Medium_Grip",
    "Kurzhantel-Bankdrücken": "Dumbbell_Bench_Press",
    "Schulterdrücken": "Standing_Military_Press",
    "Dips": "Dips_-_Chest_Version",
    "Seitheben": "Side_Lateral_Raise",
    "Trizeps-Pushdown": "Triceps_Pushdown",
    "Liegestütze": "Pushups",
    "Klimmzüge": "Pullups",
    "Langhantelrudern": "Bent_Over_Barbell_Row",
    "Kurzhantelrudern": "One-Arm_Dumbbell_Row",
    "Latzug": "Wide-Grip_Lat_Pulldown",
    "Face Pulls": "Face_Pull",
    "Bizeps-Curls": "Barbell_Curl",
    "Hammer Curls": "Hammer_Curls",
    "Kniebeugen": "Barbell_Squat",
    "Kreuzheben": "Barbell_Deadlift",
    "Rumänisches Kreuzheben": "Romanian_Deadlift",
    "Beinpresse": "Leg_Press",
    "Ausfallschritte": "Dumbbell_Lunges",
    "Beinbeuger": "Lying_Leg_Curls",
    "Beinstrecker": "Leg_Extensions",
    "Wadenheben": "Standing_Calf_Raises",
    "Hip Thrusts": "Barbell_Hip_Thrust",
    "Plank": "Plank",
    "Crunches": "Crunches",
    "Russian Twist": "Russian_Twist",
    "Hanging Leg Raises": "Hanging_Leg_Raise",
    "Cable Crunches": "Cable_Crunch",
    "Rudern Ergometer": "Rowing_Stationary",
    "Seilspringen": "Rope_Jumping",
}


# Deutsche Übersetzungen — werden aus JSON-Datei geladen
@lru_cache(maxsize=1)
def _load_instruction_translations() -> dict[str, list[str]]:
    """Lade deutsche Übersetzungen aus data/exercise_instructions_de.json."""
    translations_path = _get_data_dir() / "exercise_instructions_de.json"
    if not translations_path.exists():
        return {}
    with open(translations_path, encoding="utf-8") as f:
        return json.load(f)


# All valid muscle group names from free-exercise-db
VALID_MUSCLES = {
    "abdominals",
    "abductors",
    "adductors",
    "biceps",
    "calves",
    "chest",
    "forearms",
    "glutes",
    "hamstrings",
    "lats",
    "lower back",
    "middle back",
    "neck",
    "quadriceps",
    "shoulders",
    "traps",
    "triceps",
}


def _get_data_dir() -> Path:
    """Return the data directory path."""
    return Path(__file__).parent.parent.parent / "data"


def _get_static_dir() -> Path:
    """Return the static directory path."""
    return Path(__file__).parent.parent.parent / "static"


def load_exercise_db() -> dict[str, dict]:
    """Load free-exercise-db data indexed by ID."""
    db_path = _get_data_dir() / "free_exercise_db.json"
    if not db_path.exists():
        return {}

    with open(db_path, encoding="utf-8") as f:
        exercises = json.load(f)

    return {ex["id"]: ex for ex in exercises}


def _build_enrichment_dict(db_id: str, ex_data: dict) -> dict:
    """Build enrichment data dict from a resolved exercise-db entry."""
    image_urls = []
    static_dir = _get_static_dir()
    for img_num in [0, 1]:
        img_path = static_dir / "exercises" / db_id / f"{img_num}.jpg"
        if img_path.exists():
            image_urls.append(f"/static/exercises/{db_id}/{img_num}.jpg")

    # Deutsche Übersetzung verwenden, falls vorhanden
    instructions = _load_instruction_translations().get(db_id, ex_data.get("instructions", []))

    return {
        "exercise_db_id": db_id,
        "instructions": instructions,
        "primary_muscles": ex_data.get("primaryMuscles", []),
        "secondary_muscles": ex_data.get("secondaryMuscles", []),
        "image_urls": image_urls,
        "equipment": ex_data.get("equipment"),
        "level": ex_data.get("level"),
        "force": ex_data.get("force"),
        "mechanic": ex_data.get("mechanic"),
    }


def get_enrichment_data(exercise_name: str) -> Optional[dict]:
    """Anreicherungsdaten für einen deutschen Übungsnamen abrufen.

    Sucht zuerst im expliziten Mapping, dann per Fuzzy-Match in der
    gesamten Datenbank. Gibt ein Dict mit Anleitungen (deutsch falls
    vorhanden), Muskeln, Bildern, Metadaten zurück, oder None.
    """
    db_id = EXERCISE_DB_MAPPING.get(exercise_name)
    if not db_id:
        db_id = find_exercise_db_match(exercise_name)
    if not db_id:
        return None

    exercise_db = load_exercise_db()
    ex_data = exercise_db.get(db_id)
    if not ex_data:
        return None

    return _build_enrichment_dict(db_id, ex_data)


def get_enrichment_data_by_id(exercise_db_id: str) -> Optional[dict]:
    """Anreicherungsdaten für eine spezifische exercise-db ID abrufen.

    Kein Name-Matching — sucht direkt per ID.
    """
    exercise_db = load_exercise_db()
    ex_data = exercise_db.get(exercise_db_id)
    if not ex_data:
        return None

    return _build_enrichment_dict(exercise_db_id, ex_data)


def enrich_exercise_model(
    exercise_name: str,
) -> Optional[dict[str, Optional[str]]]:
    """Get enrichment data as DB-ready column values.

    Returns dict with JSON-serialized values ready for ExerciseModel columns,
    or None if no match found.
    """
    data = get_enrichment_data(exercise_name)
    if not data:
        return None

    return _to_db_columns(data)


def enrich_exercise_model_by_id(
    exercise_db_id: str,
) -> Optional[dict[str, Optional[str]]]:
    """Get enrichment data as DB-ready column values for a specific exercise-db ID."""
    data = get_enrichment_data_by_id(exercise_db_id)
    if not data:
        return None

    return _to_db_columns(data)


def _to_db_columns(data: dict) -> dict[str, Optional[str]]:
    """Convert enrichment data dict to DB-ready column values."""
    return {
        "exercise_db_id": data["exercise_db_id"],
        "instructions_json": json.dumps(data["instructions"]),
        "primary_muscles_json": json.dumps(data["primary_muscles"]),
        "secondary_muscles_json": json.dumps(data["secondary_muscles"]),
        "image_urls_json": json.dumps(data["image_urls"]),
        "equipment": data.get("equipment"),
        "level": data.get("level"),
        "force": data.get("force"),
        "mechanic": data.get("mechanic"),
    }


# Reverse mapping: exercise-db ID → German name (from EXERCISE_DB_MAPPING)
EXERCISE_DB_REVERSE: dict[str, str] = {v: k for k, v in EXERCISE_DB_MAPPING.items()}


# Deutsche Suchbegriffe → englische Übersetzungen für Suche
GERMAN_SEARCH_TERMS: dict[str, list[str]] = {
    # Muskeln
    "brust": ["chest"],
    "rücken": ["back", "lats"],
    "schulter": ["shoulder"],
    "schultern": ["shoulder"],
    "arme": ["arm", "bicep", "tricep", "curl"],
    "bizeps": ["bicep", "curl"],
    "trizeps": ["tricep"],
    "bauch": ["abdominal", "crunch", "sit-up"],
    "beine": ["leg", "squat", "lunge"],
    "oberschenkel": ["quadricep", "hamstring", "leg"],
    "waden": ["calf", "calves"],
    "po": ["glute", "hip thrust"],
    "gesäss": ["glute", "hip thrust"],
    "nacken": ["neck", "trap"],
    "unterarme": ["forearm", "wrist"],
    # Equipment
    "langhantel": ["barbell"],
    "kurzhantel": ["dumbbell"],
    "kabelzug": ["cable"],
    "kabel": ["cable"],
    "maschine": ["machine"],
    "körpergewicht": ["body", "bodyweight"],
    "kettlebell": ["kettlebell"],
    "band": ["band"],
    "bänder": ["band"],
    "sz-stange": ["e-z curl bar", "ez"],
    "ez-stange": ["e-z curl bar", "ez"],
    # Übungstypen
    "drücken": ["press"],
    "rudern": ["row"],
    "heben": ["raise", "lift", "deadlift"],
    "beugen": ["curl", "squat"],
    "strecken": ["extension"],
    "ziehen": ["pull"],
    "fliegen": ["fly", "flye"],
    "kreuz": ["deadlift", "cross"],
    "ausfallschritt": ["lunge"],
    "kniebeuge": ["squat"],
    "klimmzug": ["pull-up", "pullup", "chin"],
    "liegestütz": ["push-up", "pushup"],
    "dip": ["dip"],
    "plank": ["plank"],
    "crunch": ["crunch"],
    "dehnung": ["stretch"],
    "curl": ["curl"],
    "press": ["press"],
    "row": ["row"],
    "squat": ["squat"],
    "bench": ["bench"],
    "bank": ["bench"],
    "bankdrücken": ["bench press"],
    "schrägbank": ["incline bench"],
    "flachbank": ["flat bench", "bench press"],
    "latzug": ["lat pulldown", "pulldown"],
    "beinpresse": ["leg press"],
    "beinbeuger": ["leg curl", "hamstring"],
    "beinstrecker": ["leg extension"],
    "wadenheben": ["calf raise"],
    "seitheben": ["lateral raise"],
    "hüfte": ["hip"],
}


def get_german_name(exercise_db_id: str) -> Optional[str]:
    """Gibt den deutschen Namen für eine exercise-db ID zurück, falls bekannt."""
    return EXERCISE_DB_REVERSE.get(exercise_db_id)


def get_all_german_names() -> dict[str, str]:
    """Gibt alle bekannten exercise-db ID → deutscher Name Zuordnungen zurück."""
    return dict(EXERCISE_DB_REVERSE)


def translate_search_query(query: str) -> list[str]:
    """Übersetze deutsche Suchbegriffe in englische Alternativen.

    Gibt eine Liste englischer Suchbegriffe zurück, die für die
    Suche in der exercise-db verwendet werden können.
    """
    q_lower = query.strip().lower()
    seen: set[str] = set()
    translations: list[str] = []

    for german, english_terms in GERMAN_SEARCH_TERMS.items():
        if q_lower == german or german.startswith(q_lower):
            for term in english_terms:
                if term not in seen:
                    seen.add(term)
                    translations.append(term)

    return translations


def find_exercise_db_match(exercise_name: str) -> Optional[str]:
    """Try to find a free-exercise-db match for an exercise name.

    First checks the explicit mapping, then tries fuzzy matching
    against the full database.
    """
    # 1. Explicit mapping
    if exercise_name in EXERCISE_DB_MAPPING:
        return EXERCISE_DB_MAPPING[exercise_name]

    # 2. Fuzzy match against full DB (case-insensitive, partial)
    exercise_db = load_exercise_db()
    name_lower = exercise_name.lower()

    # Exact match on DB name
    for db_id, ex in exercise_db.items():
        if ex["name"].lower() == name_lower:
            return db_id

    # Partial match
    for db_id, ex in exercise_db.items():
        if name_lower in ex["name"].lower() or ex["name"].lower() in name_lower:
            return db_id

    return None
