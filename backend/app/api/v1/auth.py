"""Auth-Router: Apple Sign-In, Token-Refresh, Status, Logout."""

import logging
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
    AppleAuthRequest,
    AuthStatusResponse,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from app.services.apple_auth_service import validate_apple_id_token
from app.services.user_service import find_or_create_user_by_apple

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth")


async def _create_token_pair(db: AsyncSession, user_id: int) -> TokenResponse:
    """Erstellt ein Access/Refresh-Token-Paar und speichert den Refresh-Token."""
    access_token = create_access_token(user_id)
    raw_refresh = create_refresh_token()

    refresh_entry = RefreshTokenModel(
        user_id=user_id,
        token_hash=hash_token(raw_refresh),
        expires_at=refresh_token_expires_at(),
    )
    db.add(refresh_entry)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/apple", response_model=TokenResponse)
async def apple_sign_in(
    body: AppleAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authentifiziert einen User via Apple Sign-In."""
    try:
        claims = await validate_apple_id_token(body.id_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e

    user = await find_or_create_user_by_apple(
        db,
        apple_sub=claims.sub,
        email=claims.email,
        name=body.name,
    )
    return await _create_token_pair(db, user.id)


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status() -> AuthStatusResponse:
    """Gibt den Auth-Status zurueck (fuer App-Initialisierung)."""
    return AuthStatusResponse(
        auth_enabled=settings.auth_enabled,
        authenticated=False,
        user=None,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Erneuert Access- und Refresh-Token."""
    token_hash = hash_token(body.refresh_token)

    result = await db.execute(
        select(RefreshTokenModel).where(
            RefreshTokenModel.token_hash == token_hash,
            RefreshTokenModel.revoked_at.is_(None),
            RefreshTokenModel.expires_at > datetime.now(timezone.utc),
        )
    )
    refresh_entry = result.scalar_one_or_none()

    if refresh_entry is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiges oder abgelaufenes Refresh-Token",
        )

    # Altes Token revoken (Rotation)
    refresh_entry.revoked_at = datetime.now(timezone.utc)

    # Neues Token-Paar erstellen
    return await _create_token_pair(db, refresh_entry.user_id)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Loggt den User aus (revoked das Refresh-Token)."""
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


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: UserModel = Depends(get_current_user),
) -> UserResponse:
    """Gibt die Daten des aktuellen Users zurueck."""
    return UserResponse.model_validate(current_user)
