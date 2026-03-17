"""Add weekly_reviews table for KI-Trainingsreview (E06-S06).

Revision ID: c033
Revises: c032
Create Date: 2026-03-17
"""

from alembic import op
import sqlalchemy as sa

revision = "c033"
down_revision = "c032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weekly_reviews",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("week_start", sa.Date(), nullable=False, unique=True, index=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("volume_comparison_json", sa.Text(), nullable=False),
        sa.Column("highlights_json", sa.Text(), nullable=False),
        sa.Column("improvements_json", sa.Text(), nullable=False),
        sa.Column("next_week_recommendations_json", sa.Text(), nullable=False),
        sa.Column("overall_rating", sa.String(20), nullable=False),
        sa.Column("fatigue_assessment", sa.String(20), nullable=False),
        sa.Column("session_count", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column(
            "review_created_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("weekly_reviews")
