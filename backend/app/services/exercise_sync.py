"""Sync exercises from strength sessions to exercise library."""

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ExerciseModel


def _detect_set_type(exercise: dict) -> str | None:
    """Leitet den dominanten Set-Typ einer Übung aus ihren Sets ab."""
    sets = exercise.get("sets", [])
    if not sets:
        return None
    # Häufigsten Typ ermitteln
    type_counts: dict[str, int] = {}
    for s in sets:
        set_type = s.get("type", "weight_reps")
        type_counts[set_type] = type_counts.get(set_type, 0) + 1
    return max(type_counts, key=lambda t: type_counts[t])


async def sync_exercises_from_session(
    db: AsyncSession,
    exercises: list[dict],
    session_date: Optional[datetime] = None,
) -> None:
    """Sync exercise names from a strength session into the library.

    For each exercise used in the session:
    - If it exists: increment usage_count, update last_used_at, update default_set_type
    - If new: create as custom exercise with detected set type
    """
    for ex in exercises:
        name = ex.get("name", "").strip()
        category = ex.get("category", "push")
        if not name:
            continue

        detected_type = _detect_set_type(ex)

        result = await db.execute(select(ExerciseModel).where(ExerciseModel.name.ilike(name)))
        existing = result.scalar_one_or_none()

        if existing:
            existing.usage_count = (existing.usage_count or 0) + 1
            if session_date:
                existing.last_used_at = session_date
            if detected_type and not existing.default_set_type:
                existing.default_set_type = detected_type
        else:
            db.add(
                ExerciseModel(
                    name=name,
                    category=category,
                    is_custom=True,
                    is_favorite=False,
                    usage_count=1,
                    last_used_at=session_date,
                    default_set_type=detected_type,
                )
            )

    await db.flush()
