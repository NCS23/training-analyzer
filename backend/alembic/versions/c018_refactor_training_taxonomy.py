"""Refactor training taxonomy: session types + segment types.

Revision ID: c018
Revises: c017
"""

import json

import sqlalchemy as sa
from alembic import op

revision = "c018"
down_revision = "c017"
branch_labels = None
depends_on = None

# Segment type migration (old lap types -> new)
SEGMENT_MIGRATION = {
    "pause": "rest",
    "interval": "work",
    "tempo": "steady",
    "longrun": "steady",
    "recovery": "recovery_jog",
    "unclassified": "steady",
}

# Reverse mapping for downgrade (lossy: steady -> tempo as default)
SEGMENT_DOWNGRADE = {
    "rest": "pause",
    "work": "interval",
    "steady": "tempo",
    "recovery_jog": "recovery",
}


def upgrade() -> None:
    """Migrate existing data to new taxonomy."""
    conn = op.get_bind()

    # 1. Session types: hill_repeats -> repetitions
    conn.execute(
        sa.text(
            "UPDATE workouts SET training_type_auto = 'repetitions' "
            "WHERE training_type_auto = 'hill_repeats'"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE workouts SET training_type_override = 'repetitions' "
            "WHERE training_type_override = 'hill_repeats'"
        )
    )

    # 2. Lap/segment types in laps_json
    result = conn.execute(
        sa.text("SELECT id, laps_json FROM workouts WHERE laps_json IS NOT NULL")
    )
    for row in result:
        laps = json.loads(row[1])
        changed = False
        for lap in laps:
            for field in ("suggested_type", "user_override"):
                old_val = lap.get(field)
                if old_val in SEGMENT_MIGRATION:
                    lap[field] = SEGMENT_MIGRATION[old_val]
                    changed = True
        if changed:
            conn.execute(
                sa.text("UPDATE workouts SET laps_json = :laps WHERE id = :id"),
                {"laps": json.dumps(laps), "id": row[0]},
            )


def downgrade() -> None:
    """Reverse migration (lossy for segment types)."""
    conn = op.get_bind()

    # 1. Session types: repetitions -> hill_repeats
    conn.execute(
        sa.text(
            "UPDATE workouts SET training_type_auto = 'hill_repeats' "
            "WHERE training_type_auto = 'repetitions'"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE workouts SET training_type_override = 'hill_repeats' "
            "WHERE training_type_override = 'repetitions'"
        )
    )

    # 2. Reverse lap/segment types (lossy)
    result = conn.execute(
        sa.text("SELECT id, laps_json FROM workouts WHERE laps_json IS NOT NULL")
    )
    for row in result:
        laps = json.loads(row[1])
        changed = False
        for lap in laps:
            for field in ("suggested_type", "user_override"):
                old_val = lap.get(field)
                if old_val in SEGMENT_DOWNGRADE:
                    lap[field] = SEGMENT_DOWNGRADE[old_val]
                    changed = True
        if changed:
            conn.execute(
                sa.text("UPDATE workouts SET laps_json = :laps WHERE id = :id"),
                {"laps": json.dumps(laps), "id": row[0]},
            )
