"""JWT-Utilities fuer Access- und Refresh-Tokens, Passwort-Hashing."""

import hashlib
import secrets
from datetime import datetime, timedelta

from jose import JWTError, jwt  # type: ignore[import-untyped]
from passlib.context import CryptContext  # type: ignore[import-untyped]

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hasht ein Passwort mit bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifiziert ein Passwort gegen einen bcrypt-Hash."""
    return pwd_context.verify(plain_password, hashed_password)  # type: ignore[no-any-return]


def create_access_token(user_id: int) -> str:
    """Erstellt ein kurzlebiges Access-Token (JWT) fuer den gegebenen User."""
    expires = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "exp": expires, "type": "access"}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_refresh_token() -> str:
    """Erstellt ein kryptographisch sicheres Refresh-Token."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Hasht ein Token mit SHA-256 fuer die Datenbank-Speicherung."""
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> int | None:
    """Dekodiert ein Access-Token und gibt die User-ID zurueck, oder None bei Fehler."""
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
    """Berechnet den Ablaufzeitpunkt fuer ein neues Refresh-Token."""
    return datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
