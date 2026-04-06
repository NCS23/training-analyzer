"""Daten-Migration: Verwaiste Datensaetze (user_id=NULL) dem ersten User zuweisen."""

import logging

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import (
    AIAnalysisLogModel,
    AIRecommendationModel,
    AthleteModel,
    ChatConversationModel,
    ExerciseModel,
    PacingStrategyModel,
    PlanChangeLogModel,
    PlannedSessionModel,
    RaceGoalModel,
    SessionTemplateModel,
    ThresholdTestModel,
    TrainingPhaseModel,
    TrainingPlanModel,
    TrainingRouteModel,
    WeeklyPlanDayModel,
    WeeklyReviewModel,
    WorkoutModel,
)

logger = logging.getLogger(__name__)

# Alle Tabellen mit user_id Spalte, die migriert werden muessen
_TABLES_WITH_USER_ID = [
    WorkoutModel,
    AthleteModel,
    ThresholdTestModel,
    ExerciseModel,
    SessionTemplateModel,
    RaceGoalModel,
    PacingStrategyModel,
    TrainingRouteModel,
    TrainingPlanModel,
    TrainingPhaseModel,
    WeeklyPlanDayModel,
    PlannedSessionModel,
    AIAnalysisLogModel,
    PlanChangeLogModel,
    AIRecommendationModel,
    WeeklyReviewModel,
    ChatConversationModel,
]


async def reassign_user_data(
    db: AsyncSession, from_user_id: int, to_user_id: int
) -> dict[str, int]:
    """Weist alle Daten eines Users einem anderen zu (z.B. Fallback → echter User)."""
    from sqlalchemy import update as sql_update

    counts: dict[str, int] = {}
    for model in _TABLES_WITH_USER_ID:
        result = await db.execute(
            sql_update(model)
            .where(model.user_id == from_user_id)  # type: ignore[attr-defined]
            .values(user_id=to_user_id)
        )
        count = getattr(result, "rowcount", 0) or 0
        if count > 0:
            counts[model.__tablename__] = count

    await db.commit()
    logger.info("Datentransfer: user_id=%s → user_id=%s: %s", from_user_id, to_user_id, counts)
    return counts


async def assign_orphaned_data(db: AsyncSession, user_id: int) -> dict[str, int]:
    """Weist alle Datensaetze mit user_id=NULL dem gegebenen User zu.

    Wird automatisch beim Erstellen des ersten Users aufgerufen,
    um bestehende Daten (vor Auth-Einfuehrung) dem User zuzuordnen.

    Returns:
        Dict mit Tabellennamen und Anzahl der aktualisierten Zeilen.
    """
    results: dict[str, int] = {}

    for model in _TABLES_WITH_USER_ID:
        table_name = model.__tablename__
        stmt = (
            update(model)
            .where(model.user_id.is_(None))  # type: ignore[attr-defined]
            .values(user_id=user_id)
        )
        result = await db.execute(stmt)
        count = result.rowcount  # type: ignore[attr-defined]
        if count > 0:
            results[table_name] = count
            logger.info(
                "Daten-Migration: %d Zeilen in '%s' dem User %d zugewiesen",
                count,
                table_name,
                user_id,
            )

    await db.commit()

    total = sum(results.values())
    logger.info(
        "Daten-Migration abgeschlossen: %d Zeilen in %d Tabellen zugewiesen",
        total,
        len(results),
    )
    return results
