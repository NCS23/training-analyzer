"""Tests for chat_service.stream_sse_events error propagation (#770).

Stellt sicher, dass kontrollierte Provider-Fehler (z.B. max_tool_rounds
erreicht) als 'error'-Event an den Client durchgereicht werden — statt
einen stillen Abbruch zu erzeugen.
"""

import json
from collections.abc import AsyncIterator
from unittest.mock import patch

import pytest


def _events_from_payload(payload: str) -> list[dict]:
    """Parst die SSE-Lines aus einem yield-Payload zu dict-Events."""
    events: list[dict] = []
    for line in payload.split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


@pytest.mark.anyio
async def test_stream_sse_propagates_provider_error_event_and_skips_done() -> None:
    """Wenn der Provider ein error-Event yieldet, wird es weitergereicht
    und KEIN done-Event gesendet (weil die Antwort nicht abgeschlossen ist)."""
    from app.services import chat_service

    async def fake_stream() -> AsyncIterator[dict]:
        yield {"type": "token", "content": "Hallo"}
        yield {
            "type": "error",
            "message": "Die KI hat das Tool-Limit (12 Runden) erreicht.",
        }

    class FakeCtx:
        conversation_id = 999

    async def fake_prepare(*_args: object, **_kwargs: object) -> tuple:
        return fake_stream(), FakeCtx()

    finalize_called = False

    async def fake_finalize(*_args: object, **_kwargs: object) -> None:
        nonlocal finalize_called
        finalize_called = True

    with (
        patch.object(chat_service, "prepare_stream_with_tools", fake_prepare),
        patch.object(chat_service, "finalize_stream", fake_finalize),
    ):
        chunks: list[str] = []
        async for chunk in chat_service.stream_sse_events("hi", None, db=None):  # type: ignore[arg-type]
            chunks.append(chunk)

    events = _events_from_payload("".join(chunks))
    types = [e["type"] for e in events]

    # Reihenfolge: start, token, error — KEIN done
    assert types == ["start", "token", "error"]
    error_event = events[-1]
    assert "Tool-Limit" in error_event["message"]
    # Persistierung darf NICHT stattfinden, wenn abgebrochen wurde
    assert finalize_called is False


@pytest.mark.anyio
async def test_stream_sse_normal_flow_still_finalizes_and_sends_done() -> None:
    """Regression: Bei normalem Stream-Ende (ohne error) bleiben finalize
    und done-Event erhalten."""
    from app.services import chat_service

    async def fake_stream() -> AsyncIterator[dict]:
        yield {"type": "token", "content": "Antwort fertig"}

    class FakeCtx:
        conversation_id = 42

    async def fake_prepare(*_args: object, **_kwargs: object) -> tuple:
        return fake_stream(), FakeCtx()

    finalize_called = False

    async def fake_finalize(*_args: object, **_kwargs: object) -> None:
        nonlocal finalize_called
        finalize_called = True

    with (
        patch.object(chat_service, "prepare_stream_with_tools", fake_prepare),
        patch.object(chat_service, "finalize_stream", fake_finalize),
    ):
        chunks: list[str] = []
        async for chunk in chat_service.stream_sse_events("hi", None, db=None):  # type: ignore[arg-type]
            chunks.append(chunk)

    events = _events_from_payload("".join(chunks))
    types = [e["type"] for e in events]
    assert types == ["start", "token", "done"]
    assert finalize_called is True
