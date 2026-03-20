"""
AI Service Factory and Manager

Handles AI provider initialization, selection, and fallback logic.
"""

from collections.abc import AsyncIterator
from typing import Any, Optional

from app.core.config import settings
from app.domain.interfaces.ai_service import AIProvider
from app.infrastructure.ai.providers.claude_provider import ClaudeProvider
from app.infrastructure.ai.providers.ollama_provider import OllamaProvider


class AIProviderFactory:
    """Factory for creating AI providers"""

    _providers = {
        "claude": ClaudeProvider,
        "ollama": OllamaProvider,
    }

    @classmethod
    def create(cls, provider_name: str) -> AIProvider:
        """Create AI provider instance"""
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unknown AI provider: {provider_name}")

        return provider_class()

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider names"""
        return list(cls._providers.keys())


class AIService:
    """
    Main AI Service with provider management and fallback support

    Example:
        ai_service = AIService()
        analysis = await ai_service.analyze_workout(workout_data)
    """

    def __init__(self):
        self.primary_provider: Optional[AIProvider] = None
        self.fallback_providers: list[AIProvider] = []
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize AI providers based on config"""
        # Primary provider
        try:
            self.primary_provider = AIProviderFactory.create(settings.ai_primary_provider)
            print(f"✅ Primary AI provider: {self.primary_provider.name}")
        except Exception as e:
            print(f"⚠️  Failed to initialize primary provider: {e}")

        # Fallback providers
        for fallback_name in settings.ai_fallback_providers:
            try:
                provider = AIProviderFactory.create(fallback_name)
                if provider.is_available():
                    self.fallback_providers.append(provider)
                    print(f"✅ Fallback provider: {provider.name}")
            except Exception as e:
                print(f"⚠️  Failed to initialize fallback {fallback_name}: {e}")

    async def analyze_workout(self, workout_data: dict, api_key: str | None = None) -> str:
        """Analyze workout with automatic fallback.

        Args:
            workout_data: Dictionary with workout metrics
            api_key: Optionaler User-API-Key (überschreibt .env)

        Returns:
            AI analysis text

        Raises:
            Exception: If all providers fail
        """
        # Try primary provider
        if self.primary_provider and self.primary_provider.is_available(api_key):
            try:
                result = await self.primary_provider.analyze_workout(workout_data, api_key)
                return f"[{self.primary_provider.name}] {result}"
            except Exception as e:
                print(f"Primary provider failed: {e}")

        # Try fallback providers
        for provider in self.fallback_providers:
            if provider.is_available():
                try:
                    result = await provider.analyze_workout(workout_data)
                    return f"[{provider.name}] {result}"
                except Exception as e:
                    print(f"Fallback provider {provider.name} failed: {e}")
                    continue

        raise Exception("All AI providers failed")

    async def chat(self, message: str, context: dict, api_key: str | None = None) -> str:
        """Chat with AI with automatic fallback.

        Args:
            message: User message
            context: Conversation context
            api_key: Optionaler User-API-Key (überschreibt .env)

        Returns:
            AI response text
        """
        # Try primary provider
        if self.primary_provider and self.primary_provider.is_available(api_key):
            try:
                return await self.primary_provider.chat(message, context, api_key)
            except Exception as e:
                print(f"Primary provider failed: {e}")

        # Try fallback providers
        for provider in self.fallback_providers:
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
    ) -> tuple[str, str]:
        """Multi-Turn Chat mit Konversationshistorie.

        Returns:
            Tuple von (response_text, provider_name).
        """
        if self.primary_provider and self.primary_provider.is_available(api_key):
            try:
                result = await self.primary_provider.chat_multi_turn(
                    messages, system_prompt, api_key
                )
                return result, self.primary_provider.name
            except Exception as e:
                print(f"Primary provider failed: {e}")

        for provider in self.fallback_providers:
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
    ) -> tuple[AsyncIterator[str], str]:
        """Streamt Multi-Turn Chat Token fuer Token.

        Returns:
            Tuple von (async_iterator, provider_name).
        """
        if self.primary_provider and self.primary_provider.is_available(api_key):
            return (
                self.primary_provider.stream_chat_multi_turn(messages, system_prompt, api_key),
                self.primary_provider.name,
            )

        for provider in self.fallback_providers:
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
    ) -> tuple[AsyncIterator[dict], str]:
        """Streamt Chat mit Tool Use. Nur Claude unterstuetzt Tools.

        Returns:
            Tuple von (async_iterator mit dicts, provider_name).
        """
        if self.primary_provider and isinstance(self.primary_provider, ClaudeProvider):
            return (
                self.primary_provider.stream_chat_with_tools(
                    messages, system_prompt, tools, tool_handler, api_key
                ),
                self.primary_provider.name,
            )

        # Fallback: Ohne Tools streamen (Ollama etc.)
        if self.primary_provider and self.primary_provider.is_available(api_key):

            async def _wrap_stream() -> AsyncIterator[dict]:
                async for text in self.primary_provider.stream_chat_multi_turn(  # type: ignore[union-attr]
                    messages, system_prompt, api_key
                ):
                    yield {"type": "token", "content": text}

            return _wrap_stream(), self.primary_provider.name

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
        status = {}

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
