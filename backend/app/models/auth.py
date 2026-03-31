"""Pydantic-Modelle fuer Authentifizierung und User-Management."""

from datetime import datetime

from pydantic import BaseModel, Field


class AppleAuthRequest(BaseModel):
    """Request-Body fuer Apple Sign-In."""

    id_token: str = Field(..., description="Apple Identity Token (JWT)")
    authorization_code: str = Field(..., description="Apple Authorization Code")
    name: str | None = Field(default=None, description="Name des Users (nur beim ersten Login)")


class TokenResponse(BaseModel):
    """Response mit Access- und Refresh-Token."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access-Token Ablaufzeit in Sekunden")


class RefreshRequest(BaseModel):
    """Request-Body fuer Token-Refresh."""

    refresh_token: str


class UserResponse(BaseModel):
    """Oeffentliche User-Daten."""

    id: int
    email: str
    name: str | None = None
    avatar_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthStatusResponse(BaseModel):
    """Auth-Status fuer die App-Initialisierung."""

    auth_enabled: bool
    authenticated: bool
    user: UserResponse | None = None
