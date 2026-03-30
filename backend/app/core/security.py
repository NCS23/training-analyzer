"""JWT-Utilities für Access- und Refresh-Tokens."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt  # type: ignore[import-untyped]

from app.core.config import settings


def create_access_token(user_id: int) -> str:
    """Erzeugt ein kurzlebiges Access Token (default: 15 Min)."""
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "exp": expires,
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token() -> str:
    """Erzeugt einen kryptographisch sicheren Refresh Token (opaker String)."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """SHA-256 Hash eines Tokens (für DB-Speicherung)."""
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> int | None:
    """Decodiert ein Access Token und gibt die user_id zurück. None bei ungültigem Token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "access":
            return None
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        return int(user_id_str)
    except (JWTError, ValueError):
        return None


def refresh_token_expires_at() -> datetime:
    """Berechnet das Ablaufdatum für einen neuen Refresh Token."""
    return datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
