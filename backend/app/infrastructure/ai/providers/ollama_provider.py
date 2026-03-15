"""
Ollama AI Provider

Self-hosted LLM provider for cost-free, privacy-focused AI analysis.
"""

import httpx

from app.core.config import settings
from app.domain.interfaces.ai_service import AIProvider


class OllamaProvider(AIProvider):
    """Ollama (Self-hosted LLM) Provider"""

    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model
        self.timeout = 120.0

    async def analyze_workout(self, workout_data: dict, _api_key: str | None = None) -> str:
        """Analyze workout using Ollama"""
        prompt = self._build_workout_analysis_prompt(workout_data)

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 500,
                        },
                    },
                )
                response.raise_for_status()
                result = response.json()
                return result["response"]
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}") from e

    async def chat(self, message: str, context: dict, _api_key: str | None = None) -> str:
        """Chat with Ollama"""
        system_prompt = context.get("system_prompt") or self._build_system_prompt(context)
        full_prompt = f"{system_prompt}\n\nUser: {message}\n\nAssistant:"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.5,
                            "num_predict": 1000,
                        },
                    },
                )
                response.raise_for_status()
                result = response.json()
                return result["response"]
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}") from e

    def is_available(self, _api_key: str | None = None) -> bool:
        """Check if Ollama server is available"""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    @property
    def name(self) -> str:
        return f"Ollama ({self.model})"

    def _build_workout_analysis_prompt(self, workout_data: dict) -> str:
        """Build prompt for workout analysis"""
        return f"""Du bist ein erfahrener Lauftrainer. Analysiere dieses Training:

Typ: {workout_data.get("workout_type", "unknown")}
Dauer: {workout_data.get("duration_sec", 0) // 60} Minuten
Distanz: {workout_data.get("distance_km", 0):.2f} km
Pace: {workout_data.get("pace", "N/A")}
Herzfrequenz Ø: {workout_data.get("hr_avg", "N/A")} bpm
Herzfrequenz Max: {workout_data.get("hr_max", "N/A")} bpm

Ziel: Sub-2h Halbmarathon (5:41 min/km Ziel-Pace)

Bewertung (3-4 Sätze):
1. Passt die Intensität?
2. Warnhinweise?
3. Empfehlung

Antworte kurz und präzise:"""

    def _build_system_prompt(self, _context: dict) -> str:
        """Build system prompt for chat"""
        return """Du bist ein Lauftrainer für Halbmarathon-Vorbereitung.

Athlet: Sub-2h Ziel (5:41 min/km), Bestzeit 1:55:20, aktuell Wiedereinstieg.

Antworte kompetent, prägnant und freundlich."""
