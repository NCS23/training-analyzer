"""Fitness-Score API — Endpunkte für Score, Form, ACWR, History.

Basiert auf dem Banister Fitness-Fatigue-Modell (#675).
"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import AthleteModel, WorkoutModel
from app.infrastructure.database.session import get_db
from app.models.fitness import (
    FitnessHistoryResponse,
    FitnessScoreResponse,
    RecalculateResponse,
)
from app.services.fitness_score import (
    calculate_trimp,
    compute_full_score,
    compute_history,
)

router = APIRouter(prefix="/fitness", tags=["fitness"])


async def _get_athlete(db: AsyncSession) -> AthleteModel | None:
    result = await db.execute(select(AthleteModel).limit(1))
    return result.scalar_one_or_none()


async def _get_all_sessions(db: AsyncSession) -> list[WorkoutModel]:
    result = await db.execute(select(WorkoutModel).order_by(WorkoutModel.date.asc()))
    return list(result.scalars().all())


@router.get("/score", response_model=FitnessScoreResponse)
async def get_fitness_score(
    db: AsyncSession = Depends(get_db),
) -> FitnessScoreResponse:
    """Aktueller Fitness-Score mit Form-Indikator und ACWR."""
    athlete = await _get_athlete(db)
    sessions = await _get_all_sessions(db)

    personal_max_ctl = athlete.personal_max_ctl if athlete else None

    result = compute_full_score(sessions, personal_max_ctl)

    # Max CTL aktualisieren wenn nötig
    if athlete and result["new_max_ctl"] and result["new_max_ctl"] != personal_max_ctl:
        athlete.personal_max_ctl = result["new_max_ctl"]
        await db.commit()

    return FitnessScoreResponse(
        score=result["score"],
        endurance_score=result["endurance_score"],
        strength_score=result["strength_score"],
        trend=result["trend"],
        trend_label=result["trend_label"],
        form=result["form"],
        acwr=result["acwr"],
        context_message=result["context_message"],
        updated_at=datetime.utcnow().isoformat(),
    )


@router.get("/history", response_model=FitnessHistoryResponse)
async def get_fitness_history(
    days: int = Query(90, ge=7, le=365, description="Anzahl Tage für den Verlauf"),
    db: AsyncSession = Depends(get_db),
) -> FitnessHistoryResponse:
    """Fitness-Verlauf (CTL/ATL/TSB/Score) für Charts."""
    athlete = await _get_athlete(db)
    sessions = await _get_all_sessions(db)

    personal_max_ctl = athlete.personal_max_ctl if athlete else None
    history = compute_history(sessions, personal_max_ctl, days)

    return FitnessHistoryResponse(**history)


@router.post("/recalculate", response_model=RecalculateResponse)
async def recalculate_trimp(
    db: AsyncSession = Depends(get_db),
) -> RecalculateResponse:
    """Batch-Neuberechnung aller TRIMP-Werte.

    Nützlich nach Migration oder wenn sich die Berechnungslogik ändert.
    """
    sessions = await _get_all_sessions(db)
    count = 0

    for session in sessions:
        trimp = calculate_trimp(session)
        if trimp != session.trimp_score:
            session.trimp_score = trimp
            count += 1

    if count > 0:
        await db.commit()

    return RecalculateResponse(recalculated_sessions=count)
