"""Tests für Auth-Infrastruktur: Security, Dependencies, Endpoints."""

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
    find_user_by_email,
    get_user_count,
)

# --- Security Utils ---


class TestSecurityUtils:
    def test_create_and_decode_access_token(self) -> None:
        token = create_access_token(user_id=42)
        assert isinstance(token, str)
        assert len(token) > 20

        decoded_id = decode_access_token(token)
        assert decoded_id == 42

    def test_decode_invalid_token(self) -> None:
        assert decode_access_token("invalid.token.here") is None

    def test_decode_empty_token(self) -> None:
        assert decode_access_token("") is None

    def test_create_refresh_token(self) -> None:
        token = create_refresh_token()
        assert isinstance(token, str)
        assert len(token) >= 32

    def test_refresh_tokens_are_unique(self) -> None:
        tokens = {create_refresh_token() for _ in range(100)}
        assert len(tokens) == 100

    def test_hash_token_deterministic(self) -> None:
        token = "test-token-abc"
        assert hash_token(token) == hash_token(token)

    def test_hash_token_different_inputs(self) -> None:
        assert hash_token("token-a") != hash_token("token-b")

    def test_refresh_token_expires_at_in_future(self) -> None:
        from datetime import datetime, timezone

        expires = refresh_token_expires_at()
        assert expires > datetime.now(timezone.utc)


# --- User Service ---


class TestUserService:
    @pytest.mark.asyncio
    async def test_find_or_create_user_creates_new(self, db_session: AsyncSession) -> None:
        user, created = await find_or_create_user_by_apple(
            db_session,
            apple_sub="apple-123",
            email="test@example.com",
            name="Test User",
        )
        assert created is True
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.apple_sub == "apple-123"
        assert user.last_login_at is not None

    @pytest.mark.asyncio
    async def test_find_or_create_user_finds_existing(self, db_session: AsyncSession) -> None:
        user1, created1 = await find_or_create_user_by_apple(
            db_session,
            apple_sub="apple-456",
            email="existing@example.com",
            name="Existing",
        )
        assert created1 is True

        user2, created2 = await find_or_create_user_by_apple(
            db_session,
            apple_sub="apple-456",
            email="existing@example.com",
        )
        assert created2 is False
        assert user2.id == user1.id

    @pytest.mark.asyncio
    async def test_find_or_create_links_apple_to_email_match(
        self, db_session: AsyncSession
    ) -> None:
        # User existiert ohne apple_sub (z.B. aus Übergangsphase)
        user = UserModel(email="legacy@example.com", name="Legacy")
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        found, created = await find_or_create_user_by_apple(
            db_session,
            apple_sub="apple-789",
            email="legacy@example.com",
        )
        assert created is False
        assert found.id == user.id
        assert found.apple_sub == "apple-789"

    @pytest.mark.asyncio
    async def test_find_user_by_email(self, db_session: AsyncSession) -> None:
        user = UserModel(email="find@example.com")
        db_session.add(user)
        await db_session.commit()

        found = await find_user_by_email(db_session, "find@example.com")
        assert found is not None
        assert found.email == "find@example.com"

        not_found = await find_user_by_email(db_session, "nope@example.com")
        assert not_found is None

    @pytest.mark.asyncio
    async def test_get_user_count(self, db_session: AsyncSession) -> None:
        assert await get_user_count(db_session) == 0

        db_session.add(UserModel(email="a@b.com"))
        await db_session.commit()
        assert await get_user_count(db_session) == 1


# --- Auth Endpoints ---


class TestAuthEndpoints:
    @pytest.mark.asyncio
    async def test_auth_status(self, client: AsyncClient) -> None:
        resp = await client.get("/api/v1/auth/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "auth_enabled" in data
        assert "providers" in data

    @pytest.mark.asyncio
    async def test_get_me_without_auth_fallback(self, client: AsyncClient) -> None:
        """Wenn auth_enabled=False, sollte /me einen Fallback-User liefern."""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert "email" in data

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient) -> None:
        resp = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": "some-token"},
        )
        # Logout ist idempotent — auch mit unbekanntem Token 200
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_full_refresh_flow(self, client: AsyncClient) -> None:
        """Erstellt manuell einen User + Refresh Token, testet den Refresh-Flow."""
        from app.tests.conftest import TestSessionLocal

        async with TestSessionLocal() as db:
            user = UserModel(email="refresh@test.com")
            db.add(user)
            await db.commit()
            await db.refresh(user)

            raw_token = create_refresh_token()
            rt = RefreshTokenModel(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                expires_at=refresh_token_expires_at(),
            )
            db.add(rt)
            await db.commit()

        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": raw_token},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

        # Alter Token ist jetzt revoked
        resp2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": raw_token},
        )
        assert resp2.status_code == 401
