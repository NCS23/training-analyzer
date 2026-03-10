"""Canonical training taxonomy definitions.

Single source of truth for session types, segment types, and phase focus tags.
Used by validators, classifiers, API endpoints, and data migrations.
"""

# Session types (what kind of run was this?)
SESSION_TYPES = frozenset(
    {
        "recovery",
        "easy",
        "long_run",
        "progression",
        "tempo",
        "intervals",
        "repetitions",
        "fartlek",
        "race",
    }
)

SESSION_TYPE_REGEX = "^(" + "|".join(sorted(SESSION_TYPES)) + ")$"

# Segment/lap types (what is this lap within a session?)
SEGMENT_TYPES = frozenset(
    {
        "warmup",
        "cooldown",
        "steady",
        "work",
        "recovery_jog",
        "rest",
        "strides",
        "drills",
    }
)

SEGMENT_TYPE_REGEX = "^(" + "|".join(sorted(SEGMENT_TYPES)) + ")$"

# Intensity classification for training balance
EASY_SESSION_TYPES = frozenset({"recovery", "easy", "long_run"})
MODERATE_SESSION_TYPES = frozenset({"tempo", "progression", "fartlek"})
HARD_SESSION_TYPES = frozenset({"intervals", "repetitions", "race"})

# Migration mappings (old -> new)
SESSION_TYPE_MIGRATION = {
    "hill_repeats": "repetitions",
}

SEGMENT_TYPE_MIGRATION = {
    "pause": "rest",
    "interval": "work",
    "tempo": "steady",
    "longrun": "steady",
    "recovery": "recovery_jog",
    "unclassified": "steady",
}

# Excluded segment types for working-lap metrics
EXCLUDED_SEGMENT_TYPES = frozenset({"warmup", "cooldown", "rest"})

# Phase focus tags — trainingswissenschaftlich fundierter Katalog
# Keys are canonical identifiers, values are German display labels.
PHASE_FOCUS_TAGS: dict[str, str] = {
    "aerobic_base": "Aerobe Grundlage",
    "structural_adaptation": "Strukturanpassung",
    "running_economy": "Laufökonomie",
    "injury_prevention": "Verletzungsprävention",
    "lactate_threshold": "Laktatschwelle",
    "tempo_hardness": "Tempohärte",
    "specific_strength": "Spezifische Kraft",
    "race_pace_intro": "Wettkampftempo-Einführung",
    "vo2max": "VO2max",
    "race_pace": "Wettkampftempo",
    "race_tactics": "Renntaktik",
    "mental_toughness": "Mentale Härte",
    "supercompensation": "Superkompensation",
    "fatigue_reduction": "Ermüdungsabbau",
    "mental_preparation": "Mentale Vorbereitung",
    "race_preparation": "Wettkampfvorbereitung",
    "regeneration": "Regeneration",
    "mobility": "Mobilität",
    "overtraining_prevention": "Übertrainings-Prävention",
}

# Legacy focus label migration (YAML-imported plans → canonical keys)
# Covers both ASCII-ified and proper-umlaut variants.
FOCUS_LABEL_MIGRATION: dict[str, str] = {
    "Grundlagenausdauer": "aerobic_base",
    "Formaufbau": "structural_adaptation",
    "Verletzungspraevention": "injury_prevention",
    "Verletzungsprävention": "injury_prevention",
    "Kraftstabilitaet": "specific_strength",
    "Kraftstabilität": "specific_strength",
    "Tempodauerlauf": "tempo_hardness",
    "Laufoekonomie": "running_economy",
    "Laufökonomie": "running_economy",
    "Mentale Haerte": "mental_toughness",
    "Mentale Härte": "mental_toughness",
    "Erholung": "regeneration",
    "Mentale Frische": "mental_preparation",
}

# Reverse lookup: canonical label → key (for catalog labels stored as German text)
_LABEL_TO_KEY: dict[str, str] = {v.lower(): k for k, v in PHASE_FOCUS_TAGS.items()}
_KNOWN_KEYS: frozenset[str] = frozenset(PHASE_FOCUS_TAGS.keys())


def normalize_focus_key(value: str) -> str:
    """Normalize a focus value to its canonical key.

    Handles: canonical keys (pass-through), catalog German labels,
    and legacy YAML-imported labels.
    """
    if value in _KNOWN_KEYS:
        return value
    # Try canonical catalog label
    if key := _LABEL_TO_KEY.get(value.lower()):
        return key
    # Try legacy YAML label (case-insensitive)
    legacy = {k.lower(): v for k, v in FOCUS_LABEL_MIGRATION.items()}
    return legacy.get(value.lower(), value)


# Default focus suggestions per phase type
PHASE_FOCUS_DEFAULTS: dict[str, dict[str, list[str]]] = {
    "base": {
        "primary": ["aerobic_base", "structural_adaptation"],
        "secondary": ["running_economy", "injury_prevention"],
    },
    "build": {
        "primary": ["lactate_threshold", "tempo_hardness"],
        "secondary": ["specific_strength", "race_pace_intro"],
    },
    "peak": {
        "primary": ["vo2max", "race_pace"],
        "secondary": ["race_tactics", "mental_toughness"],
    },
    "taper": {
        "primary": ["supercompensation", "fatigue_reduction"],
        "secondary": ["mental_preparation", "race_preparation"],
    },
    "transition": {
        "primary": ["regeneration", "mobility"],
        "secondary": ["overtraining_prevention"],
    },
}
