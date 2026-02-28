"""add elevation correction factor to athletes

Revision ID: c005
Revises: c004
Create Date: 2026-02-27

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c005"
down_revision: Union[str, Sequence[str], None] = "c004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add elevation correction factors to athletes table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = [c["name"] for c in inspector.get_columns("athletes")]

    if "elevation_gain_factor" not in existing:
        op.add_column(
            "athletes",
            sa.Column("elevation_gain_factor", sa.Float(), nullable=True, server_default="10.0"),
        )
    if "elevation_loss_factor" not in existing:
        op.add_column(
            "athletes",
            sa.Column("elevation_loss_factor", sa.Float(), nullable=True, server_default="5.0"),
        )


def downgrade() -> None:
    """Remove elevation correction factor columns."""
    op.drop_column("athletes", "elevation_loss_factor")
    op.drop_column("athletes", "elevation_gain_factor")
