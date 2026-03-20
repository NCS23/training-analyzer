"""Chat Service — KI Trainingsplan-Assistent (E06-S05).

Verwaltet Konversationen und Nachrichten. Baut den vollen
Trainingskontext als System-Prompt und sendet Multi-Turn-Anfragen
an den AI-Provider.
"""

import logging
import time

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.api_key_resolver import resolve_claude_api_key
from app.infrastructure.ai.ai_service import ai_service
from app.infrastructure.database.models import ChatConversationModel, ChatMessageModel
from app.models.chat import (
    ChatMessageDetail,
    ChatMessageResponse,
    ConversationDetail,
    ConversationListResponse,
    ConversationSummary,
)
from app.services.ai_log_service import AICallData, log_ai_call
from app.services.chat_context_service import build_chat_system_prompt

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 30


async def send_message(
    message: str,
    conversation_id: int | None,
    db: AsyncSession,
) -> ChatMessageResponse:
    """Sendet eine Nachricht und gibt die KI-Antwort zurueck."""
    # 1. Konversation erstellen oder laden
    if conversation_id:
        conversation = await _load_conversation(conversation_id, db)
    else:
        title = message[:100].strip()
        conversation = ChatConversationModel(title=title)
        db.add(conversation)
        await db.flush()

    # 2. User-Nachricht speichern
    user_msg = ChatMessageModel(
        conversation_id=conversation.id,
        role="user",
        content=message,
    )
    db.add(user_msg)
    await db.flush()

    # 3. Konversationshistorie laden
    history = await _load_message_history(conversation.id, db)

    # 4. System-Prompt mit Trainingskontext
    system_prompt = await build_chat_system_prompt(db)

    # 5. Messages-Array fuer Claude API
    api_messages = [{"role": m.role, "content": m.content} for m in history]

    # 6. AI-Anfrage
    api_key = await resolve_claude_api_key(db)
    start = time.monotonic()
    response_text, provider_name = await ai_service.chat_multi_turn(
        api_messages, system_prompt, api_key
    )
    duration_ms = int((time.monotonic() - start) * 1000)

    # 7. Antwort speichern
    assistant_msg = ChatMessageModel(
        conversation_id=conversation.id,
        role="assistant",
        content=response_text,
        provider=provider_name,
        duration_ms=duration_ms,
    )
    db.add(assistant_msg)
    await db.commit()

    # 8. AI-Call loggen
    await log_ai_call(
        db,
        AICallData(
            use_case="chat",
            provider=provider_name,
            system_prompt=system_prompt[:2000],
            user_prompt=message,
            raw_response=response_text,
            parsed_ok=True,
            duration_ms=duration_ms,
            context_label=f"conversation:{conversation.id}",
        ),
    )

    return ChatMessageResponse(
        conversation_id=conversation.id,
        message_id=assistant_msg.id,
        content=response_text,
        provider=provider_name,
        duration_ms=duration_ms,
    )


async def list_conversations(db: AsyncSession) -> ConversationListResponse:
    """Listet alle Konversationen (neueste zuerst)."""
    result = await db.execute(
        select(ChatConversationModel).order_by(ChatConversationModel.updated_at.desc()).limit(50)
    )
    conversations = result.scalars().all()

    summaries = []
    for conv in conversations:
        count_result = await db.execute(
            select(func.count(ChatMessageModel.id)).where(
                ChatMessageModel.conversation_id == conv.id
            )
        )
        count = count_result.scalar() or 0
        summaries.append(
            ConversationSummary(
                id=conv.id,
                title=conv.title,
                message_count=count,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
        )

    return ConversationListResponse(conversations=summaries, total=len(summaries))


async def get_conversation(conversation_id: int, db: AsyncSession) -> ConversationDetail:
    """Laedt eine Konversation mit allen Nachrichten."""
    conversation = await _load_conversation(conversation_id, db)

    result = await db.execute(
        select(ChatMessageModel)
        .where(ChatMessageModel.conversation_id == conversation_id)
        .order_by(ChatMessageModel.created_at)
    )
    messages = [
        ChatMessageDetail(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at,
        )
        for m in result.scalars().all()
    ]

    return ConversationDetail(
        id=conversation.id,
        title=conversation.title,
        messages=messages,
        created_at=conversation.created_at,
    )


async def delete_conversation(conversation_id: int, db: AsyncSession) -> None:
    """Loescht eine Konversation (Messages via CASCADE)."""
    conversation = await _load_conversation(conversation_id, db)
    await db.delete(conversation)
    await db.commit()


async def _load_conversation(conversation_id: int, db: AsyncSession) -> ChatConversationModel:
    """Laedt Konversation oder wirft ValueError."""
    result = await db.execute(
        select(ChatConversationModel).where(ChatConversationModel.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise ValueError(f"Konversation {conversation_id} nicht gefunden")
    return conversation


async def _load_message_history(conversation_id: int, db: AsyncSession) -> list[ChatMessageModel]:
    """Laedt die letzten N Nachrichten einer Konversation."""
    result = await db.execute(
        select(ChatMessageModel)
        .where(ChatMessageModel.conversation_id == conversation_id)
        .order_by(ChatMessageModel.created_at.desc())
        .limit(MAX_HISTORY_MESSAGES)
    )
    messages = list(result.scalars().all())
    messages.reverse()  # Chronologisch sortieren
    return messages
