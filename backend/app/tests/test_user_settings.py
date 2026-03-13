"""Tests für User Settings API (API Keys)."""

import pytest
from httpx import AsyncClient


@pytest.mark.unit
async def test_get_user_settings_empty(client: AsyncClient) -> None:
    """GET ohne gespeicherte Keys gibt leere Settings zurück."""
    response = await client.get("/api/v1/user/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["claude_api_key_set"] is False
    assert data["openai_api_key_set"] is False
    assert data["claude_api_key_masked"] is None
    assert data["openai_api_key_masked"] is None


@pytest.mark.unit
async def test_set_claude_key(client: AsyncClient) -> None:
    """PATCH setzt Claude Key und gibt maskierte Version zurück."""
    response = await client.patch(
        "/api/v1/user/settings",
        json={"claude_api_key": "sk-ant-api03-testkey1234"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["claude_api_key_set"] is True
    assert "****" in data["claude_api_key_masked"]
    assert "1234" in data["claude_api_key_masked"]
    # Raw Key darf NICHT in Response sein
    assert "testkey" not in str(data)


@pytest.mark.unit
async def test_set_openai_key(client: AsyncClient) -> None:
    """PATCH setzt OpenAI Key."""
    response = await client.patch(
        "/api/v1/user/settings",
        json={"openai_api_key": "sk-proj-abc123xyz5678"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["openai_api_key_set"] is True
    assert data["claude_api_key_set"] is False


@pytest.mark.unit
async def test_clear_api_key(client: AsyncClient) -> None:
    """Leerer String löscht den Key."""
    # Erst setzen
    await client.patch(
        "/api/v1/user/settings",
        json={"claude_api_key": "sk-ant-test1234"},
    )
    # Dann löschen
    response = await client.patch(
        "/api/v1/user/settings",
        json={"claude_api_key": ""},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["claude_api_key_set"] is False
    assert data["claude_api_key_masked"] is None


@pytest.mark.unit
async def test_partial_update_preserves_other_key(client: AsyncClient) -> None:
    """Nur Claude setzen → OpenAI bleibt unverändert (und umgekehrt)."""
    # Claude setzen
    await client.patch(
        "/api/v1/user/settings",
        json={"claude_api_key": "sk-ant-xxx1234"},
    )
    # OpenAI setzen — Claude sollte bleiben
    response = await client.patch(
        "/api/v1/user/settings",
        json={"openai_api_key": "sk-openai-xxx5678"},
    )
    data = response.json()
    assert data["claude_api_key_set"] is True
    assert data["openai_api_key_set"] is True


@pytest.mark.unit
async def test_get_after_set(client: AsyncClient) -> None:
    """GET nach PATCH zeigt den gesetzten Key."""
    await client.patch(
        "/api/v1/user/settings",
        json={"claude_api_key": "sk-ant-api03-persisttest9999"},
    )
    response = await client.get("/api/v1/user/settings")
    assert response.status_code == 200
    data = response.json()
    assert data["claude_api_key_set"] is True
    assert "9999" in data["claude_api_key_masked"]
