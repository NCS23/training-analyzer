"""Pydantic-Modelle fuer Admin User-Management."""

from datetime import datetime

from pydantic import BaseModel


class AdminUserResponse(BaseModel):
    """User-Daten fuer die Admin-Ansicht."""

    id: int
    email: str
    name: str | None
    role: str
    is_active: bool
    has_password: bool
    has_apple: bool
    created_at: datetime
    last_login_at: datetime | None

    model_config = {"from_attributes": True}


class AdminUserUpdate(BaseModel):
    """Felder die ein Admin aendern kann."""

    role: str | None = None
    is_active: bool | None = None
