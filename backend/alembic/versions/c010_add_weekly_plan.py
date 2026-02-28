"""Add weekly plan entries table.

Revision ID: c010
Revises: c009
Create Date: 2026-03-01
"""

from alembic import op
import sqlalchemy as sa

revision = "c010"
down_revision = "c009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weekly_plan_entries",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "week_start",
            sa.Date(),
            nullable=False,
            index=True,
        ),
        sa.Column("day_of_week", sa.Integer(), nullable=False),  # 0=Mon, 6=Sun
        sa.Column(
            "training_type",
            sa.String(30),
            nullable=True,
        ),  # 'strength', 'running', None for rest
        sa.Column("plan_id", sa.Integer(), nullable=True),  # FK to training_plans
        sa.Column(
            "is_rest_day",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("week_start", "day_of_week", name="uq_week_day"),
    )


def downgrade() -> None:
    op.drop_table("weekly_plan_entries")
