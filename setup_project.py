#!/usr/bin/env python3
"""
Training Analyzer - Project Structure Generator

This script creates the complete project structure with all necessary files.
Run this script to bootstrap the entire application.

Usage:
    python setup_project.py
"""

import os
from pathlib import Path
from typing import Dict

# Define project structure
STRUCTURE: Dict[str, str] = {
    # Backend - Core
    "backend/app/__init__.py": "",
    "backend/app/core/__init__.py": "",
    "backend/app/core/config.py": """from pydantic_settings import BaseSettings
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
""",
    
    # Backend - Domain
    "backend/app/domain/__init__.py": "",
    "backend/app/domain/entities/__init__.py": "",
    "backend/app/domain/entities/workout.py": """from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class Workout:
    id: Optional[int] = None
    date: datetime = datetime.now()
    workout_type: str = "running"  # running, strength
    subtype: Optional[str] = None  # quality, recovery, longrun, studio_tag1, studio_tag2
    
    # Running data
    duration_sec: Optional[int] = None
    distance_km: Optional[float] = None
    pace: Optional[str] = None  # "6:31"
    hr_avg: Optional[int] = None
    hr_max: Optional[int] = None
    hr_min: Optional[int] = None
    
    # Metadata
    csv_data: Optional[str] = None
    warnings: List[str] = None
    ai_analysis: Optional[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
""",
    
    # Backend - AI Interface
    "backend/app/domain/interfaces/__init__.py": "",
    "backend/app/domain/interfaces/ai_service.py": """from abc import ABC, abstractmethod
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
""",
    
    # Backend - Database
    "backend/app/infrastructure/__init__.py": "",
    "backend/app/infrastructure/database/__init__.py": "",
    "backend/app/infrastructure/database/session.py": """from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

# Convert sync URL to async if needed
database_url = settings.database_url
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
elif database_url.startswith("sqlite:///"):
    database_url = database_url.replace("sqlite:///", "sqlite+aiosqlite:///")

engine = create_async_engine(database_url, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session_maker() as session:
        yield session

async def init_db():
    # Create tables if they don't exist
    from app.infrastructure.database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
""",
    
    "backend/app/infrastructure/database/models.py": """from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class WorkoutModel(Base):
    __tablename__ = "workouts"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, nullable=False, index=True)
    workout_type = Column(String, nullable=False, index=True)
    subtype = Column(String)
    
    duration_sec = Column(Integer)
    distance_km = Column(Float)
    pace = Column(String)
    hr_avg = Column(Integer)
    hr_max = Column(Integer)
    hr_min = Column(Integer)
    
    csv_data = Column(Text)
    ai_analysis = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
""",
    
    # Backend - API
    "backend/app/api/__init__.py": "",
    "backend/app/api/v1/__init__.py": "",
    "backend/app/api/v1/router.py": """from fastapi import APIRouter
from app.api.v1 import health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
""",
    
    "backend/app/api/v1/health.py": """from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health_check():
    return {"status": "healthy"}
""",
    
    # Frontend - package.json
    "frontend/package.json": """{
  "name": "training-analyzer-frontend",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "format": "prettier --write \\"src/**/*.{ts,tsx,css}\\"",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:coverage": "vitest --coverage",
    "storybook": "storybook dev -p 6006",
    "build-storybook": "storybook build"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "zustand": "^4.5.0",
    "axios": "^1.6.7",
    "@tanstack/react-query": "^5.20.0",
    "recharts": "^2.10.0",
    "zod": "^3.22.4",
    "date-fns": "^3.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.2.55",
    "@types/react-dom": "^18.2.19",
    "@typescript-eslint/eslint-plugin": "^6.21.0",
    "@typescript-eslint/parser": "^6.21.0",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.17",
    "eslint": "^8.56.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.35",
    "prettier": "^3.2.5",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3",
    "vite": "^5.1.0",
    "vitest": "^1.2.2"
  }
}
""",
    
    # Frontend - Vite config
    "frontend/vite.config.ts": """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: true,
  },
})
""",
    
    # Frontend - Tailwind config
    "frontend/tailwind.config.js": """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#2563eb',
        workout: {
          quality: '#8b5cf6',
          recovery: '#10b981',
          longrun: '#3b82f6',
          strength: '#f97316',
        },
        hr: {
          zone1: '#10b981',
          zone2: '#f59e0b',
          zone3: '#ef4444',
        },
      },
    },
  },
  plugins: [],
}
""",
    
    # Frontend - Basic structure
    "frontend/index.html": """<!doctype html>
<html lang="de">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Training Analyzer</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""",
    
    "frontend/src/main.tsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""",
    
    "frontend/src/App.tsx": """function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-12 px-4">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          🏃‍♂️ Training Analyzer
        </h1>
        <p className="text-gray-600">
          AI-powered half-marathon training platform
        </p>
      </div>
    </div>
  )
}

export default App
""",
    
    "frontend/src/index.css": """@tailwind base;
@tailwind components;
@tailwind utilities;
""",
    
    # Docker
    "frontend/Dockerfile": """FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
""",
    
    # Git files
    ".gitignore": """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv
*.egg-info/
dist/
build/

# Node
node_modules/
dist/
.cache/
*.log

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Database
*.db
*.sqlite
*.sqlite3

# Docker
.dockerignore

# Testing
.coverage
htmlcov/
.pytest_cache/
coverage/

# Data
/backend/data/
/uploads/
""",
}


def create_structure():
    """Create all project files"""
    base_path = Path("/home/claude/training-analyzer")
    
    print("🏗️  Creating Training Analyzer project structure...")
    print()
    
    created_files = 0
    created_dirs = 0
    
    for file_path, content in STRUCTURE.items():
        full_path = base_path / file_path
        
        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if not full_path.parent.exists():
            created_dirs += 1
        
        # Write file
        if not full_path.exists():
            full_path.write_text(content)
            created_files += 1
            print(f"✅ Created: {file_path}")
        else:
            print(f"⏭️  Skipped (exists): {file_path}")
    
    print()
    print(f"📁 Created {created_dirs} directories")
    print(f"📄 Created {created_files} files")
    print()
    print("✨ Project structure ready!")
    print()
    print("Next steps:")
    print("1. cd training-analyzer")
    print("2. Configure .env file (copy from .env.example)")
    print("3. docker-compose up -d")
    print("4. Open http://localhost:3000")


if __name__ == "__main__":
    create_structure()
