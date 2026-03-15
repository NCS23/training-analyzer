"""fix workout_id nullable — c030 was recorded but ALTER failed

init_db()._ensure_columns_exist() added use_case/context_label
before Alembic c030 could run its add_column calls, causing c030
to fail. But alembic_version was already at c030, so the
alter_column for workout_id was never applied.

Revision ID: c031
Revises: c030
Create Date: 2026-03-15
"""

import sqlalchemy as sa
from alembic import op

revision = "c031"
down_revision = "c030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "ai_analysis_log", "workout_id", existing_type=sa.Integer(), nullable=True
    )


def downgrade() -> None:
    op.alter_column(
        "ai_analysis_log", "workout_id", existing_type=sa.Integer(), nullable=False
    )
