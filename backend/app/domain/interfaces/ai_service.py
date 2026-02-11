from abc import ABC, abstractmethod
from typing import List, Optional

class AIProvider(ABC):
    @abstractmethod
    async def analyze_workout(self, workout_data: dict) -> str:
        pass
    
    @abstractmethod
    async def chat(self, message: str, context: dict) -> str:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
