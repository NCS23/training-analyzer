"""Pydantic Schemas für User Settings (API Keys) API."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.infrastructure.database.models import AthleteModel


class UserSettingsRequest(BaseModel):
    """PATCH Request für API Key Settings.

    - Feld nicht im Body oder None → keine Änderung
    - Leerer String '' → Key löschen
    - Wert → Key verschlüsseln und speichern
    """

    claude_api_key: str | None = Field(
        None, description="Anthropic API Key (raw). None = nicht ändern, '' = löschen"
    )
    openai_api_key: str | None = Field(
        None, description="OpenAI API Key (raw). None = nicht ändern, '' = löschen"
    )


class UserSettingsResponse(BaseModel):
    """Response mit maskierten API Keys."""

    claude_api_key_masked: str | None = None
    openai_api_key_masked: str | None = None
    claude_api_key_set: bool = False
    openai_api_key_set: bool = False

    @classmethod
    def from_db(cls, model: AthleteModel) -> UserSettingsResponse:
        from app.core.encryption import decrypt_api_key, mask_api_key

        claude_masked = None
        openai_masked = None
        claude_set = False
        openai_set = False

        if model.encrypted_claude_api_key:
            try:
                raw = decrypt_api_key(model.encrypted_claude_api_key)
                claude_masked = mask_api_key(raw)
                claude_set = True
            except Exception:
                claude_set = False

        if model.encrypted_openai_api_key:
            try:
                raw = decrypt_api_key(model.encrypted_openai_api_key)
                openai_masked = mask_api_key(raw)
                openai_set = True
            except Exception:
                openai_set = False

        return cls(
            claude_api_key_masked=claude_masked,
            openai_api_key_masked=openai_masked,
            claude_api_key_set=claude_set,
            openai_api_key_set=openai_set,
        )
