"""Add status column to planned_sessions.

Enables marking sessions as 'skipped' so compliance doesn't count them as missed.

Revision ID: c023
Revises: c022
"""

import sqlalchemy as sa

from alembic import op

revision = "c023"
down_revision = "c022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add status column with default 'active'."""
    op.add_column(
        "planned_sessions",
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
    )


def downgrade() -> None:
    """Remove status column."""
    op.drop_column("planned_sessions", "status")
