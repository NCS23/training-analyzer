"""Auth-Router: Apple Sign-In, E-Mail/Passwort, Token-Refresh, Status, Logout."""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    refresh_token_expires_at,
    verify_password,
)
from app.infrastructure.database.models import RefreshTokenModel, UserModel
from app.infrastructure.database.session import get_db
from app.models.auth import (
    AppleAuthRequest,
    AuthStatusResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.apple_auth_service import validate_apple_id_token
from app.services.user_service import (
    _count_real_users,
    create_user_with_password,
    find_or_create_user_by_apple,
    find_user_by_email,
)

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
    import logging

    logger = logging.getLogger(__name__)

    try:
        claims = await validate_apple_id_token(body.id_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception("Apple Token-Validierung fehlgeschlagen: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token-Validierung fehlgeschlagen: {e}",
        ) from e

    try:
        user = await find_or_create_user_by_apple(
            db,
            apple_sub=claims.sub,
            email=claims.email,
            name=body.name,
        )
        return await _create_token_pair(db, user.id)
    except Exception as e:
        logger.exception("User-Erstellung fehlgeschlagen: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User-Erstellung fehlgeschlagen: {e}",
        ) from e


@router.post("/apple/callback")
async def apple_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Verarbeitet Apples Server-Redirect (form POST mit code + id_token)."""
    form = await request.form()
    id_token = form.get("id_token")

    if not id_token or not isinstance(id_token, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="id_token fehlt",
        )

    try:
        claims = await validate_apple_id_token(id_token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        ) from e

    user = await find_or_create_user_by_apple(
        db,
        apple_sub=claims.sub,
        email=claims.email,
        name=None,
    )
    tokens = await _create_token_pair(db, user.id)

    # Redirect zum Frontend mit Tokens im URL-Fragment (nicht sichtbar fuer Server)
    host = request.headers.get("host", "")
    scheme = "https" if request.url.scheme == "https" or "localhost" not in host else "http"
    fragment = (
        f"access_token={tokens.access_token}"
        f"&refresh_token={tokens.refresh_token}"
        f"&expires_in={tokens.expires_in}"
    )
    redirect_url = f"{scheme}://{host}/login#auth={fragment}"
    return RedirectResponse(url=redirect_url, status_code=303)


@router.post("/register", response_model=TokenResponse)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Registriert einen neuen User mit E-Mail und Passwort."""
    existing = await find_user_by_email(db, body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="E-Mail-Adresse bereits registriert",
        )

    is_first = await _count_real_users(db) == 0
    # E2E-Tests: Auto-Approve damit Smoke Tests funktionieren
    e2e_auto_approve = settings.environment == "production" and body.email.endswith(
        "@training-analyzer.app"
    )
    if is_first:
        role = "admin"
    elif e2e_auto_approve:
        role = "user"
    else:
        role = "pending"

    import logging

    logger = logging.getLogger(__name__)
    try:
        pw_hash = hash_password(body.password)
    except Exception as e:
        logger.exception("Passwort-Hashing fehlgeschlagen: %s", e)
        raise HTTPException(status_code=500, detail=f"Registrierung fehlgeschlagen: {e}") from e

    try:
        user = await create_user_with_password(
            db,
            email=body.email,
            password_hash=pw_hash,
            name=body.name,
            role=role,
        )
        return await _create_token_pair(db, user.id)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("User-Erstellung fehlgeschlagen: %s", e)
        raise HTTPException(status_code=500, detail=f"Registrierung fehlgeschlagen: {e}") from e


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authentifiziert einen User mit E-Mail und Passwort."""
    user = await find_user_by_email(db, body.email)
    if user is None or user.password_hash is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültige E-Mail oder Passwort",
        )

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültige E-Mail oder Passwort",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Konto deaktiviert",
        )

    user.last_login_at = datetime.utcnow()
    await db.commit()

    return await _create_token_pair(db, user.id)


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(request: Request) -> AuthStatusResponse:
    """Gibt den Auth-Status zurueck (fuer App-Initialisierung)."""
    host = request.headers.get("host", "")
    scheme = "https" if request.url.scheme == "https" or "localhost" not in host else "http"
    return AuthStatusResponse(
        auth_enabled=settings.auth_enabled,
        authenticated=False,
        user=None,
        apple_client_id=settings.apple_client_id if settings.auth_enabled else None,
        redirect_uri=f"{scheme}://{host}/api/v1/auth/apple/callback"
        if settings.auth_enabled
        else None,
        email_auth_enabled=True,
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
