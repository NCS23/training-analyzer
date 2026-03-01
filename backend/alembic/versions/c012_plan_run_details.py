"""Add run_details_json to training_plans for running templates.

Revision ID: c012
Revises: c011
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa

revision = "c012"
down_revision = "c011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "training_plans",
        sa.Column("run_details_json", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("training_plans", "run_details_json")
