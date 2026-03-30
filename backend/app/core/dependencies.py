"""FastAPI Dependencies für Authentifizierung."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token
from app.infrastructure.database.models import UserModel
from app.infrastructure.database.session import get_db

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserModel:
    """Extrahiert den aktuellen User aus dem Bearer Token.

    Wenn auth_enabled=False (Übergangsphase), wird None-Token toleriert
    und der erste User zurückgegeben (Single-User-Kompatibilität).
    """
    if not settings.auth_enabled:
        return await _get_fallback_user(db)

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nicht authentifiziert",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiger oder abgelaufener Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(UserModel).where(UserModel.id == user_id, UserModel.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Benutzer nicht gefunden oder deaktiviert",
        )
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserModel | None:
    """Wie get_current_user, aber gibt None statt 401 zurück."""
    if credentials is None:
        if not settings.auth_enabled:
            return await _get_fallback_user(db)
        return None

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        return None

    result = await db.execute(
        select(UserModel).where(UserModel.id == user_id, UserModel.is_active.is_(True))
    )
    return result.scalar_one_or_none()


async def _get_fallback_user(db: AsyncSession) -> UserModel:
    """Fallback für auth_enabled=False: Gibt den ersten User zurück oder erstellt einen."""
    result = await db.execute(select(UserModel).limit(1))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    # Kein User vorhanden — erstelle Default-User für Übergangsphase
    user = UserModel(email="local@training-analyzer.dev", name="Lokaler Benutzer")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
