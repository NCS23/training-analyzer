"""Add is_hidden column to exercises for soft-delete of default exercises.

When users delete a seeded default exercise, it is marked as hidden
instead of hard-deleted, so the seed function won't re-create it.

Revision ID: c040
Revises: c039
Create Date: 2026-03-21
"""

from alembic import op
import sqlalchemy as sa

revision = "c040"
down_revision = "c039"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "exercises",
        sa.Column("is_hidden", sa.Boolean(), server_default="false", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("exercises", "is_hidden")
