"""Admin-Router: User-Verwaltung (nur fuer Admins)."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_admin
from app.infrastructure.database.models import UserModel
from app.infrastructure.database.session import get_db
from app.models.admin import AdminUserResponse, AdminUserUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin")

VALID_ROLES = {"admin", "user", "pending"}


def _to_admin_response(user: UserModel) -> AdminUserResponse:
    """Konvertiert ein UserModel in eine AdminUserResponse."""
    return AdminUserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_active=user.is_active,
        has_password=user.password_hash is not None,
        has_apple=user.apple_sub is not None,
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _admin: UserModel = Depends(get_current_admin),
) -> list[AdminUserResponse]:
    """Listet alle User auf (nur Admin)."""
    result = await db.execute(select(UserModel).order_by(UserModel.id))
    users = result.scalars().all()
    return [_to_admin_response(u) for u in users]


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: int,
    body: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
    admin: UserModel = Depends(get_current_admin),
) -> AdminUserResponse:
    """Aktualisiert Role/Status eines Users (nur Admin, nicht sich selbst)."""
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Eigenes Konto kann nicht geändert werden",
        )

    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    if body.role is not None:
        if body.role not in VALID_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ungültige Rolle: {body.role}",
            )
        user.role = body.role

    if body.is_active is not None:
        user.is_active = body.is_active

    await db.commit()
    await db.refresh(user)
    logger.info(
        "Admin %s hat User %s aktualisiert: role=%s, active=%s",
        admin.id,
        user_id,
        user.role,
        user.is_active,
    )
    return _to_admin_response(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    admin: UserModel = Depends(get_current_admin),
) -> None:
    """Deaktiviert einen User (nur Admin, nicht sich selbst)."""
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Eigenes Konto kann nicht deaktiviert werden",
        )

    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Benutzer nicht gefunden",
        )

    user.is_active = False
    await db.commit()
    logger.info("Admin %s hat User %s deaktiviert", admin.id, user_id)
