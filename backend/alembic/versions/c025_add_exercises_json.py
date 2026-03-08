"""Add exercises_json column to planned_sessions.

Stores structured strength exercises (TemplateExercise[]) as JSON,
analogous to how run_details_json stores running session details.

Revision ID: c025
Revises: c024
"""

import sqlalchemy as sa

from alembic import op

revision = "c025"
down_revision = "c024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add exercises_json column."""
    op.add_column(
        "planned_sessions",
        sa.Column("exercises_json", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    """Remove exercises_json column."""
    op.drop_column("planned_sessions", "exercises_json")
