"""Fernet-basierte Verschlüsselung für API Keys."""

import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings


def _derive_fernet_key(secret: str) -> bytes:
    """Leite einen 32-Byte Fernet-Key aus dem App-Secret via SHA-256 ab."""
    digest = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def _get_fernet() -> Fernet:
    return Fernet(_derive_fernet_key(settings.secret_key))


def encrypt_api_key(raw_key: str) -> str:
    """Verschlüsselt einen API Key. Gibt base64-codierten Ciphertext zurück."""
    return _get_fernet().encrypt(raw_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Entschlüsselt einen API Key. Gibt den Klartext zurück."""
    return _get_fernet().decrypt(encrypted_key.encode()).decode()


def mask_api_key(raw_key: str) -> str:
    """Maskiert einen API Key für die Anzeige: Prefix + letzte 4 Zeichen."""
    if len(raw_key) <= 8:
        return "****"
    prefix = raw_key[:7]
    suffix = raw_key[-4:]
    return f"{prefix}...****{suffix}"
