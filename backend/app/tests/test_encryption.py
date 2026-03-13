"""Tests für API Key Verschlüsselung."""

import pytest

from app.core.encryption import decrypt_api_key, encrypt_api_key, mask_api_key


@pytest.mark.unit
def test_encrypt_decrypt_roundtrip() -> None:
    raw = "sk-ant-api03-test1234567890abcdef"
    encrypted = encrypt_api_key(raw)
    assert encrypted != raw
    decrypted = decrypt_api_key(encrypted)
    assert decrypted == raw


@pytest.mark.unit
def test_encrypt_produces_different_ciphertext() -> None:
    """Fernet produziert bei jedem Aufruf anderen Ciphertext (Nonce)."""
    raw = "sk-ant-api03-test1234567890"
    enc1 = encrypt_api_key(raw)
    enc2 = encrypt_api_key(raw)
    assert enc1 != enc2
    # Beide müssen trotzdem zum selben Klartext entschlüsseln
    assert decrypt_api_key(enc1) == raw
    assert decrypt_api_key(enc2) == raw


@pytest.mark.unit
def test_mask_api_key_standard() -> None:
    masked = mask_api_key("sk-ant-api03-abcdefghij1234")
    assert masked == "sk-ant-...****1234"


@pytest.mark.unit
def test_mask_api_key_openai() -> None:
    masked = mask_api_key("sk-proj-abc123xyz789")
    assert masked == "sk-proj...****z789"


@pytest.mark.unit
def test_mask_api_key_short() -> None:
    assert mask_api_key("short") == "****"
    assert mask_api_key("12345678") == "****"


@pytest.mark.unit
def test_mask_api_key_just_above_threshold() -> None:
    masked = mask_api_key("123456789")
    assert masked == "1234567...****6789"
