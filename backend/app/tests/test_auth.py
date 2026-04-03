"""Tests fuer Auth: Security Utils, User Service, Auth Endpoints."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_token,
    refresh_token_expires_at,
)
from app.infrastructure.database.models import RefreshTokenModel, UserModel
from app.services.user_service import (
    find_or_create_user_by_apple,
    find_user_by_apple_sub,
    find_user_by_email,
    get_user_count,
)

# ---------------------------------------------------------------------------
# Security Utils
# ---------------------------------------------------------------------------


class TestSecurityUtils:
    """Tests fuer JWT und Token-Utilities."""

    def test_create_and_decode_access_token(self) -> None:
        token = create_access_token(42)
        assert isinstance(token, str)
        user_id = decode_access_token(token)
        assert user_id == 42

    def test_decode_invalid_token_returns_none(self) -> None:
        assert decode_access_token("invalid.token.here") is None

    def test_decode_empty_token_returns_none(self) -> None:
        assert decode_access_token("") is None

    def test_create_refresh_token_is_unique(self) -> None:
        t1 = create_refresh_token()
        t2 = create_refresh_token()
        assert t1 != t2
        assert len(t1) > 30

    def test_hash_token_deterministic(self) -> None:
        token = "test-token-123"
        assert hash_token(token) == hash_token(token)

    def test_hash_token_different_for_different_tokens(self) -> None:
        assert hash_token("token-a") != hash_token("token-b")

    def test_refresh_token_expires_at_in_future(self) -> None:
        expires = refresh_token_expires_at()
        assert expires > datetime.utcnow()


# ---------------------------------------------------------------------------
# User Service
# ---------------------------------------------------------------------------


class TestUserService:
    """Tests fuer User CRUD Operationen."""

    @pytest.mark.asyncio
    async def test_find_user_by_apple_sub_not_found(self, db_session: AsyncSession) -> None:
        result = await find_user_by_apple_sub(db_session, "nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_find_user_by_email_not_found(self, db_session: AsyncSession) -> None:
        result = await find_user_by_email(db_session, "no@one.com")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_user_count_with_fallback(self, db_session: AsyncSession) -> None:
        # conftest pre-creates the fallback user
        count = await get_user_count(db_session)
        assert count == 1

    @pytest.mark.asyncio
    async def test_find_or_create_user_creates_new(self, db_session: AsyncSession) -> None:
        with patch(
            "app.services.user_service.assign_orphaned_data",
            new_callable=AsyncMock,
        ) as mock_migrate:
            user = await find_or_create_user_by_apple(
                db_session,
                apple_sub="apple-sub-123",
                email="test@example.com",
                name="Test User",
            )
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.apple_sub == "apple-sub-123"
        assert user.name == "Test User"
        # Erster User → Daten-Migration aufgerufen
        mock_migrate.assert_called_once_with(db_session, user.id)

    @pytest.mark.asyncio
    async def test_find_or_create_user_finds_existing(self, db_session: AsyncSession) -> None:
        # Erst User erstellen
        user = UserModel(email="existing@test.com", apple_sub="sub-existing", is_active=True)
        db_session.add(user)
        await db_session.commit()

        # Dann via Service suchen
        found = await find_or_create_user_by_apple(
            db_session, apple_sub="sub-existing", email="existing@test.com"
        )
        assert found.id == user.id
        assert found.last_login_at is not None

    @pytest.mark.asyncio
    async def test_find_or_create_links_apple_to_existing_email(
        self, db_session: AsyncSession
    ) -> None:
        # User ohne Apple-Sub erstellen
        user = UserModel(email="link@test.com", is_active=True)
        db_session.add(user)
        await db_session.commit()

        # Via Apple einloggen → sollte verknuepft werden
        found = await find_or_create_user_by_apple(
            db_session, apple_sub="new-apple-sub", email="link@test.com", name="Linked"
        )
        assert found.id == user.id
        assert found.apple_sub == "new-apple-sub"


# ---------------------------------------------------------------------------
# Auth Endpoints
# ---------------------------------------------------------------------------


class TestAuthEndpoints:
    """Tests fuer Auth API Endpoints."""

    @pytest.mark.asyncio
    async def test_auth_status(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/auth/status")
        assert response.status_code == 200
        data = response.json()
        assert "auth_enabled" in data
        assert "authenticated" in data

    @pytest.mark.asyncio
    async def test_auth_me_without_auth(self, client: AsyncClient) -> None:
        """Ohne Auth-Header sollte der Default-User zurueckgegeben werden (auth_enabled=False)."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "local@training-analyzer.app"

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_unknown_token(self, client: AsyncClient) -> None:
        """Logout mit unbekanntem Token ist idempotent (204)."""
        response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "unknown-token"},
        )
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_apple_sign_in_missing_config(self, client: AsyncClient) -> None:
        """Apple Sign-In ohne konfigurierte Client-ID schlaegt fehl."""
        response = await client.post(
            "/api/v1/auth/apple",
            json={
                "id_token": "fake-token",
                "authorization_code": "fake-code",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_rotation(
        self, client: AsyncClient, db_session: AsyncSession
    ) -> None:
        """Refresh-Token Rotation: Altes Token wird revoked, neues erstellt."""
        # User erstellen
        user = UserModel(email="rotation@test.com", is_active=True)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        # Refresh-Token manuell erstellen
        raw_token = create_refresh_token()
        refresh_entry = RefreshTokenModel(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.utcnow() + timedelta(days=30),
        )
        db_session.add(refresh_entry)
        await db_session.commit()

        # Token refreshen
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": raw_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # Neues Refresh-Token ist anders
        assert data["refresh_token"] != raw_token
