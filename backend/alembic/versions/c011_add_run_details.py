"""Add run_details_json to weekly plan entries.

Revision ID: c011
Revises: c010
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa

revision = "c011"
down_revision = "c010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "weekly_plan_entries",
        sa.Column("run_details_json", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("weekly_plan_entries", "run_details_json")
