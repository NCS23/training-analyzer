"""generalize ai_analysis_log for all use cases

Revision ID: c030
Revises: c029
Create Date: 2026-03-15
"""

from alembic import op
import sqlalchemy as sa

revision = "c030"
down_revision = "c029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("ai_analysis_log", "workout_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("ai_analysis_log", sa.Column("use_case", sa.String(50), nullable=False, server_default="session_analysis"))
    op.add_column("ai_analysis_log", sa.Column("context_label", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("ai_analysis_log", "context_label")
    op.drop_column("ai_analysis_log", "use_case")
    op.alter_column("ai_analysis_log", "workout_id", existing_type=sa.Integer(), nullable=False)
