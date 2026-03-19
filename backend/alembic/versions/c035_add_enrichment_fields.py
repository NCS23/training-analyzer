"""Enrichment-Felder fuer externe APIs (Wetter, Location, Luftqualitaet, Elevation).

Revision ID: c035
Revises: c034
Create Date: 2026-03-19
"""

from alembic import op
import sqlalchemy as sa

revision = "c035"
down_revision = "c034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("workouts") as batch_op:
        batch_op.add_column(sa.Column("weather_json", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("location_name", sa.String(200), nullable=True))
        batch_op.add_column(sa.Column("air_quality_json", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "elevation_corrected",
                sa.Boolean(),
                nullable=False,
                server_default="false",
            )
        )
        batch_op.add_column(
            sa.Column(
                "enrichment_status",
                sa.String(20),
                nullable=True,
                server_default="pending",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("workouts") as batch_op:
        batch_op.drop_column("enrichment_status")
        batch_op.drop_column("elevation_corrected")
        batch_op.drop_column("air_quality_json")
        batch_op.drop_column("location_name")
        batch_op.drop_column("weather_json")
