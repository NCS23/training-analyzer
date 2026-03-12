"""Sync exercises from strength sessions to exercise library."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ExerciseModel


async def sync_exercises_from_session(
    db: AsyncSession,
    exercises: list[dict],
    session_date: Optional[datetime] = None,
) -> None:
    """Sync exercise names from a strength session into the library.

    For each exercise used in the session:
    - If it exists: increment usage_count, update last_used_at
    - If new: create as custom exercise
    """
    for ex in exercises:
        name = ex.get("name", "").strip()
        category = ex.get("category", "push")
        if not name:
            continue

        result = await db.execute(select(ExerciseModel).where(ExerciseModel.name.ilike(name)))
        existing = result.scalar_one_or_none()

        if existing:
            existing.usage_count = (existing.usage_count or 0) + 1
            if session_date:
                existing.last_used_at = session_date
        else:
            db.add(
                ExerciseModel(
                    name=name,
                    category=category,
                    is_custom=True,
                    is_favorite=False,
                    usage_count=1,
                    last_used_at=session_date,
                )
            )

    await db.flush()
