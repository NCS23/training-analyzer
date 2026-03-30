"""Pydantic Models für Auth-Endpoints."""

from pydantic import BaseModel


class AppleAuthRequest(BaseModel):
    """Request Body für Apple Sign-In."""

    id_token: str
    authorization_code: str | None = None


class TokenResponse(BaseModel):
    """JWT Token-Paar als Response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Sekunden bis Access Token abläuft


class RefreshRequest(BaseModel):
    """Request für Token-Refresh."""

    refresh_token: str


class UserResponse(BaseModel):
    """Öffentliche User-Daten."""

    id: int
    email: str
    name: str | None
    avatar_url: str | None

    model_config = {"from_attributes": True}


class AuthStatusResponse(BaseModel):
    """Gibt den Auth-Status der Instanz zurück."""

    auth_enabled: bool
    providers: list[str]
