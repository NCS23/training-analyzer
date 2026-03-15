"""add ai_analysis_log table

Revision ID: c029
Revises: c028
Create Date: 2026-03-15
"""

from alembic import op
import sqlalchemy as sa

revision = "c029"
down_revision = "c028"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_analysis_log",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("workout_id", sa.Integer(), sa.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("system_prompt", sa.Text(), nullable=False),
        sa.Column("user_prompt", sa.Text(), nullable=False),
        sa.Column("raw_response", sa.Text(), nullable=False),
        sa.Column("parsed_ok", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("ai_analysis_log")
