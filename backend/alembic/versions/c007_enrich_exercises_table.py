"""enrich exercises table with instructions, muscles, images, metadata

Revision ID: c007
Revises: c006
Create Date: 2026-02-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c007"
down_revision: Union[str, Sequence[str], None] = "c006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add enrichment columns to exercises table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_columns = {c["name"] for c in inspector.get_columns("exercises")}

    new_columns = [
        ("instructions_json", sa.Text()),
        ("primary_muscles_json", sa.Text()),
        ("secondary_muscles_json", sa.Text()),
        ("image_urls_json", sa.Text()),
        ("equipment", sa.String(50)),
        ("level", sa.String(20)),
        ("force", sa.String(20)),
        ("mechanic", sa.String(20)),
        ("exercise_db_id", sa.String(100)),
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_columns:
            op.add_column("exercises", sa.Column(col_name, col_type, nullable=True))


def downgrade() -> None:
    """Remove enrichment columns from exercises table."""
    columns_to_drop = [
        "instructions_json",
        "primary_muscles_json",
        "secondary_muscles_json",
        "image_urls_json",
        "equipment",
        "level",
        "force",
        "mechanic",
        "exercise_db_id",
    ]
    for col_name in columns_to_drop:
        op.drop_column("exercises", col_name)
