"""Pacing-Strategien am Ziel speichern (#528).

Revision ID: c044
Revises: c043
Create Date: 2026-03-28
"""

from alembic import op
import sqlalchemy as sa

revision = "c044"
down_revision = "c043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pacing_strategies",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "goal_id", sa.Integer, sa.ForeignKey("race_goals.id"), nullable=False, index=True
        ),
        sa.Column("strategy", sa.String(30), nullable=False),
        sa.Column("strategy_label", sa.String(50), nullable=False),
        sa.Column("distance_km", sa.Float, nullable=False),
        sa.Column("target_time_seconds", sa.Integer, nullable=False),
        sa.Column("target_time_formatted", sa.String(20), nullable=False),
        sa.Column("avg_pace_sec_per_km", sa.Float, nullable=False),
        sa.Column("avg_pace_formatted", sa.String(10), nullable=False),
        sa.Column("splits_json", sa.Text, nullable=False),
        sa.Column("weather_json", sa.Text, nullable=True),
        sa.Column("elevation_preset", sa.String(20), nullable=True),
        sa.Column("notes_json", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("pacing_strategies")
