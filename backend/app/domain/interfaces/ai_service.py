from abc import ABC, abstractmethod


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

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def is_available(self, api_key: str | None = None) -> bool:
        pass
