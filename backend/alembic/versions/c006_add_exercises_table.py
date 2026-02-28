"""add exercises library table

Revision ID: c006
Revises: c005
Create Date: 2026-02-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c006"
down_revision: Union[str, Sequence[str], None] = "c005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create exercises table for exercise library."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if "exercises" not in inspector.get_table_names():
        op.create_table(
            "exercises",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(100), nullable=False, unique=True),
            sa.Column("category", sa.String(20), nullable=False),
            sa.Column(
                "is_favorite",
                sa.Boolean(),
                nullable=False,
                server_default="0",
            ),
            sa.Column(
                "is_custom",
                sa.Boolean(),
                nullable=False,
                server_default="1",
            ),
            sa.Column("usage_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("last_used_at", sa.DateTime(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )


def downgrade() -> None:
    """Drop exercises table."""
    op.drop_table("exercises")
