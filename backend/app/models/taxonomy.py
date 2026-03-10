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
