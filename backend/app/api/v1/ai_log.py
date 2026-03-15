"""API-Endpoints fuer KI Analyse-Log."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import AIAnalysisLogModel, WorkoutModel
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/ai/log")


class AILogListEntry(BaseModel):
    """Kurzform fuer Liste."""

    id: int
    workout_id: int
    created_at: datetime
    provider: str
    parsed_ok: bool
    duration_ms: int | None
    session_date: str
    session_type: str


class AILogDetail(AILogListEntry):
    """Vollstaendiger Eintrag mit Prompts und Response."""

    system_prompt: str
    user_prompt: str
    raw_response: str


class AILogListResponse(BaseModel):
    """Paginierte Antwort."""

    items: list[AILogListEntry]
    total: int


@router.get("", response_model=AILogListResponse)
async def list_ai_logs(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AILogListResponse:
    """Paginierte Liste aller KI-Analyse-Logs (neueste zuerst)."""
    # Total count
    count_result = await db.execute(select(func.count(AIAnalysisLogModel.id)))
    total = count_result.scalar_one()

    # Logs mit Workout-Daten joinen
    stmt = (
        select(AIAnalysisLogModel, WorkoutModel.date, WorkoutModel.workout_type)
        .join(WorkoutModel, AIAnalysisLogModel.workout_id == WorkoutModel.id)
        .order_by(AIAnalysisLogModel.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for log, w_date, w_type in rows:
        session_date = w_date.date().isoformat() if isinstance(w_date, datetime) else str(w_date)
        items.append(
            AILogListEntry(
                id=log.id,
                workout_id=log.workout_id,
                created_at=log.created_at,
                provider=log.provider,
                parsed_ok=log.parsed_ok,
                duration_ms=log.duration_ms,
                session_date=session_date,
                session_type=str(w_type),
            )
        )

    return AILogListResponse(items=items, total=total)


@router.get("/{log_id}", response_model=AILogDetail)
async def get_ai_log_detail(
    log_id: int,
    db: AsyncSession = Depends(get_db),
) -> AILogDetail:
    """Einzelner Log-Eintrag mit vollem Prompt und Response."""
    stmt = (
        select(AIAnalysisLogModel, WorkoutModel.date, WorkoutModel.workout_type)
        .join(WorkoutModel, AIAnalysisLogModel.workout_id == WorkoutModel.id)
        .where(AIAnalysisLogModel.id == log_id)
    )
    result = await db.execute(stmt)
    row = result.one_or_none()

    if not row:
        raise HTTPException(status_code=404, detail="Log-Eintrag nicht gefunden")

    log, w_date, w_type = row
    session_date = w_date.date().isoformat() if isinstance(w_date, datetime) else str(w_date)

    return AILogDetail(
        id=log.id,
        workout_id=log.workout_id,
        created_at=log.created_at,
        provider=log.provider,
        parsed_ok=log.parsed_ok,
        duration_ms=log.duration_ms,
        session_date=session_date,
        session_type=str(w_type),
        system_prompt=log.system_prompt,
        user_prompt=log.user_prompt,
        raw_response=log.raw_response,
    )
