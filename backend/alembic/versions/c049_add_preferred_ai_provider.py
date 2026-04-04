"""Fügt preferred_ai_provider Spalte zur athletes-Tabelle hinzu.

NULL = System-Default (claude). Gültige Werte: 'claude', 'openai'.

Revision ID: c049_add_preferred_ai_provider
Revises: c048_add_role_and_password_hash
"""

import sqlalchemy as sa
from alembic import op

revision = "c049_add_preferred_ai_provider"
down_revision = "c048_add_role_and_password_hash"


def upgrade() -> None:
    op.add_column(
        "athletes",
        sa.Column("preferred_ai_provider", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("athletes", "preferred_ai_provider")
