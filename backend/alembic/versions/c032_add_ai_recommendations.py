"""add ai_recommendations table

Revision ID: c032
Revises: c031
Create Date: 2026-03-17
"""

import sqlalchemy as sa
from alembic import op

revision = "c032"
down_revision = "c031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_recommendations",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "session_id",
            sa.Integer,
            sa.ForeignKey("workouts.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        ),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("target_session_id", sa.Integer, nullable=True),
        sa.Column("current_value", sa.String(100), nullable=True),
        sa.Column("suggested_value", sa.String(100), nullable=True),
        sa.Column("reasoning", sa.Text, nullable=False),
        sa.Column("priority", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ai_recommendations")
