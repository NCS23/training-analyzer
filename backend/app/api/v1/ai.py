"""
AI API Endpoints

Manage AI providers, chat functionality, and KI-Chat-Assistent.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key_resolver import resolve_claude_api_key
from app.infrastructure.ai.ai_service import AIProviderFactory, ai_service
from app.infrastructure.database.session import get_db
from app.models.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ConversationDetail,
    ConversationListResponse,
)
from app.services import chat_service

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    context: dict = {}


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
