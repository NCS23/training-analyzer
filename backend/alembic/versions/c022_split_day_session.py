"""Split weekly_plan_entries into weekly_plan_days + planned_sessions.

Enables multiple sessions per day (e.g. morning run + evening strength).

Revision ID: c022
Revises: c021
"""

import sqlalchemy as sa

from alembic import op

revision = "c022"
down_revision = "c021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Split weekly_plan_entries into day + session tables."""
    conn = op.get_bind()

    # 1. Create weekly_plan_days table
    op.create_table(
        "weekly_plan_days",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("plan_id", sa.Integer, nullable=True, index=True),
        sa.Column("week_start", sa.Date, nullable=False, index=True),
        sa.Column("day_of_week", sa.Integer, nullable=False),
        sa.Column(
            "is_rest_day",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "edited",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("week_start", "day_of_week", name="uq_day_week_day"),
    )

    # 2. Copy day-level data (preserve IDs for remapping)
    conn.execute(
        sa.text(
            "INSERT INTO weekly_plan_days "
            "(id, plan_id, week_start, day_of_week, is_rest_day, "
            "notes, edited, created_at, updated_at) "
            "SELECT id, plan_id, week_start, day_of_week, is_rest_day, "
            "notes, edited, created_at, updated_at "
            "FROM weekly_plan_entries"
        )
    )

    # 3. Create planned_sessions table
    op.create_table(
        "planned_sessions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("day_id", sa.Integer, nullable=False, index=True),
        sa.Column("position", sa.Integer, nullable=False, server_default="0"),
        sa.Column("training_type", sa.String(30), nullable=False),
        sa.Column("template_id", sa.Integer, nullable=True),
        sa.Column("run_details_json", sa.Text, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
    )

    # 4. Extract session data (only non-rest entries with training_type)
    conn.execute(
        sa.text(
            "INSERT INTO planned_sessions "
            "(day_id, position, training_type, template_id, "
            "run_details_json, notes, created_at, updated_at) "
            "SELECT id, 0, training_type, template_id, "
            "run_details_json, NULL, created_at, updated_at "
            "FROM weekly_plan_entries "
            "WHERE training_type IS NOT NULL"
        )
    )

    # 5. Remap workouts.planned_entry_id (old entry_id -> new session_id)
    rows = conn.execute(
        sa.text("SELECT id, day_id FROM planned_sessions")
    ).fetchall()
    for session_id, day_id in rows:
        conn.execute(
            sa.text(
                "UPDATE workouts SET planned_entry_id = :new "
                "WHERE planned_entry_id = :old"
            ),
            {"new": session_id, "old": day_id},
        )

    # 6. Verification
    old_count = conn.execute(
        sa.text("SELECT COUNT(*) FROM weekly_plan_entries")
    ).scalar()
    new_day_count = conn.execute(
        sa.text("SELECT COUNT(*) FROM weekly_plan_days")
    ).scalar()
    assert old_count == new_day_count, (
        f"Day count mismatch: {old_count} entries vs {new_day_count} days"
    )

    old_sessions = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM weekly_plan_entries "
            "WHERE training_type IS NOT NULL"
        )
    ).scalar()
    new_sessions = conn.execute(
        sa.text("SELECT COUNT(*) FROM planned_sessions")
    ).scalar()
    assert old_sessions == new_sessions, (
        f"Session count mismatch: {old_sessions} vs {new_sessions}"
    )

    # 7. Drop old table
    op.drop_table("weekly_plan_entries")


def downgrade() -> None:
    """Merge weekly_plan_days + planned_sessions back into weekly_plan_entries."""
    conn = op.get_bind()

    # 1. Recreate weekly_plan_entries
    op.create_table(
        "weekly_plan_entries",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("plan_id", sa.Integer, nullable=True, index=True),
        sa.Column("week_start", sa.Date, nullable=False, index=True),
        sa.Column("day_of_week", sa.Integer, nullable=False),
        sa.Column("training_type", sa.String(30), nullable=True),
        sa.Column("template_id", sa.Integer, nullable=True),
        sa.Column(
            "is_rest_day",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("run_details_json", sa.Text, nullable=True),
        sa.Column(
            "edited",
            sa.Boolean,
            nullable=False,
            server_default="false",
        ),
        sa.Column("created_at", sa.DateTime, nullable=False),
        sa.Column("updated_at", sa.DateTime, nullable=False),
        sa.UniqueConstraint("week_start", "day_of_week", name="uq_week_day"),
    )

    # 2. Merge data back (LEFT JOIN: days without sessions get NULL training_type)
    conn.execute(
        sa.text(
            "INSERT INTO weekly_plan_entries "
            "(id, plan_id, week_start, day_of_week, training_type, "
            "template_id, is_rest_day, notes, run_details_json, "
            "edited, created_at, updated_at) "
            "SELECT d.id, d.plan_id, d.week_start, d.day_of_week, "
            "s.training_type, s.template_id, d.is_rest_day, d.notes, "
            "s.run_details_json, d.edited, d.created_at, d.updated_at "
            "FROM weekly_plan_days d "
            "LEFT JOIN planned_sessions s ON s.day_id = d.id AND s.position = 0"
        )
    )

    # 3. Remap workouts.planned_entry_id back (session_id -> day_id)
    rows = conn.execute(
        sa.text("SELECT id, day_id FROM planned_sessions")
    ).fetchall()
    for session_id, day_id in rows:
        conn.execute(
            sa.text(
                "UPDATE workouts SET planned_entry_id = :new "
                "WHERE planned_entry_id = :old"
            ),
            {"new": day_id, "old": session_id},
        )

    # 4. Drop new tables
    op.drop_table("planned_sessions")
    op.drop_table("weekly_plan_days")
