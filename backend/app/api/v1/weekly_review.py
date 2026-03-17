"""Wöchentliches KI-Trainingsreview API (E06-S06)."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.models.weekly_review import WeeklyReviewGenerateRequest, WeeklyReviewResponse
from app.services.weekly_review_service import generate_weekly_review, get_weekly_review

router = APIRouter()


@router.post("/weekly-review/generate", response_model=WeeklyReviewResponse)
async def generate_review(
    request: WeeklyReviewGenerateRequest,
    db: AsyncSession = Depends(get_db),
) -> WeeklyReviewResponse:
    """Generiert ein wöchentliches KI-Trainingsreview.

    **Parameters:**
    - week_start: ISO-Datum des Montags der Woche (z.B. "2026-03-10")
    - force_refresh: true um ein bestehendes Review zu überschreiben
    """
    try:
        week_start_date = date.fromisoformat(request.week_start)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Ungültiges Datum: {request.week_start}",
        ) from e

    try:
        return await generate_weekly_review(
            week_start_date, db, force_refresh=request.force_refresh
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Review konnte nicht generiert werden: {e}",
        ) from e


@router.get("/weekly-review/{week_start}", response_model=WeeklyReviewResponse)
async def get_review(
    week_start: str,
    db: AsyncSession = Depends(get_db),
) -> WeeklyReviewResponse:
    """Lädt ein gespeichertes Wochen-Review.

    **Parameters:**
    - week_start: ISO-Datum des Montags der Woche (z.B. "2026-03-10")
    """
    try:
        week_start_date = date.fromisoformat(week_start)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Ungültiges Datum: {week_start}",
        ) from e

    try:
        review = await get_weekly_review(week_start_date, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not review:
        raise HTTPException(
            status_code=404,
            detail=f"Kein Review für Woche {week_start} gefunden",
        )
    return review
