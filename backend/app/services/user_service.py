"""User CRUD-Operationen und Apple-Login-Integration."""

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import UserModel
from app.services.data_migration_service import assign_orphaned_data

logger = logging.getLogger(__name__)


async def find_user_by_apple_sub(db: AsyncSession, apple_sub: str) -> UserModel | None:
    """Sucht einen User anhand seiner Apple Subject-ID."""
    result = await db.execute(select(UserModel).where(UserModel.apple_sub == apple_sub))
    return result.scalar_one_or_none()


async def find_user_by_email(db: AsyncSession, email: str) -> UserModel | None:
    """Sucht einen User anhand seiner E-Mail-Adresse."""
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    return result.scalar_one_or_none()


async def find_or_create_user_by_apple(
    db: AsyncSession,
    *,
    apple_sub: str,
    email: str,
    name: str | None = None,
) -> UserModel:
    """Findet oder erstellt einen User basierend auf Apple Sign-In Daten.

    Bei der Erstellung des allerersten Users werden verwaiste Daten
    (user_id=NULL) automatisch dem neuen User zugewiesen.
    """
    # 1. Suche nach apple_sub
    user = await find_user_by_apple_sub(db, apple_sub)
    if user is not None:
        user.last_login_at = datetime.now(timezone.utc)
        await db.commit()
        return user

    # 2. Suche nach E-Mail (bestehender User ohne Apple-Verknuepfung)
    user = await find_user_by_email(db, email)
    if user is not None:
        user.apple_sub = apple_sub
        user.last_login_at = datetime.now(timezone.utc)
        if name and not user.name:
            user.name = name
        await db.commit()
        return user

    # 3. Pruefen ob dies der erste User ist (fuer Daten-Migration)
    is_first_user = await get_user_count(db) == 0

    # 4. Neuen User erstellen
    user = UserModel(
        email=email,
        name=name,
        apple_sub=apple_sub,
        is_active=True,
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info("Neuer User erstellt via Apple Sign-In: id=%s, email=%s", user.id, email)

    # 5. Bei erstem User: Verwaiste Daten zuweisen
    if is_first_user:
        await assign_orphaned_data(db, user.id)

    return user


async def get_user_count(db: AsyncSession) -> int:
    """Zaehlt alle aktiven User in der Datenbank."""
    result = await db.execute(select(func.count(UserModel.id)))
    return result.scalar_one()
