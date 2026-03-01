"""Add weekly_template_json to training_phases.

Stores a 7-day weekly template per phase for configurable session
distribution (replaces hardcoded PHASE_DEFAULTS).

Revision ID: c015
Revises: c014
Create Date: 2026-03-01
"""

import sqlalchemy as sa

from alembic import op

revision = "c015"
down_revision = "c014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "training_phases",
        sa.Column("weekly_template_json", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("training_phases", "weekly_template_json")
