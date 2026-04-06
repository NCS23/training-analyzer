"""
OpenAI AI Provider

High-quality AI analysis using OpenAI's GPT models.
"""

import logging
from collections.abc import AsyncIterator

from openai import AsyncOpenAI, OpenAI

from app.core.config import settings
from app.domain.interfaces.ai_service import AIProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI (ChatGPT) AI Provider"""

    def __init__(self) -> None:
        self.default_api_key = settings.openai_api_key
        self.model = settings.openai_model

    def _get_client(self, api_key: str | None = None) -> OpenAI:
        """Client zurückgeben, optional mit anderem API Key."""
        key = api_key or self.default_api_key
        return OpenAI(api_key=key) if key else OpenAI(api_key="none")

    def _get_async_client(self, api_key: str | None = None) -> AsyncOpenAI:
        """Async Client zurückgeben, optional mit anderem API Key."""
        key = api_key or self.default_api_key
        return AsyncOpenAI(api_key=key) if key else AsyncOpenAI(api_key="none")

    async def analyze_workout(self, workout_data: dict, api_key: str | None = None) -> str:
        """Analyze workout using OpenAI"""
        prompt = self._build_workout_analysis_prompt(workout_data)
        client = self._get_async_client(api_key)

        try:
            response = await client.chat.completions.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}") from e

    async def chat(self, message: str, context: dict, api_key: str | None = None) -> str:
        """Chat with OpenAI"""
        system_prompt = context.get("system_prompt") or self._build_system_prompt(context)
        client = self._get_async_client(api_key)

        try:
            response = await client.chat.completions.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}") from e

    async def chat_multi_turn(
        self,
        messages: list[dict],
        system_prompt: str,
        api_key: str | None = None,
    ) -> str:
        """Multi-Turn Chat mit Konversationshistorie."""
        client = self._get_async_client(api_key)
        api_messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            *[{"role": m["role"], "content": m["content"]} for m in messages],
        ]

        try:
            response = await client.chat.completions.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                messages=api_messages,  # type: ignore[arg-type]
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}") from e

    async def stream_chat_multi_turn(
        self,
        messages: list[dict],
        system_prompt: str,
        api_key: str | None = None,
    ) -> AsyncIterator[str]:
        """Streamt die KI-Antwort Token fuer Token."""
        client = self._get_async_client(api_key)
        api_messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            *[{"role": m["role"], "content": m["content"]} for m in messages],
        ]

        stream = await client.chat.completions.create(
            model=self.model,
            max_tokens=2000,
            temperature=0.3,
            messages=api_messages,  # type: ignore[arg-type]
            stream=True,
        )
        async for chunk in stream:  # type: ignore[union-attr]
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def is_available(self, api_key: str | None = None) -> bool:
        """Prüft ob ein API Key vorhanden ist (kein teurer Test-Call)."""
        key = api_key or self.default_api_key
        return bool(key)

    @property
    def name(self) -> str:
        return f"OpenAI ({self.model})"

    def _build_workout_analysis_prompt(self, workout_data: dict) -> str:
        """Build prompt for workout analysis"""
        return f"""Analysiere dieses Lauftraining für die Halbmarathon-Vorbereitung:

Typ: {workout_data.get("workout_type", "unknown")}
Dauer: {workout_data.get("duration_sec", 0) // 60} Minuten
Distanz: {workout_data.get("distance_km", 0):.2f} km
Pace: {workout_data.get("pace", "N/A")}
Herzfrequenz Ø: {workout_data.get("hr_avg", "N/A")} bpm
Herzfrequenz Max: {workout_data.get("hr_max", "N/A")} bpm

Bewerte das Training kurz und prägnant in 3-4 Sätzen."""

    def _build_system_prompt(self, _context: dict) -> str:
        """Build system prompt for chat"""
        return """Du bist ein erfahrener Lauftrainer für Halbmarathon-Vorbereitung.
Analysiere Trainingseinheiten wissenschaftlich fundiert, gib konkrete Empfehlungen,
achte auf Übertraining-Signale und priorisiere Gesundheit vor Performance.
Antworte prägnant, freundlich und kompetent."""
