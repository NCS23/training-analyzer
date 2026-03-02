"""Add weekly_templates_json to training_phases.

Stores per-week template overrides as JSON dict.
Existing rows stay NULL (= no per-week overrides, shared template applies).

Revision ID: c017
Revises: c016
Create Date: 2026-03-02
"""

import sqlalchemy as sa

from alembic import op

revision = "c017"
down_revision = "c016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "training_phases",
        sa.Column("weekly_templates_json", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("training_phases", "weekly_templates_json")
