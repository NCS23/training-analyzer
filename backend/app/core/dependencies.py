"""FastAPI Auth-Dependencies fuer Dependency Injection."""

import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import decode_access_token
from app.infrastructure.database.models import UserModel
from app.infrastructure.database.session import get_db

logger = logging.getLogger(__name__)

# Optional bearer scheme — auto_error=False damit es nicht 403 wirft wenn kein Token da ist
_bearer_scheme = HTTPBearer(auto_error=False)

DEFAULT_USER_EMAIL = "local@training-analyzer.app"


async def _ensure_default_user(db: AsyncSession) -> UserModel:
    """Erstellt oder findet den Default-User fuer auth_enabled=False Betrieb."""
    result = await db.execute(select(UserModel).where(UserModel.email == DEFAULT_USER_EMAIL))
    user = result.scalar_one_or_none()
    if user is not None:
        return user

    user = UserModel(email=DEFAULT_USER_EMAIL, name="Lokaler Benutzer", is_active=True)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("Default-User erstellt (auth_enabled=False): id=%s", user.id)
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserModel:
    """Gibt den aktuellen User zurueck.

    - Bei auth_enabled=False: Default-User (automatisch erstellt)
    - Bei auth_enabled=True: JWT-basierte Authentifizierung
    """
    if not settings.auth_enabled:
        return await _ensure_default_user(db)

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentifizierung erforderlich",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültiges oder abgelaufenes Token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Benutzer nicht gefunden oder deaktiviert",
        )
    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserModel | None:
    """Optionale Authentifizierung — gibt None zurueck wenn kein Token vorhanden."""
    if not settings.auth_enabled:
        return await _ensure_default_user(db)

    if credentials is None:
        return None

    user_id = decode_access_token(credentials.credentials)
    if user_id is None:
        return None

    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        return None
    return user
