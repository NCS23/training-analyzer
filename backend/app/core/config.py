from pydantic_settings import BaseSettings
from typing import List, Literal

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./training_analyzer.db"
    
    # AI Providers
    ai_primary_provider: Literal["claude", "ollama", "openai"] = "claude"
    ai_fallback_providers: List[str] = ["ollama"]
    
    # Claude
    claude_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo"
    
    # Docling
    docling_server_url: str = "http://192.168.68.66:5001"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
