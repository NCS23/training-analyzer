"""
Claude (Anthropic) AI Provider

High-quality AI analysis using Claude Sonnet 4.
"""
from typing import Optional
import anthropic

from app.domain.interfaces.ai_service import AIProvider
from app.core.config import settings


class ClaudeProvider(AIProvider):
    """Anthropic Claude AI Provider"""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.claude_api_key)
        self.model = settings.claude_model
    
    async def analyze_workout(self, workout_data: dict) -> str:
        """Analyze workout using Claude"""
        prompt = self._build_workout_analysis_prompt(workout_data)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")
    
    async def chat(self, message: str, context: dict) -> str:
        """Chat with Claude"""
        system_prompt = self._build_system_prompt(context)
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": message}]
            )
            
            return response.content[0].text
        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if Claude API is available"""
        if not settings.claude_api_key:
            return False
        
        try:
            # Quick test
            self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
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

Typ: {workout_data.get('workout_type', 'unknown')}
Dauer: {workout_data.get('duration_sec', 0) // 60} Minuten
Distanz: {workout_data.get('distance_km', 0):.2f} km
Pace: {workout_data.get('pace', 'N/A')}
Herzfrequenz Ø: {workout_data.get('hr_avg', 'N/A')} bpm
Herzfrequenz Max: {workout_data.get('hr_max', 'N/A')} bpm

Ziel: Sub-2h Halbmarathon (5:41 min/km Pace)

Bewerte das Training kurz und prägnant:
1. Passt die Intensität zum Trainingstyp?
2. Gibt es Warnhinweise (z.B. HF zu hoch)?
3. Kurze Empfehlung für nächstes Training

Antworte in 3-4 Sätzen, sachlich und direkt."""
    
    def _build_system_prompt(self, context: dict) -> str:
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
