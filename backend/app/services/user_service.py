"""User CRUD Operationen."""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import UserModel


async def find_user_by_apple_sub(db: AsyncSession, apple_sub: str) -> UserModel | None:
    """Findet einen User anhand seiner Apple Subject ID."""
    result = await db.execute(select(UserModel).where(UserModel.apple_sub == apple_sub))
    return result.scalar_one_or_none()


async def find_user_by_email(db: AsyncSession, email: str) -> UserModel | None:
    """Findet einen User anhand seiner E-Mail-Adresse."""
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    return result.scalar_one_or_none()


async def find_or_create_user_by_apple(
    db: AsyncSession,
    *,
    apple_sub: str,
    email: str,
    name: str | None = None,
) -> tuple[UserModel, bool]:
    """Findet oder erstellt einen User nach Apple Sign-In.

    Returns:
        Tuple von (user, created) — created=True wenn neuer User.
    """
    # Erst nach apple_sub suchen (stabiler als E-Mail)
    user = await find_user_by_apple_sub(db, apple_sub)
    if user is not None:
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()
        return user, False

    # Fallback: E-Mail-Match (User existiert evtl. aus Übergangsphase)
    user = await find_user_by_email(db, email)
    if user is not None:
        user.apple_sub = apple_sub
        if name and not user.name:
            user.name = name
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()
        return user, False

    # Neuer User
    user = UserModel(
        email=email,
        name=name,
        apple_sub=apple_sub,
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, True


async def get_user_count(db: AsyncSession) -> int:
    """Anzahl der User in der Datenbank."""
    result = await db.execute(select(UserModel))
    return len(result.scalars().all())
