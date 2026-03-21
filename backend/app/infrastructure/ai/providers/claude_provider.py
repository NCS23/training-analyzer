"""
Claude (Anthropic) AI Provider

High-quality AI analysis using Claude Sonnet 4.
Unterstuetzt Tool Use fuer den KI-Chat (#407).
"""

import json
import logging
from collections.abc import AsyncIterator
from typing import Any

import anthropic

from app.core.config import settings
from app.domain.interfaces.ai_service import AIProvider

logger = logging.getLogger(__name__)


class ClaudeProvider(AIProvider):
    """Anthropic Claude AI Provider"""

    def __init__(self) -> None:
        self.default_api_key = settings.claude_api_key
        self.client = anthropic.Anthropic(api_key=self.default_api_key)
        self.async_client = anthropic.AsyncAnthropic(api_key=self.default_api_key)
        self.model = settings.claude_model

    def _get_client(self, api_key: str | None = None) -> anthropic.Anthropic:
        """Client zurückgeben, optional mit anderem API Key."""
        if api_key and api_key != self.default_api_key:
            return anthropic.Anthropic(api_key=api_key)
        return self.client

    def _get_async_client(self, api_key: str | None = None) -> anthropic.AsyncAnthropic:
        """Async Client zurückgeben, optional mit anderem API Key."""
        if api_key and api_key != self.default_api_key:
            return anthropic.AsyncAnthropic(api_key=api_key)
        return self.async_client

    async def analyze_workout(self, workout_data: dict, api_key: str | None = None) -> str:
        """Analyze workout using Claude"""
        client = self._get_client(api_key)
        prompt = self._build_workout_analysis_prompt(workout_data)

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            return response.content[0].text  # type: ignore[union-attr]
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}") from e

    async def chat(self, message: str, context: dict, api_key: str | None = None) -> str:
        """Chat with Claude"""
        client = self._get_client(api_key)
        system_prompt = context.get("system_prompt") or self._build_system_prompt(context)

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": message}],
            )

            return response.content[0].text  # type: ignore[union-attr]
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}") from e

    async def chat_multi_turn(
        self,
        messages: list[dict],
        system_prompt: str,
        api_key: str | None = None,
    ) -> str:
        """Multi-Turn Chat mit Konversationshistorie."""
        client = self._get_client(api_key)
        # Cast fuer Anthropic SDK Typen
        api_messages: list[anthropic.types.MessageParam] = [
            {"role": m["role"], "content": m["content"]}
            for m in messages  # type: ignore[misc]
        ]

        try:
            response = client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                system=system_prompt,
                messages=api_messages,
            )
            return response.content[0].text  # type: ignore[union-attr]
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}") from e

    async def stream_chat_multi_turn(
        self,
        messages: list[dict],
        system_prompt: str,
        api_key: str | None = None,
    ) -> AsyncIterator[str]:
        """Streamt die KI-Antwort Token fuer Token."""
        client = self._get_async_client(api_key)
        api_messages: list[anthropic.types.MessageParam] = [
            {"role": m["role"], "content": m["content"]}
            for m in messages  # type: ignore[misc]
        ]

        async with client.messages.stream(
            model=self.model,
            max_tokens=2000,
            temperature=0.3,
            system=system_prompt,
            messages=api_messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def stream_chat_with_tools(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: list[dict],
        tool_handler: Any,
        api_key: str | None = None,
    ) -> AsyncIterator[dict]:
        """Streamt Chat mit Tool Use. Yields dicts mit type: tool_call | token."""
        client = self._get_async_client(api_key)
        api_messages: list[anthropic.types.MessageParam] = [
            {"role": m["role"], "content": m["content"]}
            for m in messages  # type: ignore[misc]
        ]

        max_tool_rounds = 5
        for round_idx in range(max_tool_rounds):
            # Signal: Neuer API-Call startet (nach Tool-Verarbeitung)
            if round_idx > 0:
                yield {"type": "thinking"}
            async with client.messages.stream(
                model=self.model,
                max_tokens=8000,
                temperature=0.3,
                system=system_prompt,
                messages=api_messages,
                tools=tools,  # type: ignore[arg-type]
            ) as stream:
                # Text-Tokens streamen
                async for text in stream.text_stream:
                    yield {"type": "token", "content": text}

                final = await stream.get_final_message()

            # Pruefen ob Tool-Calls vorhanden
            if final.stop_reason != "tool_use":
                return  # Fertig, kein Tool-Call

            # Tool-Calls verarbeiten
            api_messages.append({"role": "assistant", "content": final.content})  # type: ignore[arg-type]

            tool_results: list[dict] = []
            for block in final.content:
                if block.type == "tool_use":
                    yield {"type": "tool_call", "name": block.name, "input": block.input}
                    logger.info("Tool-Call: %s(%s)", block.name, json.dumps(block.input)[:200])
                    result = await tool_handler(block.name, block.input)
                    # Signal: Tool-Ergebnis wird verarbeitet
                    yield {"type": "thinking"}
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result, ensure_ascii=False),
                        }
                    )

            api_messages.append({"role": "user", "content": tool_results})  # type: ignore[arg-type,typeddict-item]

    def is_available(self, api_key: str | None = None) -> bool:
        """Check if Claude API is available"""
        key = api_key or self.default_api_key
        if not key:
            return False

        try:
            client = self._get_client(api_key)
            client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}],
            )
            return True
        except Exception:
            return False

    @property
    def name(self) -> str:
        return f"Claude ({self.model})"

    def _build_workout_analysis_prompt(self, workout_data: dict) -> str:
        """Build prompt for workout analysis"""
        return f"""Analysiere dieses Lauftraining für die Halbmarathon-Vorbereitung:

Typ: {workout_data.get("workout_type", "unknown")}
Dauer: {workout_data.get("duration_sec", 0) // 60} Minuten
Distanz: {workout_data.get("distance_km", 0):.2f} km
Pace: {workout_data.get("pace", "N/A")}
Herzfrequenz Ø: {workout_data.get("hr_avg", "N/A")} bpm
Herzfrequenz Max: {workout_data.get("hr_max", "N/A")} bpm

Ziel: Sub-2h Halbmarathon (5:41 min/km Pace)

Bewerte das Training kurz und prägnant:
1. Passt die Intensität zum Trainingstyp?
2. Gibt es Warnhinweise (z.B. HF zu hoch)?
3. Kurze Empfehlung für nächstes Training

Antworte in 3-4 Sätzen, sachlich und direkt."""

    def _build_system_prompt(self, _context: dict) -> str:
        """Build system prompt for chat"""
        return """Du bist ein erfahrener Lauftrainer für Halbmarathon-Vorbereitung.

Dein Athlet:
- Ziel: Sub-2h Halbmarathon (5:41 min/km)
- Bisherige Bestzeit: 1:55:20
- Aktuell: Wiedereinstieg nach Winterpause

Deine Aufgabe:
- Analysiere Trainingseinheiten wissenschaftlich fundiert
- Gib konkrete, umsetzbare Empfehlungen
- Achte auf Übertraining-Signale
- Priorisiere Gesundheit vor Performance

Antworte prägnant, freundlich und kompetent."""
