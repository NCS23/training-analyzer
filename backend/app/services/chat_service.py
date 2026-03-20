"""Chat Service — KI Trainingsplan-Assistent (E06-S05).

Verwaltet Konversationen und Nachrichten. Baut den vollen
Trainingskontext als System-Prompt und sendet Multi-Turn-Anfragen
an den AI-Provider.
"""

import json
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass

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
MAX_TITLE_LENGTH = 50


def _generate_title(message: str) -> str:
    """Erzeugt einen kurzen Konversationstitel aus der ersten Nachricht."""
    title = message.replace("\n", " ").strip()
    if len(title) <= MAX_TITLE_LENGTH:
        return title
    # An Wortgrenze kuerzen
    truncated = title[:MAX_TITLE_LENGTH].rsplit(" ", 1)[0]
    return f"{truncated}..." if truncated else f"{title[:MAX_TITLE_LENGTH]}..."


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
        conversation = ChatConversationModel(title=_generate_title(message))
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


@dataclass
class StreamContext:
    """Kontext fuer die Nachbearbeitung nach dem Streaming."""

    conversation_id: int
    system_prompt: str
    user_message: str
    provider_name: str
    start_time: float


async def prepare_stream(
    message: str,
    conversation_id: int | None,
    db: AsyncSession,
) -> tuple[AsyncIterator[str], StreamContext]:
    """Bereitet Streaming vor: speichert User-Msg, gibt Stream + Kontext zurueck."""
    if conversation_id:
        conversation = await _load_conversation(conversation_id, db)
    else:
        title = message[:100].strip()
        conversation = ChatConversationModel(title=title)
        db.add(conversation)
        await db.flush()

    user_msg = ChatMessageModel(
        conversation_id=conversation.id,
        role="user",
        content=message,
    )
    db.add(user_msg)
    await db.flush()

    history = await _load_message_history(conversation.id, db)
    system_prompt = await build_chat_system_prompt(db)
    api_messages = [{"role": m.role, "content": m.content} for m in history]

    api_key = await resolve_claude_api_key(db)
    stream, provider_name = await ai_service.stream_chat_multi_turn(
        api_messages, system_prompt, api_key
    )

    ctx = StreamContext(
        conversation_id=conversation.id,
        system_prompt=system_prompt,
        user_message=message,
        provider_name=provider_name,
        start_time=time.monotonic(),
    )
    return stream, ctx


async def finalize_stream(
    full_response: str,
    ctx: StreamContext,
    db: AsyncSession,
) -> None:
    """Speichert die gestreamte Antwort und loggt den AI-Call."""
    duration_ms = int((time.monotonic() - ctx.start_time) * 1000)

    assistant_msg = ChatMessageModel(
        conversation_id=ctx.conversation_id,
        role="assistant",
        content=full_response,
        provider=ctx.provider_name,
        duration_ms=duration_ms,
    )
    db.add(assistant_msg)
    await db.commit()

    await log_ai_call(
        db,
        AICallData(
            use_case="chat",
            provider=ctx.provider_name,
            system_prompt=ctx.system_prompt[:2000],
            user_prompt=ctx.user_message,
            raw_response=full_response,
            parsed_ok=True,
            duration_ms=duration_ms,
            context_label=f"conversation:{ctx.conversation_id}",
        ),
    )


async def stream_sse_events(
    message: str,
    conversation_id: int | None,
    db: AsyncSession,
) -> AsyncIterator[str]:
    """Generiert SSE-Events fuer den Streaming-Endpoint."""
    stream, ctx = await prepare_stream(message, conversation_id, db)

    # Erstes Event: Konversations-ID
    yield f"data: {json.dumps({'type': 'start', 'conversation_id': ctx.conversation_id})}\n\n"

    full_response = ""
    try:
        async for token in stream:
            full_response += token
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
    except Exception as e:
        logger.error("Streaming-Fehler: %s", e)
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        return

    # Antwort persistieren
    await finalize_stream(full_response, ctx, db)

    yield f"data: {json.dumps({'type': 'done', 'conversation_id': ctx.conversation_id})}\n\n"


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
