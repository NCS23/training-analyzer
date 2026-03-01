"""Add plan_id to weekly_plan_entries.

Links generated weekly plan entries to their source training plan.
NULL = manually created entry (not from generator).

Revision ID: c016
Revises: c015
Create Date: 2026-03-01
"""

import sqlalchemy as sa

from alembic import op

revision = "c016"
down_revision = "c015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "weekly_plan_entries",
        sa.Column("plan_id", sa.Integer, nullable=True, index=True),
    )


def downgrade() -> None:
    op.drop_column("weekly_plan_entries", "plan_id")
