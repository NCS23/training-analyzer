from abc import ABC, abstractmethod
from collections.abc import AsyncIterator


class AIProvider(ABC):
    @abstractmethod
    async def analyze_workout(self, workout_data: dict, api_key: str | None = None) -> str:
        pass

    @abstractmethod
    async def chat(self, message: str, context: dict, api_key: str | None = None) -> str:
        pass

    @abstractmethod
    async def chat_multi_turn(
        self,
        messages: list[dict],
        system_prompt: str,
        api_key: str | None = None,
    ) -> str:
        pass

    @abstractmethod
    async def stream_chat_multi_turn(
        self,
        messages: list[dict],
        system_prompt: str,
        api_key: str | None = None,
    ) -> AsyncIterator[str]:
        """Streamt die KI-Antwort Token fuer Token."""
        ...  # pragma: no cover
        # yield needed to make this an async generator in implementations
        yield ""  # type: ignore[misc]

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def is_available(self, api_key: str | None = None) -> bool:
        pass
