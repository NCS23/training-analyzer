"""Add trimp_score to workouts and personal_max_ctl to athletes.

Part of Fitness-Score Engine (#675):
- trimp_score: Edwards TRIMP pro Session (berechnet aus HR-Zonen × Dauer)
- personal_max_ctl: Höchster je erreichter CTL-Wert (für Score-Normalisierung 0-100)

Revision ID: c045
Revises: c044
Create Date: 2026-04-06
"""

import sqlalchemy as sa
from alembic import op

revision = "c045"
down_revision = "c044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    # trimp_score auf workouts
    existing_workout_cols = [c["name"] for c in inspector.get_columns("workouts")]
    if "trimp_score" not in existing_workout_cols:
        op.add_column("workouts", sa.Column("trimp_score", sa.Float(), nullable=True))

    # personal_max_ctl auf athletes
    existing_athlete_cols = [c["name"] for c in inspector.get_columns("athletes")]
    if "personal_max_ctl" not in existing_athlete_cols:
        op.add_column(
            "athletes", sa.Column("personal_max_ctl", sa.Float(), nullable=True)
        )


def downgrade() -> None:
    op.drop_column("athletes", "personal_max_ctl")
    op.drop_column("workouts", "trimp_score")
