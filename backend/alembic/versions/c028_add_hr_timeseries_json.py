"""HR-Timeseries-JSON-Spalte zur workouts-Tabelle hinzufügen.

Ermöglicht per-Sekunde HR-Daten auch ohne GPS-Track zu persistieren
(z.B. Laufband-FIT-Uploads).

Revision ID: c028
Revises: c027
Create Date: 2026-03-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c028"
down_revision: Union[str, Sequence[str], None] = "c027"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("workouts", sa.Column("hr_timeseries_json", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("workouts", "hr_timeseries_json")
