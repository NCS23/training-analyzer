"""Apple Sign-In Token-Validierung mit JWKS-Caching."""

import logging
import time
from dataclasses import dataclass, field

import httpx
from jose import JWTError, jwk, jwt  # type: ignore[import-untyped]

from app.core.config import settings

logger = logging.getLogger(__name__)

APPLE_JWKS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"
JWKS_CACHE_TTL_SECONDS = 3600  # 1 Stunde


@dataclass
class _JWKSCache:
    """In-Memory JWKS Cache mit TTL."""

    keys: list[dict[str, str]] = field(default_factory=list)
    fetched_at: float = 0.0

    @property
    def is_expired(self) -> bool:
        return time.time() - self.fetched_at > JWKS_CACHE_TTL_SECONDS


_cache = _JWKSCache()


async def _fetch_apple_jwks() -> list[dict[str, str]]:
    """Holt die aktuellen Apple JWKS Keys (mit Caching)."""
    if not _cache.is_expired and _cache.keys:
        return _cache.keys

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(APPLE_JWKS_URL)
        response.raise_for_status()
        data = response.json()

    _cache.keys = data.get("keys", [])
    _cache.fetched_at = time.time()
    logger.debug("Apple JWKS aktualisiert: %d Keys", len(_cache.keys))
    return _cache.keys


def _find_matching_key(keys: list[dict[str, str]], kid: str) -> dict[str, str] | None:
    """Findet den passenden Public Key anhand der Key-ID."""
    for key_data in keys:
        if key_data.get("kid") == kid:
            return key_data
    return None


@dataclass
class AppleTokenClaims:
    """Validierte Claims aus einem Apple Identity Token."""

    sub: str  # Apple Subject ID (eindeutig pro User)
    email: str
    email_verified: bool


async def validate_apple_id_token(id_token: str) -> AppleTokenClaims:
    """Validiert ein Apple Identity Token und extrahiert die Claims.

    Raises:
        ValueError: Bei ungueltigem Token oder fehlender Konfiguration.
    """
    if not settings.apple_client_id:
        raise ValueError("Apple Client ID nicht konfiguriert")

    # 1. Header lesen ohne Validierung (um kid zu bekommen)
    try:
        unverified_header = jwt.get_unverified_header(id_token)
    except JWTError as e:
        raise ValueError(f"Ungültiger Token-Header: {e}") from e

    kid = unverified_header.get("kid")
    if not kid:
        raise ValueError("Token-Header enthält keine Key-ID (kid)")

    # 2. Apple JWKS holen und passenden Key finden
    keys = await _fetch_apple_jwks()
    key_data = _find_matching_key(keys, kid)
    if key_data is None:
        # Cache invalidieren und nochmal versuchen
        _cache.fetched_at = 0.0
        keys = await _fetch_apple_jwks()
        key_data = _find_matching_key(keys, kid)
        if key_data is None:
            raise ValueError(f"Kein passender Apple Key gefunden fuer kid={kid}")

    # 3. Public Key konstruieren und Token verifizieren
    try:
        public_key = jwk.construct(key_data)
        payload = jwt.decode(
            id_token,
            public_key,
            algorithms=["RS256"],
            audience=settings.apple_client_id,
            issuer=APPLE_ISSUER,
        )
    except JWTError as e:
        raise ValueError(f"Token-Validierung fehlgeschlagen: {e}") from e

    # 4. Claims extrahieren
    sub = payload.get("sub")
    email = payload.get("email")
    if not sub or not email:
        raise ValueError("Token enthält keine sub oder email Claims")

    return AppleTokenClaims(
        sub=sub,
        email=email,
        email_verified=payload.get("email_verified", False),
    )
