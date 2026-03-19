from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Environment
    environment: Literal["development", "production", "testing"] = "development"
    debug: bool = False

    # Database
    database_url: str = "sqlite:///./training_analyzer.db"

    # AI Providers
    ai_primary_provider: Literal["claude", "ollama", "openai"] = "claude"
    ai_fallback_providers: list[str] = ["ollama"]

    # Claude (env var: ANTHROPIC_API_KEY)
    claude_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    claude_model: str = "claude-sonnet-4-20250514"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # OpenAI (env var: OPENAI_API_KEY)
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = "gpt-4-turbo"

    # Docling
    docling_server_url: str = Field(default="http://192.168.68.66:5001", alias="DOCLING_BASE_URL")

    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"

    # External APIs (Enrichment)
    enrichment_enabled: bool = True
    open_meteo_timeout: float = 10.0
    nominatim_user_agent: str = "training-analyzer/1.0"
    nominatim_rate_limit_ms: int = 1100

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment == "testing"


settings = Settings()
