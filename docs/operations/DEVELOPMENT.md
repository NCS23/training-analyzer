# 🛠️ Development Guide

## Quick Start

### 1. Setup Environment

```bash
# Clone and navigate
cd training-analyzer

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Start with Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### 3. Manual Development Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

---

## 📁 Project Structure Explained

### Backend (Clean Architecture)

```
backend/app/
├── api/                  # API Layer (Controllers)
│   └── v1/
│       ├── router.py    # Main API router
│       ├── workouts.py  # Workout endpoints
│       ├── ai.py        # AI endpoints
│       └── health.py    # Health checks
│
├── application/          # Application Layer (Use Cases)
│   ├── use_cases/       # Business workflows
│   └── services/        # Application services
│
├── domain/              # Domain Layer (Business Logic)
│   ├── entities/        # Domain entities
│   │   └── workout.py
│   ├── value_objects/   # Immutable values
│   └── interfaces/      # Ports (Dependency Inversion)
│       └── ai_service.py
│
├── infrastructure/      # Infrastructure Layer
│   ├── database/        # Database implementation
│   │   ├── models.py   # SQLAlchemy models
│   │   └── session.py  # DB session
│   └── ai/             # AI implementations
│       ├── ai_service.py
│       └── providers/
│           ├── claude_provider.py
│           └── ollama_provider.py
│
└── core/               # Core configuration
    └── config.py       # Settings (Pydantic)
```

**Key Principles:**
- **Dependency Inversion:** Domain depends on interfaces, not implementations
- **Testability:** Mock infrastructure, test business logic
- **Separation of Concerns:** Each layer has clear responsibility

### Frontend (Feature-based)

```
frontend/src/
├── app/                 # App configuration
├── components/         # Shared components
│   ├── ui/            # Design system components
│   └── layout/        # Layout components
├── features/          # Feature modules
│   ├── workouts/      # Workout feature
│   ├── ai-chat/       # AI chat feature
│   └── analytics/     # Analytics feature
├── design-system/     # Design tokens
└── lib/              # Third-party configs
```

---

## 🎯 Adding New Features

### Example: Add New Workout Type (Cycling)

#### 1. Update Domain Entity

```python
# backend/app/domain/entities/workout.py
@dataclass
class Workout:
    workout_type: str = "running"  # Add: running, strength, cycling
```

#### 2. Update Database Model

```python
# backend/app/infrastructure/database/models.py
class WorkoutModel(Base):
    # Add cycling-specific fields
    power_avg: Column(Integer)  # Watts
    cadence_avg: Column(Integer)  # RPM
```

#### 3. Create Migration

```bash
cd backend
alembic revision --autogenerate -m "Add cycling support"
alembic upgrade head
```

#### 4. Update API

```python
# backend/app/api/v1/workouts.py
@router.post("/workouts/upload/cycling")
async def upload_cycling_workout(...):
    # Cycling-specific parsing
    pass
```

#### 5. Add Frontend Components

```tsx
// frontend/src/features/workouts/components/CyclingUpload.tsx
export function CyclingUpload() {
  // Component logic
}
```

---

## 🤖 Adding New AI Provider

### Example: Add Google Gemini

#### 1. Create Provider Implementation

```python
# backend/app/infrastructure/ai/providers/gemini_provider.py
import google.generativeai as genai
from app.domain.interfaces.ai_service import AIProvider

class GeminiProvider(AIProvider):
    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def analyze_workout(self, workout_data: dict) -> str:
        prompt = self._build_prompt(workout_data)
        response = self.model.generate_content(prompt)
        return response.text
    
    # ... implement other methods
```

#### 2. Register in Factory

```python
# backend/app/infrastructure/ai/ai_service.py
class AIProviderFactory:
    _providers = {
        "claude": ClaudeProvider,
        "ollama": OllamaProvider,
        "gemini": GeminiProvider,  # Add here
    }
```

#### 3. Add Configuration

```python
# backend/app/core/config.py
class Settings(BaseSettings):
    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-pro"
```

#### 4. Update .env.example

```bash
# Gemini (Google)
GEMINI_API_KEY=your-key-here
GEMINI_MODEL=gemini-pro
```

---

## 🧪 Testing

### Unit Tests

```python
# backend/app/tests/unit/test_workout_service.py
import pytest
from app.domain.entities.workout import Workout

def test_workout_creation():
    workout = Workout(
        workout_type="running",
        duration_sec=3600,
        distance_km=10.0
    )
    assert workout.pace is not None
```

**Run tests:**
```bash
cd backend
pytest
pytest --cov=app --cov-report=html
```

### Integration Tests

```python
# backend/app/tests/integration/test_workout_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_upload_workout(client: AsyncClient):
    files = {"csv_file": ("test.csv", csv_content)}
    response = await client.post("/api/v1/workouts/upload", files=files)
    assert response.status_code == 200
```

### Frontend Tests

```typescript
// frontend/src/components/ui/Button/Button.test.tsx
import { render, screen } from '@testing-library/react'
import { Button } from './Button'

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByText('Click me')).toBeInTheDocument()
  })
})
```

**Run tests:**
```bash
cd frontend
npm run test
npm run test:coverage
```

---

## 📊 Database Migrations

### Create Migration

```bash
cd backend

# Auto-generate from model changes
alembic revision --autogenerate -m "Add new field"

# Create empty migration
alembic revision -m "Custom migration"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Downgrade one version
alembic downgrade -1

# Show current version
alembic current

# Show history
alembic history
```

### Example Migration

```python
# backend/alembic/versions/xxx_add_power_field.py
def upgrade():
    op.add_column('workouts', 
        sa.Column('power_avg', sa.Integer(), nullable=True)
    )

def downgrade():
    op.drop_column('workouts', 'power_avg')
```

---

## 🎨 Design System

### Adding New Design Token

```typescript
// frontend/src/design-system/tokens/colors.ts
export const colors = {
  // Add new semantic color
  info: {
    DEFAULT: '#3b82f6',
    hover: '#2563eb',
    muted: '#93c5fd',
  }
}
```

### Creating New Component

```tsx
// frontend/src/components/ui/Alert/Alert.tsx
import { colors } from '@/design-system/tokens/colors'

interface AlertProps {
  variant?: 'success' | 'warning' | 'danger' | 'info'
  children: React.ReactNode
}

export function Alert({ variant = 'info', children }: AlertProps) {
  return (
    <div className={`p-4 rounded-lg bg-${variant}`}>
      {children}
    </div>
  )
}
```

**Add to Tailwind:**
```javascript
// frontend/tailwind.config.js
theme: {
  extend: {
    colors: {
      info: colors.info,
    }
  }
}
```

---

## 🚀 Deployment

### Railway.app

```bash
# Install CLI
npm i -g @railway/cli

# Login
railway login

# Link project
railway link

# Deploy
railway up
```

### Docker Production Build

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Push to registry
docker tag training-analyzer-backend:latest your-registry/backend:latest
docker push your-registry/backend:latest

# Deploy on server
docker-compose -f docker-compose.prod.yml up -d
```

### Environment Variables (Production)

```bash
# .env.production
DATABASE_URL=postgresql://user:pass@prod-db/training_analyzer
SECRET_KEY=production-secret-min-32-chars
ALLOWED_ORIGINS=https://your-domain.com
DEBUG=false
```

---

## 🐛 Debugging

### Backend Debug

```python
# Add breakpoint
import ipdb; ipdb.set_trace()

# Or use logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"Workout data: {workout_data}")
```

### Frontend Debug

```typescript
// React DevTools
console.log('Workout data:', workoutData)

// Network debugging
// Check browser DevTools -> Network tab
```

### Docker Debugging

```bash
# View logs
docker-compose logs -f backend

# Execute commands in container
docker-compose exec backend bash
docker-compose exec backend python

# Check database
docker-compose exec postgres psql -U training_user -d training_analyzer
```

---

## 📝 Code Style

### Backend (Python)

```bash
# Format code
ruff format app/

# Lint
ruff check app/ --fix

# Type check
mypy app/
```

### Frontend (TypeScript)

```bash
# Format
npm run format

# Lint
npm run lint

# Type check
npm run type-check
```

### Pre-commit Hooks

```bash
# Install
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## 🔍 Troubleshooting

### Common Issues

**Database connection fails:**
```bash
# Check if PostgreSQL is running
docker-compose ps

# Reset database
docker-compose down -v
docker-compose up -d
```

**AI provider not available:**
```bash
# Test provider
curl http://localhost:8000/api/v1/ai/providers

# For Ollama
docker exec -it ollama ollama list
docker exec -it ollama ollama pull llama3.1:8b
```

**Frontend build fails:**
```bash
# Clear cache
rm -rf node_modules
npm install

# Check Node version
node --version  # Should be 20+
```

---

## 📚 Additional Resources

### Documentation
- [FastAPI Docs](https://fastapi.tiangolo.com)
- [React Docs](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [SQLAlchemy](https://docs.sqlalchemy.org)

### AI Providers
- [Anthropic Claude](https://docs.anthropic.com)
- [Ollama](https://ollama.ai)
- [OpenAI](https://platform.openai.com/docs)

---

## 💡 Best Practices

1. **Always write tests** for new features
2. **Use type hints** in Python
3. **Follow Clean Architecture** principles
4. **Keep functions small** (<50 lines)
5. **Document complex logic** with comments
6. **Use meaningful variable names**
7. **Commit often** with clear messages
8. **Review your own code** before PR

---

**Happy Coding! 🚀**
