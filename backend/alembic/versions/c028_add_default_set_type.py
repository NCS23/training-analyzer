"""default_set_type Spalte zur exercises-Tabelle hinzufügen.

Speichert den Standard-Set-Typ einer Übung (z.B. duration für Plank).

Revision ID: c028
Revises: c027
Create Date: 2026-03-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c028"
down_revision: Union[str, Sequence[str], None] = "c027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exercises",
        sa.Column("default_set_type", sa.String(30), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("exercises", "default_set_type")
