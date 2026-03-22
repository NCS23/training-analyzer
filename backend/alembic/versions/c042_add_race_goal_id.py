"""Add race_goal_id column to workouts for race-to-goal linking (#52).

Revision ID: c042
Revises: c041
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa

revision = "c042"
down_revision = "c041"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workouts",
        sa.Column("race_goal_id", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("workouts", "race_goal_id")
