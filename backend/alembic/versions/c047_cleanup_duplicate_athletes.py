"""Bereinigt doppelte Athletes nach Auth-Migration.

Zwischen dem Deploy von #624 (user_id-Filter) und #625 (orphan-migration)
konnte ein leerer Athlete mit user_id=1 erstellt werden, waehrend der
originale Athlete (mit HR, API-Keys etc.) noch user_id=NULL hatte.
Nach assign_orphaned_data existieren dann zwei Athletes pro User.

Diese Migration behaelt den Athlete mit Daten und loescht den leeren.

Revision ID: c047_cleanup_duplicate_athletes
Revises: c046_add_user_id_to_all_tables
"""

from alembic import op

revision = "c047_cleanup_duplicate_athletes"
down_revision = "c046_add_user_id_to_all_tables"


def upgrade() -> None:
    # Loescht leere Athlete-Duplikate: user_id gesetzt, aber keine Settings,
    # und es existiert ein anderer Athlete mit gleicher user_id der Settings hat.
    op.execute("""
        DELETE FROM athletes
        WHERE id IN (
            SELECT a1.id FROM athletes a1
            WHERE a1.user_id IS NOT NULL
              AND a1.resting_hr IS NULL
              AND a1.max_hr IS NULL
              AND a1.encrypted_claude_api_key IS NULL
              AND EXISTS (
                  SELECT 1 FROM athletes a2
                  WHERE a2.user_id = a1.user_id
                    AND a2.id != a1.id
                    AND (a2.resting_hr IS NOT NULL OR a2.max_hr IS NOT NULL
                         OR a2.encrypted_claude_api_key IS NOT NULL)
              )
        )
    """)


def downgrade() -> None:
    # Nicht reversibel — leere Duplikate werden geloescht
    pass
