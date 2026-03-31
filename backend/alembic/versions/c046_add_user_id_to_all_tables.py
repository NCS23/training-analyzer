"""Add user_id FK to all existing tables.

Revision ID: c046_add_user_id_to_all_tables
Revises: c045_add_users_and_refresh_tokens
Create Date: 2026-03-30
"""

from alembic import op
import sqlalchemy as sa

revision = "c046_add_user_id_to_all_tables"
down_revision = "c045_add_users_and_refresh_tokens"
branch_labels = None
depends_on = None

TABLES = [
    "workouts", "athletes", "threshold_tests", "exercises", "session_templates",
    "race_goals", "pacing_strategies", "training_routes", "training_plans",
    "training_phases", "weekly_plan_days", "planned_sessions", "ai_analysis_log",
    "plan_changelog", "ai_recommendations", "weekly_reviews", "chat_conversations",
]


def upgrade() -> None:
    for table in TABLES:
        op.add_column(table, sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True))


def downgrade() -> None:
    for table in reversed(TABLES):
        op.drop_column(table, "user_id")
