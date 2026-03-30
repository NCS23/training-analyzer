"""Auth-Endpoints: Login, Refresh, Logout, Status."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_token,
    refresh_token_expires_at,
)
from app.infrastructure.database.models import RefreshTokenModel, UserModel
from app.infrastructure.database.session import get_db
from app.models.auth import (
    AuthStatusResponse,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth")


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status() -> AuthStatusResponse:
    """Gibt zurück ob Auth aktiviert ist und welche Provider verfügbar sind."""
    providers: list[str] = []
    if settings.apple_client_id:
        providers.append("apple")
    return AuthStatusResponse(
        auth_enabled=settings.auth_enabled,
        providers=providers,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Tauscht einen gültigen Refresh Token gegen ein neues Token-Paar."""
    token_hash = hash_token(body.refresh_token)

    result = await db.execute(
        select(RefreshTokenModel).where(
            RefreshTokenModel.token_hash == token_hash,
            RefreshTokenModel.revoked_at.is_(None),
            RefreshTokenModel.expires_at > datetime.now(timezone.utc),
        )
    )
    stored_token = result.scalar_one_or_none()

    if stored_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger oder abgelaufener Refresh Token",
        )

    # Alten Token revoken (Rotation)
    stored_token.revoked_at = datetime.now(timezone.utc)

    # Neues Token-Paar erstellen
    access_token = create_access_token(stored_token.user_id)
    new_refresh = create_refresh_token()
    new_refresh_model = RefreshTokenModel(
        user_id=stored_token.user_id,
        token_hash=hash_token(new_refresh),
        expires_at=refresh_token_expires_at(),
    )
    db.add(new_refresh_model)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout")
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Revoked den Refresh Token (Logout)."""
    token_hash = hash_token(body.refresh_token)
    await db.execute(
        update(RefreshTokenModel)
        .where(
            RefreshTokenModel.token_hash == token_hash,
            RefreshTokenModel.revoked_at.is_(None),
        )
        .values(revoked_at=datetime.now(timezone.utc))
    )
    await db.commit()
    return {"detail": "Erfolgreich ausgeloggt"}


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: UserModel = Depends(get_current_user),
) -> UserModel:
    """Gibt den aktuellen User zurück."""
    return current_user
