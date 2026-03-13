"""Verschlüsselte API-Key-Spalten zur athletes-Tabelle hinzufügen.

Revision ID: c027
Revises: c026
Create Date: 2026-03-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c027"
down_revision: Union[str, Sequence[str], None] = "c026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = [c["name"] for c in inspector.get_columns("athletes")]

    if "encrypted_claude_api_key" not in existing:
        op.add_column(
            "athletes",
            sa.Column("encrypted_claude_api_key", sa.Text(), nullable=True),
        )
    if "encrypted_openai_api_key" not in existing:
        op.add_column(
            "athletes",
            sa.Column("encrypted_openai_api_key", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("athletes", "encrypted_openai_api_key")
    op.drop_column("athletes", "encrypted_claude_api_key")
