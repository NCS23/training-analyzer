# 🏃‍♂️ Training Analyzer

**Enterprise-grade training analysis platform for half-marathon preparation with AI-powered insights.**

[![CI](https://github.com/yourusername/training-analyzer/workflows/CI/badge.svg)](https://github.com/yourusername/training-analyzer/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 Features

### Core Functionality
- ✅ **CSV Upload & Analysis** - Apple Watch workout data (running + strength)
- ✅ **OCR Integration** - Automatic exercise extraction from EGYM screenshots via Docling
- ✅ **Training Plan Management** - Markdown-based plans with versioning
- ✅ **AI-Powered Insights** - Workout analysis, weekly reports, chat interface
- ✅ **Progress Tracking** - Pace progression, HF efficiency, weekly load
- ✅ **Multi-Device Support** - Responsive design (Desktop, Tablet, Mobile)

### AI Provider Flexibility
- 🤖 **Claude (Anthropic)** - Premium quality analysis
- 🦙 **Ollama (Self-hosted)** - Cost-free, privacy-focused
- 🧠 **OpenAI (GPT-4)** - Alternative cloud option
- 🔄 **Automatic Fallback** - Seamless provider switching

### Analytics & Visualization
- 📊 **HF Efficiency Chart** - Aerobic fitness progression
- 📈 **Pace Progression** - Interval training development
- 💪 **Weekly Load** - Training volume & intensity distribution

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  - Design System (Tailwind + Tokens)                    │
│  - Component Library (shadcn/ui)                        │
│  - State Management (Zustand)                           │
│  - Charts (Recharts)                                    │
└─────────────────┬───────────────────────────────────────┘
                  │ REST API
┌─────────────────▼───────────────────────────────────────┐
│              Backend (FastAPI)                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Clean Architecture (Hexagonal)          │   │
│  │  - API Layer (Routes)                           │   │
│  │  - Application Layer (Use Cases)                │   │
│  │  - Domain Layer (Business Logic)                │   │
│  │  - Infrastructure Layer (DB, OCR, AI)           │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────┬───────────────────────────────────────┘
                  │
    ┌─────────────┼─────────────┬─────────────┐
    │             │             │             │
┌───▼────┐  ┌────▼─────┐  ┌───▼──────┐  ┌──▼─────┐
│Database│  │ Docling  │  │ AI       │  │ File   │
│(SQLite/│  │ OCR      │  │ Providers│  │Storage │
│Postgres)│  │ Server   │  │          │  │        │
└────────┘  └──────────┘  └──────────┘  └────────┘
```

**Technology Stack:**
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Zustand
- **Backend:** FastAPI (Python 3.11+), SQLAlchemy, Pydantic
- **Database:** SQLite (dev), PostgreSQL (prod)
- **AI:** Anthropic SDK, OpenAI SDK, Ollama HTTP API
- **OCR:** Docling Server
- **Testing:** Vitest, Pytest, Playwright
- **DevOps:** Docker, GitHub Actions

---

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** (recommended)
- **OR** Manual setup:
  - Node.js 20+
  - Python 3.11+
  - PostgreSQL 15+ (for production)

### Option A: Docker Compose (Recommended)

```bash
# 1. Clone repository
git clone https://github.com/yourusername/training-analyzer.git
cd training-analyzer

# 2. Configure environment
cp .env.example .env
# Edit .env with your settings (API keys, etc.)

# 3. Start all services
docker-compose up -d

# 4. Access the app
open http://localhost:3000
```

**Services started:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: PostgreSQL on port 5432
- Ollama (optional): http://localhost:11434

### Option B: Manual Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Setup database
alembic upgrade head

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with backend URL

# Run development server
npm run dev
```

---

## ⚙️ Configuration

### Environment Variables

#### Backend (.env)

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/training_analyzer

# AI Providers
AI_PRIMARY_PROVIDER=claude  # claude, ollama, openai
AI_FALLBACK_PROVIDERS=ollama,openai

# Claude (Anthropic)
CLAUDE_API_KEY=sk-ant-xxx
CLAUDE_MODEL=claude-sonnet-4-20250514

# Ollama (Self-hosted)
OLLAMA_BASE_URL=http://192.168.68.66:11434
OLLAMA_MODEL=llama3.1:8b

# OpenAI (Optional)
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4-turbo

# Docling OCR
DOCLING_SERVER_URL=http://192.168.68.66:5001

# Security
SECRET_KEY=your-secret-key-here-min-32-chars
ALGORITHM=HS256

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

#### Frontend (.env.local)

```bash
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=Training Analyzer
```

---

## 🐳 Docker Deployment (NAS)

### Setup on Synology/QNAP NAS

```bash
# 1. SSH into NAS
ssh admin@your-nas-ip

# 2. Clone repo
cd /volume1/docker
git clone https://github.com/yourusername/training-analyzer.git
cd training-analyzer

# 3. Configure for NAS
cp docker-compose.nas.yml docker-compose.yml
cp .env.example .env
nano .env  # Edit with your settings

# 4. Start services
docker-compose up -d

# 5. Access app
# http://your-nas-ip:3000
```

**Ports on NAS:**
- Frontend: 3000
- Backend: 8000
- PostgreSQL: 5432 (internal only)
- Ollama: 11434 (optional)

### Ollama Setup (Self-hosted AI)

```bash
# Start Ollama
docker-compose up -d ollama

# Pull model (choose one based on NAS performance)
docker exec -it ollama ollama pull llama3.1:8b      # 4.7GB, fast
docker exec -it ollama ollama pull llama3.1:70b     # 40GB, better quality
docker exec -it ollama ollama pull mistral:7b       # 4.1GB, alternative

# Test
curl http://localhost:11434/api/tags
```

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest app/tests/unit/test_workout_service.py -v

# Integration tests
pytest app/tests/integration/ -v
```

### Frontend Tests

```bash
cd frontend

# Unit tests
npm run test

# Watch mode
npm run test:watch

# Coverage
npm run test:coverage

# E2E tests (Playwright)
npm run test:e2e
```

---

## 📚 Documentation

### API Documentation

Auto-generated OpenAPI docs available at:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

### Component Documentation

Storybook (component library):
```bash
cd frontend
npm run storybook
# Open http://localhost:6006
```

### Architecture Documentation

- [Architecture Decision Records](./docs/adr/)
- [API Design](./docs/api-design.md)
- [Database Schema](./docs/database-schema.md)
- [AI Provider Guide](./docs/ai-providers.md)

---

## 🔧 Development

### Project Structure

```
training-analyzer/
├── frontend/              # React application
│   ├── src/
│   │   ├── app/          # App config
│   │   ├── components/   # Shared components
│   │   ├── features/     # Feature modules
│   │   ├── design-system/ # Design tokens
│   │   └── ...
│   └── package.json
│
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── application/ # Use cases
│   │   ├── domain/      # Business logic
│   │   ├── infrastructure/ # External services
│   │   └── core/        # Config
│   └── pyproject.toml
│
├── docs/                # Documentation
├── docker-compose.yml   # Development setup
└── .github/             # CI/CD workflows
```

### Code Quality

**Pre-commit hooks:**
```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

**Linting:**
```bash
# Frontend
cd frontend
npm run lint
npm run format

# Backend
cd backend
ruff check app/
ruff format app/
mypy app/
```

---

## 🚢 Production Deployment

### Railway.app (Recommended)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Deploy
railway up
```

### Manual Production Setup

1. **Build Frontend:**
```bash
cd frontend
npm run build
# Outputs to frontend/dist
```

2. **Configure Backend for Production:**
```bash
# backend/.env.production
DATABASE_URL=postgresql://prod-user:pass@prod-db:5432/training_analyzer
ALLOWED_ORIGINS=https://your-domain.com
SECRET_KEY=production-secret-min-32-chars
```

3. **Run with Gunicorn:**
```bash
cd backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

4. **Serve Frontend:**
Use Nginx, Caddy, or any static file server to serve `frontend/dist`

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) first.

### Development Workflow

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Standards

- **TypeScript:** Strict mode, explicit types
- **Python:** Type hints, docstrings, PEP 8
- **Tests:** >80% coverage required
- **Commits:** Conventional Commits format

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](./LICENSE) file.

---

## 🙏 Acknowledgments

- **Anthropic** - Claude AI API
- **Ollama** - Self-hosted LLM platform
- **Docling** - Document parsing & OCR
- **shadcn/ui** - Component library
- **FastAPI** - Python web framework

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/training-analyzer/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/training-analyzer/discussions)

---

## 🗺️ Roadmap

### Phase 1 (Current)
- ✅ CSV Upload & Analysis
- ✅ AI Provider System
- ✅ Training Plan Management
- ✅ Basic Charts

### Phase 2 (Next)
- [ ] Advanced Analytics (TRIMP, Training Load)
- [ ] Race Predictor
- [ ] Mobile App (React Native)
- [ ] Social Features (Share workouts)

### Phase 3 (Future)
- [ ] Multi-user / Coach-Athlete
- [ ] Wearable Integration (Garmin, Polar)
- [ ] Nutrition Tracking
- [ ] Injury Prevention Alerts

---

**Built with ❤️ for runners by runners**
