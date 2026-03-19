"""Add original file storage for session reparse (#349).

Speichert die Originaldatei (CSV/FIT) bei jedem Upload, damit Sessions
nach Parser-Fixes neu geparst werden koennen ohne Re-Upload.

Revision ID: c034
Revises: c033
Create Date: 2026-03-19
"""

from alembic import op
import sqlalchemy as sa

revision = "c034"
down_revision = "c033"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("workouts", sa.Column("original_file_content", sa.LargeBinary(), nullable=True))
    op.add_column("workouts", sa.Column("original_file_name", sa.String(255), nullable=True))
    op.add_column("workouts", sa.Column("original_file_format", sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column("workouts", "original_file_format")
    op.drop_column("workouts", "original_file_name")
    op.drop_column("workouts", "original_file_content")
