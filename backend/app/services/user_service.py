"""User CRUD-Operationen und Apple-Login-Integration."""

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import UserModel
from app.services.data_migration_service import assign_orphaned_data

logger = logging.getLogger(__name__)

# E-Mail des automatisch erstellten Fallback-Users (auth_enabled=False).
# Muss mit DEFAULT_USER_EMAIL in app.core.dependencies uebereinstimmen.
_FALLBACK_USER_EMAIL = "local@training-analyzer.app"


async def find_user_by_apple_sub(db: AsyncSession, apple_sub: str) -> UserModel | None:
    """Sucht einen User anhand seiner Apple Subject-ID."""
    result = await db.execute(select(UserModel).where(UserModel.apple_sub == apple_sub))
    return result.scalar_one_or_none()


async def find_user_by_email(db: AsyncSession, email: str) -> UserModel | None:
    """Sucht einen User anhand seiner E-Mail-Adresse."""
    result = await db.execute(select(UserModel).where(UserModel.email == email))
    return result.scalar_one_or_none()


async def _count_real_users(db: AsyncSession) -> int:
    """Zaehlt echte User (ohne den Fallback-User fuer auth_enabled=False)."""
    result = await db.execute(
        select(func.count(UserModel.id)).where(UserModel.email != _FALLBACK_USER_EMAIL)
    )
    return result.scalar_one()


async def find_or_create_user_by_apple(
    db: AsyncSession,
    *,
    apple_sub: str,
    email: str,
    name: str | None = None,
) -> UserModel:
    """Findet oder erstellt einen User basierend auf Apple Sign-In Daten.

    Beim ersten echten User (auch wenn ein Fallback-User existiert) werden
    verwaiste Daten (user_id=NULL) automatisch dem neuen User zugewiesen.
    So ist die Reihenfolge von auth_enabled-Aktivierung und S05-Deployment egal.
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

    # 3. Pruefen ob dies der erste echte User ist (fuer Daten-Migration).
    # Fallback-User (auth_enabled=False) zaehlt nicht als echter User.
    is_first_real_user = await _count_real_users(db) == 0

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

    # 5. Beim ersten echten User: Verwaiste Daten (user_id=NULL) zuweisen.
    # assign_orphaned_data ist idempotent — greift nur Zeilen ohne user_id an.
    if is_first_real_user:
        await assign_orphaned_data(db, user.id)

    return user


async def get_user_count(db: AsyncSession) -> int:
    """Zaehlt alle User in der Datenbank."""
    result = await db.execute(select(func.count(UserModel.id)))
    return result.scalar_one()
