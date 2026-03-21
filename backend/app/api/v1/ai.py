"""
AI API Endpoints

Manage AI providers, chat functionality, and KI-Chat-Assistent.
"""

import json
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key_resolver import resolve_claude_api_key
from app.infrastructure.ai.ai_service import AIProviderFactory, ai_service
from app.infrastructure.database.models import (
    PlanChangeLogModel,
    PlannedSessionModel,
    TrainingPlanModel,
    WeeklyPlanDayModel,
)
from app.infrastructure.database.session import get_db
from app.models.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationDetail,
    ConversationListResponse,
)
from app.services import chat_service
from app.services.chat_notifications import get_notifications

logger = logging.getLogger(__name__)

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    context: dict = {}


class ApplyPlanChangeRequest(BaseModel):
    """Request zum Anwenden einer Planänderung aus dem KI-Chat."""

    action: str = Field(..., pattern="^(swap|skip|add|move|replace|rest_day)$")
    date: str = Field(..., description="Datum der Änderung (YYYY-MM-DD)")
    week_start: Optional[str] = None
    plan_id: Optional[int] = None
    description: str = ""
    reason: str = ""
    from_value: Optional[str] = Field(None, alias="from")
    to_value: Optional[str] = Field(None, alias="to")

    model_config = {"populate_by_name": True}


@router.get("/ai/providers")
async def get_providers():
    """
    Get available AI providers and their status

    **Returns:**
    - primary: Current primary provider
    - available: List of all available provider types
    - status: Detailed status of each configured provider
    """
    return {
        "primary": ai_service.get_active_provider(),
        "available": AIProviderFactory.get_available_providers(),
        "status": ai_service.get_provider_status(),
    }


@router.post("/ai/chat")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """Chat with AI trainer (User-Key → .env Fallback)."""
    try:
        claude_key = await resolve_claude_api_key(db)
        response = await ai_service.chat(request.message, request.context, api_key=claude_key)
        return {
            "success": True,
            "message": response,
            "provider": ai_service.get_active_provider(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI chat failed: {str(e)}") from e


@router.post("/ai/providers/test/{provider_name}")
async def test_provider(provider_name: str):
    """
    Test if a specific AI provider is working

    **Parameters:**
    - provider_name: claude, ollama, or openai

    **Returns:**
    Provider test results
    """
    try:
        provider = AIProviderFactory.create(provider_name)

        is_available = provider.is_available()

        if is_available:
            # Quick test
            test_data = {
                "workout_type": "test",
                "duration_sec": 1800,
                "distance_km": 5.0,
                "pace": "6:00",
                "hr_avg": 150,
            }

            test_result = await provider.analyze_workout(test_data)

            return {
                "success": True,
                "provider": provider.name,
                "available": True,
                "response_preview": test_result[:100] + "...",
            }
        else:
            return {
                "success": False,
                "provider": provider.name,
                "available": False,
                "error": f"{provider_name} is not available",
            }

    except Exception as e:
        return {"success": False, "provider": provider_name, "available": False, "error": str(e)}


# --- KI Chat-Assistent (Konversationen) ---


@router.post("/ai/conversations/messages", response_model=ChatMessageResponse)
async def send_chat_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """Sendet eine Nachricht an den KI-Trainingsassistenten."""
    try:
        return await chat_service.send_message(
            message=request.message,
            conversation_id=request.conversation_id,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat-Fehler: {str(e)}") from e


@router.post("/ai/conversations/messages/stream")
async def stream_chat_message(
    request: ChatMessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """Streamt eine KI-Antwort als Server-Sent Events."""
    try:
        return StreamingResponse(
            chat_service.stream_sse_events(
                message=request.message,
                conversation_id=request.conversation_id,
                db=db,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming-Fehler: {str(e)}") from e


@router.get("/ai/conversations", response_model=ConversationListResponse)
async def list_conversations(db: AsyncSession = Depends(get_db)):
    """Listet alle Konversationen (neueste zuerst)."""
    return await chat_service.list_conversations(db)


@router.get("/ai/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Laedt eine Konversation mit allen Nachrichten."""
    try:
        return await chat_service.get_conversation(conversation_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete("/ai/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Loescht eine Konversation."""
    try:
        await chat_service.delete_conversation(conversation_id, db)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/ai/notifications")
async def get_ai_notifications(db: AsyncSession = Depends(get_db)):
    """Liefert proaktive KI-Benachrichtigungen basierend auf Trainingsdaten."""
    notifications = await get_notifications(db)
    return {"notifications": notifications, "count": len(notifications)}


@router.post("/ai/apply-plan-change")
async def apply_plan_change(
    request: ApplyPlanChangeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Wendet eine KI-vorgeschlagene Planänderung auf den Wochenplan an."""
    try:
        target_date = datetime.strptime(request.date, "%Y-%m-%d").date()
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Ungültiges Datum: {request.date}") from e

    week_start = target_date - timedelta(days=target_date.weekday())
    day_of_week = target_date.weekday()

    # Plan-ID ermitteln
    plan_id = request.plan_id
    if not plan_id:
        today = date.today()
        plan_result = await db.execute(
            select(TrainingPlanModel.id)
            .where(
                TrainingPlanModel.status == "active",
                TrainingPlanModel.start_date <= today,
                TrainingPlanModel.end_date >= today,
            )
            .limit(1)
        )
        plan_id = plan_result.scalar_one_or_none()

    # Tag laden oder erstellen
    day_result = await db.execute(
        select(WeeklyPlanDayModel).where(
            WeeklyPlanDayModel.week_start == week_start,
            WeeklyPlanDayModel.day_of_week == day_of_week,
        )
    )
    day = day_result.scalar_one_or_none()

    if not day:
        day = WeeklyPlanDayModel(
            plan_id=plan_id,
            week_start=week_start,
            day_of_week=day_of_week,
            is_rest_day=False,
            edited=True,
        )
        db.add(day)
        await db.flush()

    result = await _execute_plan_action(request.action, day, request, db)

    # Edited-Flag setzen
    day.edited = True

    # Changelog erstellen
    if plan_id:
        changelog = PlanChangeLogModel(
            plan_id=plan_id,
            change_type="session_modified",
            category="content",
            summary=request.description or f"KI-Chat: {request.action}",
            reason=request.reason,
            details_json=json.dumps(
                {
                    "source": "ki_chat",
                    "action": request.action,
                    "date": request.date,
                    "from": request.from_value,
                    "to": request.to_value,
                }
            ),
        )
        db.add(changelog)

    await db.commit()
    return {"success": True, **result}


async def _execute_plan_action(
    action: str,
    day: WeeklyPlanDayModel,
    request: ApplyPlanChangeRequest,
    db: AsyncSession,
) -> dict:
    """Führt die eigentliche Planänderung durch."""
    action_map = {
        "rest_day": _action_rest_day,
        "skip": _action_skip,
        "replace": _action_replace,
        "add": _action_add,
        "swap": _handle_swap,
        "move": _handle_move,
    }
    handler = action_map.get(action)
    if handler:
        return await handler(day, request, db)
    return {"message": f"Aktion '{action}' ausgeführt"}


async def _action_rest_day(
    day: WeeklyPlanDayModel,
    _request: ApplyPlanChangeRequest,
    db: AsyncSession,
) -> dict:
    """Setzt einen Tag als Ruhetag."""
    day.is_rest_day = True
    sessions_result = await db.execute(
        select(PlannedSessionModel).where(PlannedSessionModel.day_id == day.id)
    )
    for s in sessions_result.scalars().all():
        s.status = "skipped"
    return {"message": "Ruhetag eingetragen"}


async def _action_skip(
    day: WeeklyPlanDayModel,
    _request: ApplyPlanChangeRequest,
    db: AsyncSession,
) -> dict:
    """Überspringt alle aktiven Sessions eines Tages."""
    sessions_result = await db.execute(
        select(PlannedSessionModel).where(
            PlannedSessionModel.day_id == day.id,
            PlannedSessionModel.status == "active",
        )
    )
    skipped = 0
    for s in sessions_result.scalars().all():
        s.status = "skipped"
        skipped += 1
    return {"message": f"{skipped} Session(s) übersprungen"}


async def _action_replace(
    day: WeeklyPlanDayModel,
    request: ApplyPlanChangeRequest,
    db: AsyncSession,
) -> dict:
    """Ersetzt bestehende Sessions durch eine neue."""
    sessions_result = await db.execute(
        select(PlannedSessionModel).where(PlannedSessionModel.day_id == day.id)
    )
    for s in sessions_result.scalars().all():
        await db.delete(s)

    new_type, new_notes = _parse_to_value(request.to_value)
    db.add(
        PlannedSessionModel(
            day_id=day.id,
            position=0,
            training_type=new_type,
            notes=new_notes or request.description,
        )
    )
    day.is_rest_day = False
    return {"message": f"Session ersetzt: {request.to_value}"}


async def _action_add(
    day: WeeklyPlanDayModel,
    request: ApplyPlanChangeRequest,
    db: AsyncSession,
) -> dict:
    """Fügt eine neue Session zum Tag hinzu."""
    max_pos_result = await db.execute(
        select(PlannedSessionModel.position)
        .where(PlannedSessionModel.day_id == day.id)
        .order_by(PlannedSessionModel.position.desc())
        .limit(1)
    )
    max_pos = max_pos_result.scalar_one_or_none() or -1

    new_type, new_notes = _parse_to_value(request.to_value)
    db.add(
        PlannedSessionModel(
            day_id=day.id,
            position=max_pos + 1,
            training_type=new_type,
            notes=new_notes or request.description,
        )
    )
    day.is_rest_day = False
    return {"message": f"Session hinzugefügt: {request.to_value}"}


async def _handle_swap(
    day: WeeklyPlanDayModel,
    request: ApplyPlanChangeRequest,
    db: AsyncSession,
) -> dict:
    """Tauscht Sessions zwischen zwei Tagen."""
    if not request.from_value:
        return {"message": "Tausch erfordert 'from'-Datum"}

    # Zweiten Tag finden (from_value kann ein Wochentag-Name oder Datum sein)
    other_dow = _parse_weekday(request.from_value)
    if other_dow is None:
        return {"message": f"Unbekannter Wochentag: {request.from_value}"}

    other_result = await db.execute(
        select(WeeklyPlanDayModel).where(
            WeeklyPlanDayModel.week_start == day.week_start,
            WeeklyPlanDayModel.day_of_week == other_dow,
        )
    )
    other_day = other_result.scalar_one_or_none()
    if not other_day:
        return {"message": f"Kein Wochenplaneintrag für Tag {request.from_value}"}

    # Sessions laden
    day_sessions = await db.execute(
        select(PlannedSessionModel).where(PlannedSessionModel.day_id == day.id)
    )
    other_sessions = await db.execute(
        select(PlannedSessionModel).where(PlannedSessionModel.day_id == other_day.id)
    )

    # day_ids tauschen
    for s in day_sessions.scalars().all():
        s.day_id = other_day.id
    for s in other_sessions.scalars().all():
        s.day_id = day.id

    # Rest-Day Status tauschen
    day.is_rest_day, other_day.is_rest_day = other_day.is_rest_day, day.is_rest_day
    day.edited = True
    other_day.edited = True

    return {"message": "Sessions getauscht"}


async def _handle_move(
    day: WeeklyPlanDayModel,
    request: ApplyPlanChangeRequest,
    db: AsyncSession,
) -> dict:
    """Verschiebt Sessions auf einen anderen Tag."""
    if not request.to_value:
        return {"message": "Verschieben erfordert 'to'-Zielangabe"}

    target_dow = _parse_weekday(request.to_value)
    if target_dow is None:
        return {"message": f"Unbekannter Ziel-Wochentag: {request.to_value}"}

    # Ziel-Tag laden oder erstellen
    target_result = await db.execute(
        select(WeeklyPlanDayModel).where(
            WeeklyPlanDayModel.week_start == day.week_start,
            WeeklyPlanDayModel.day_of_week == target_dow,
        )
    )
    target_day = target_result.scalar_one_or_none()
    if not target_day:
        target_day = WeeklyPlanDayModel(
            plan_id=day.plan_id,
            week_start=day.week_start,
            day_of_week=target_dow,
            is_rest_day=False,
            edited=True,
        )
        db.add(target_day)
        await db.flush()

    # Sessions verschieben
    sessions_result = await db.execute(
        select(PlannedSessionModel).where(PlannedSessionModel.day_id == day.id)
    )
    for s in sessions_result.scalars().all():
        s.day_id = target_day.id

    day.is_rest_day = True
    day.edited = True
    target_day.is_rest_day = False
    target_day.edited = True

    return {"message": "Sessions verschoben"}


def _parse_weekday(text: str) -> int | None:
    """Parst einen deutschen Wochentag zu day_of_week (0=Mo)."""
    mapping = {
        "montag": 0,
        "dienstag": 1,
        "mittwoch": 2,
        "donnerstag": 3,
        "freitag": 4,
        "samstag": 5,
        "sonntag": 6,
        "mo": 0,
        "di": 1,
        "mi": 2,
        "do": 3,
        "fr": 4,
        "sa": 5,
        "so": 6,
    }
    return mapping.get(text.lower().strip())


def _parse_to_value(to_value: str | None) -> tuple[str, str | None]:
    """Extrahiert training_type und Notizen aus dem to_value."""
    if not to_value:
        return "running", None

    text = to_value.lower()
    if any(k in text for k in ["kraft", "strength", "gym"]):
        return "strength", to_value
    return "running", to_value
