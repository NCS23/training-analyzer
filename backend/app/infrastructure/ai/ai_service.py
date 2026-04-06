"""
AI Service Factory and Manager

Handles AI provider initialization, selection, and fallback logic.
Providers können pro Request gewählt werden (User-Präferenz).
"""

from collections.abc import AsyncIterator
from typing import Any, Optional

from app.core.config import settings
from app.domain.interfaces.ai_service import AIProvider
from app.infrastructure.ai.providers.claude_provider import ClaudeProvider
from app.infrastructure.ai.providers.ollama_provider import OllamaProvider
from app.infrastructure.ai.providers.openai_provider import OpenAIProvider


class AIProviderFactory:
    """Factory for creating AI providers"""

    _providers = {
        "claude": ClaudeProvider,
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
    }

    @classmethod
    def create(cls, provider_name: str) -> AIProvider:
        """Create AI provider instance"""
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown AI provider: {provider_name}")
        return provider_class()  # type: ignore[abstract]

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider names"""
        return list(cls._providers.keys())


class AIService:
    """Main AI Service mit Provider-Cache und dynamischer Auswahl pro Request."""

    def __init__(self) -> None:
        self._provider_cache: dict[str, AIProvider] = {}
        self.primary_provider: Optional[AIProvider] = None
        self.fallback_providers: list[AIProvider] = []
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialisiert Default-Provider aus Config (für Fallback-Chain)."""
        try:
            self.primary_provider = self._get_or_create(settings.ai_primary_provider)
            print(f"✅ Primary AI provider: {self.primary_provider.name}")
        except Exception as e:
            print(f"⚠️  Failed to initialize primary provider: {e}")

        for fallback_name in settings.ai_fallback_providers:
            try:
                provider = self._get_or_create(fallback_name)
                if provider.is_available():
                    self.fallback_providers.append(provider)
                    print(f"✅ Fallback provider: {provider.name}")
            except Exception as e:
                print(f"⚠️  Failed to initialize fallback {fallback_name}: {e}")

    def _get_or_create(self, provider_name: str) -> AIProvider:
        """Provider aus Cache holen oder neu erstellen."""
        name = provider_name.lower()
        if name not in self._provider_cache:
            self._provider_cache[name] = AIProviderFactory.create(name)
        return self._provider_cache[name]

    def _select_provider(self, provider_name: str | None) -> AIProvider | None:
        """Wählt Provider basierend auf Name oder nimmt Primary."""
        if provider_name:
            try:
                return self._get_or_create(provider_name)
            except ValueError:
                pass
        return self.primary_provider

    async def analyze_workout(
        self,
        workout_data: dict,
        api_key: str | None = None,
        provider_name: str | None = None,
    ) -> str:
        """Analyze workout mit gewähltem Provider + Fallback."""
        primary = self._select_provider(provider_name)
        if primary and primary.is_available(api_key):
            try:
                result = await primary.analyze_workout(workout_data, api_key)
                return f"[{primary.name}] {result}"
            except Exception as e:
                print(f"Primary provider failed: {e}")

        for provider in self.fallback_providers:
            if provider is primary:
                continue
            if provider.is_available():
                try:
                    result = await provider.analyze_workout(workout_data)
                    return f"[{provider.name}] {result}"
                except Exception as e:
                    print(f"Fallback provider {provider.name} failed: {e}")
                    continue

        raise Exception("All AI providers failed")

    async def chat(
        self,
        message: str,
        context: dict,
        api_key: str | None = None,
        provider_name: str | None = None,
    ) -> str:
        """Chat mit gewähltem Provider + Fallback."""
        primary = self._select_provider(provider_name)
        if primary and primary.is_available(api_key):
            try:
                return await primary.chat(message, context, api_key)
            except Exception as e:
                print(f"Primary provider failed: {e}")

        for provider in self.fallback_providers:
            if provider is primary:
                continue
            if provider.is_available():
                try:
                    return await provider.chat(message, context)
                except Exception as e:
                    print(f"Fallback provider {provider.name} failed: {e}")
                    continue

        raise Exception("All AI providers failed")

    async def chat_multi_turn(
        self,
        messages: list[dict],
        system_prompt: str,
        api_key: str | None = None,
        provider_name: str | None = None,
    ) -> tuple[str, str]:
        """Multi-Turn Chat mit gewähltem Provider."""
        primary = self._select_provider(provider_name)
        if primary and primary.is_available(api_key):
            try:
                result = await primary.chat_multi_turn(messages, system_prompt, api_key)
                return result, primary.name
            except Exception as e:
                print(f"Primary provider failed: {e}")

        for provider in self.fallback_providers:
            if provider is primary:
                continue
            if provider.is_available():
                try:
                    result = await provider.chat_multi_turn(messages, system_prompt)
                    return result, provider.name
                except Exception as e:
                    print(f"Fallback provider {provider.name} failed: {e}")
                    continue

        raise Exception("All AI providers failed")

    async def stream_chat_multi_turn(
        self,
        messages: list[dict],
        system_prompt: str,
        api_key: str | None = None,
        provider_name: str | None = None,
    ) -> tuple[AsyncIterator[str], str]:
        """Streamt Multi-Turn Chat Token fuer Token."""
        primary = self._select_provider(provider_name)
        if primary and primary.is_available(api_key):
            return (
                primary.stream_chat_multi_turn(messages, system_prompt, api_key),
                primary.name,
            )

        for provider in self.fallback_providers:
            if provider is primary:
                continue
            if provider.is_available():
                return (
                    provider.stream_chat_multi_turn(messages, system_prompt),
                    provider.name,
                )

        raise Exception("All AI providers failed")

    async def stream_chat_with_tools(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: list[dict],
        tool_handler: Any,
        api_key: str | None = None,
        provider_name: str | None = None,
    ) -> tuple[AsyncIterator[dict], str]:
        """Streamt Chat mit Tool Use. Nur Claude unterstützt Tools nativ."""
        primary = self._select_provider(provider_name)
        if isinstance(primary, ClaudeProvider) and primary.is_available(api_key):
            return (
                primary.stream_chat_with_tools(
                    messages, system_prompt, tools, tool_handler, api_key
                ),
                primary.name,
            )

        # Fallback: Ohne Tools streamen (OpenAI, Ollama etc.)
        if primary and primary.is_available(api_key):

            async def _wrap_stream() -> AsyncIterator[dict]:
                async for text in primary.stream_chat_multi_turn(  # type: ignore[union-attr]
                    messages, system_prompt, api_key
                ):
                    yield {"type": "token", "content": text}

            return _wrap_stream(), primary.name

        raise Exception("No AI provider available for tool-use streaming")

    def get_active_provider(self) -> Optional[str]:
        """Get name of currently active provider"""
        if self.primary_provider and self.primary_provider.is_available():
            return self.primary_provider.name

        for provider in self.fallback_providers:
            if provider.is_available():
                return provider.name

        return None

    def get_provider_status(self) -> dict:
        """Get status of all configured providers"""
        status: dict = {}

        if self.primary_provider:
            status[self.primary_provider.name] = {
                "available": self.primary_provider.is_available(),
                "is_primary": True,
            }

        for provider in self.fallback_providers:
            status[provider.name] = {
                "available": provider.is_available(),
                "is_primary": False,
            }

        return status


# Global instance
ai_service = AIService()
