"""Fix auto-created exercises: set is_custom=True for deletability.

Auto-created drill/stride exercises from plan generation were created
with is_custom=False, preventing users from deleting them.

Revision ID: c039
Revises: c038
Create Date: 2026-03-21
"""

from alembic import op

revision = "c039"
down_revision = "c038"
branch_labels = None
depends_on = None


# Exercises auto-created by plan_generator / _ensure_exercises_exist
_AUTO_CREATED_NAMES = [
    "Steigerungslauf",
    "Steigerungslauf 100m",
    "Steigerungslauf 80m",
    "Koordinationsleiter",
    "Überkreuzlauf",
    "Seitgalopp",
    "Hopserlauf",
    "Kniehebelauf",
    "Anfersen",
    "Skippings",
    "Fußgelenksarbeit",
    "Prellhopser",
    "Sprunglauf",
]


def upgrade() -> None:
    # Set is_custom=True for auto-created exercises so they can be deleted
    names_sql = ", ".join(f"'{n}'" for n in _AUTO_CREATED_NAMES)
    op.execute(
        f"UPDATE exercises SET is_custom = true WHERE name IN ({names_sql}) AND is_custom = false"
    )


def downgrade() -> None:
    names_sql = ", ".join(f"'{n}'" for n in _AUTO_CREATED_NAMES)
    op.execute(
        f"UPDATE exercises SET is_custom = false WHERE name IN ({names_sql}) AND is_custom = true"
    )
