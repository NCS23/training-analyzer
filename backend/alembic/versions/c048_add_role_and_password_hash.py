"""Fuegt role und password_hash Spalten zur users-Tabelle hinzu.

Bestehende User bekommen role='user'. Der erste echte User
(nicht der Fallback-User) wird zum Admin befördert.

Revision ID: c048_add_role_and_password_hash
Revises: c047_cleanup_duplicate_athletes
"""

import sqlalchemy as sa
from alembic import op

revision = "c048_add_role_and_password_hash"
down_revision = "c047_cleanup_duplicate_athletes"


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(20), server_default="user", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(255), nullable=True),
    )

    # Ersten echten User (nicht den Fallback) zum Admin machen
    op.execute(
        """
        UPDATE users SET role = 'admin'
        WHERE id = (
            SELECT MIN(id) FROM users
            WHERE email != 'local@training-analyzer.app'
        )
        """
    )


def downgrade() -> None:
    op.drop_column("users", "password_hash")
    op.drop_column("users", "role")
