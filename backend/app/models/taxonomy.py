"""Canonical session type and segment type definitions.

Single source of truth for the training taxonomy.
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
