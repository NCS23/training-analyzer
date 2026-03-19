"""Surface-JSON Feld fuer Untergrund-Analyse (Overpass API).

Revision ID: c036
Revises: c035
Create Date: 2026-03-19
"""

from alembic import op
import sqlalchemy as sa

revision = "c036"
down_revision = "c035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workouts") as batch_op:
        batch_op.add_column(sa.Column("surface_json", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("workouts") as batch_op:
        batch_op.drop_column("surface_json")
