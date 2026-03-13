"""
AI API Endpoints

Manage AI providers and chat functionality.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key_resolver import resolve_claude_api_key
from app.infrastructure.ai.ai_service import AIProviderFactory, ai_service
from app.infrastructure.database.session import get_db

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
