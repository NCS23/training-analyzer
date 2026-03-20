"""Pydantic Schemas fuer Chat API."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

# --- Request Schemas ---


class ChatMessageRequest(BaseModel):
    """Request fuer neue Chat-Nachricht."""

    message: str = Field(min_length=1, max_length=5000)
    conversation_id: int | None = None  # None = neue Konversation


# --- Response Schemas ---


class ChatMessageResponse(BaseModel):
    """Antwort nach gesendeter Nachricht."""

    conversation_id: int
    message_id: int
    content: str
    provider: str
    duration_ms: int | None = None


class ChatMessageDetail(BaseModel):
    """Einzelne Nachricht in einer Konversation."""

    id: int
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime


class ConversationSummary(BaseModel):
    """Kurzformat fuer Konversations-Liste."""

    id: int
    title: str
    message_count: int
    created_at: datetime
    updated_at: datetime


class ConversationDetail(BaseModel):
    """Vollstaendige Konversation mit Nachrichten."""

    id: int
    title: str
    messages: list[ChatMessageDetail]
    created_at: datetime


class ConversationListResponse(BaseModel):
    """Liste aller Konversationen."""

    conversations: list[ConversationSummary]
    total: int
