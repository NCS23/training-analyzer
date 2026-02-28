# Training Analyzer - Project Context

**For Claude Code: Read this document first!** 📖

Last Updated: 2026-02-12  
Current Phase: Phase 1 - Web App Development (Week 7/2026)

---

## 🎯 Project Overview

**What:** Training Analyzer for half-marathon preparation  
**Who:** Nils-Christian (Runner, Sub-2h goal end of March 2026)  
**Stack:** FastAPI (Backend) + React/TypeScript (Frontend) + PostgreSQL  
**Deployed:** Synology NAS (Docker Compose, GitHub Actions)

**Current Status:**
- ✅ CSV Upload & Parsing (Running + Strength)
- ✅ Lap Classification with User Override
- ✅ HR Zones (Total + Working Laps)
- 🔄 FIT Import (in progress)
- ⏳ Database Persistence (planned)

**Next Goal:** PostgreSQL integration + Session persistence

---

## 🏗️ Tech Stack

### Backend
- Framework: FastAPI 0.104+
- Language: Python 3.11
- Database: PostgreSQL 15 (planned, not yet implemented)
- ORM: SQLAlchemy 2.0 (planned)
- Parsing: fitparse (FIT), pandas (CSV)
- Deployment: Docker Compose on Synology NAS

### Frontend
- Framework: React 18
- Language: TypeScript 4.9+
- Build: Vite
- UI: Tailwind CSS, lucide-react
- Charts: recharts (planned)

### Infrastructure
- Container: Docker Compose
- Reverse Proxy: Nginx (on NAS)
- CI/CD: GitHub Actions → Auto-Deploy
- VCS: GitHub

---

## 📁 Repository Structure

```
training-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI App Entry
│   │   ├── models/
│   │   │   └── training.py      # SQLAlchemy Models (planned)
│   │   ├── services/
│   │   │   ├── csv_parser.py    # ✅ CSV Parsing + Lap Classification
│   │   │   └── fit_parser.py    # 🔄 FIT Parsing (in progress)
│   │   └── routers/
│   │       └── training.py      # API Endpoints
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── Upload.tsx       # ✅ Main Upload UI
│   │   ├── components/
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── docs/
│   ├── CONTEXT.md               # ⭐ This file!
│   ├── IMPLEMENTATION_STATUS.md # What's done/todo
│   ├── DOMAIN_MODEL.md          # Technical architecture
│   ├── TRAINING_CONTEXT.md      # Nils' training goals
│   ├── USER_STORIES.md          # Requirements
│   ├── DEVELOPMENT_ROADMAP.md   # 3-phase plan
│   ├── AI_ANALYSIS_INTEGRATION.md
│   ├── NATIVE_APP_STRATEGY.md
│   ├── CSV_FORMAT_EXAMPLES.md
│   ├── QUICK_REFERENCE.md
│   ├── QUICKSTART.md
│   └── DEVELOPMENT.md
├── docker-compose.yml
└── README.md
```

---

## 📊 Data Model (High-Level)

**Core Entities:**

```python
TrainingSession (1)
  ├── id: UUID
  ├── date: DateTime
  ├── training_type: Enum (running, strength)
  ├── training_subtype: Enum (interval, longrun, recovery, tempo)
  ├── source_file_type: Enum (CSV, FIT)
  ├── avg_heart_rate: int
  ├── avg_pace: float (min/km)
  └── Laps (N)
       ├── lap_number: int
       ├── lap_type: Enum (warmup, interval, recovery, cooldown, ...)
       ├── duration: int (seconds)
       ├── avg_heart_rate: int
       ├── avg_pace: float
       └── running_dynamics: JSON (FIT only)
           ├── avg_cadence: int (spm)
           ├── avg_ground_contact_time: int (ms)
           ├── avg_vertical_oscillation: float (cm)
           └── avg_vertical_ratio: float (%)
```

**Details:** See `docs/DOMAIN_MODEL.md`

---

## 🎯 Current Phase: Phase 1 - Web App

**Timeline:** 10 weeks (KW06-15/2026)

### Week 1-2: FIT Import ✅ (current: KW07)
```
Status: 🔄 In Progress
Tasks:
  ✅ Basic FIT Parsing (fitparse integration)
  ✅ Session Metadata Extraction
  🔄 Running Dynamics (Cadence, GCT, VO, VR)
  🔄 Power Data (if available)
  🔄 Workout Structure Parsing
  ⏳ Tests
  
Key Files:
  - backend/app/services/fit_parser.py
  - backend/tests/test_fit_parser.py
```

### Week 3-4: Lap Classification ⏳
```
Status: ⏳ TODO
Tasks:
  - Auto-Classification (HR-based)
  - FIT Workout Steps → Lap Types
  - Manual Override UI
  - Confidence Scoring
  
Key Files:
  - backend/app/services/lap_classifier.py (create)
  - frontend/src/components/LapClassification.tsx (create)
```

### Week 5-6: AI Analysis ⏳
```
Status: ⏳ TODO
Tasks:
  - Anthropic API Integration
  - Backend: AIAnalysisService
  - Frontend: AI Analysis Component
  - Prompt Engineering
  
Key Files:
  - backend/app/services/ai_analysis.py (create)
  - frontend/src/components/AIAnalysis.tsx (create)
  
Reference: docs/AI_ANALYSIS_INTEGRATION.md
```

**Full Roadmap:** See `docs/DEVELOPMENT_ROADMAP.md`

---

## 🔑 Key Concepts

### Lap Types (Enum)
```python
class LapType(str, Enum):
    WARMUP = "warmup"       # Warm-up
    INTERVAL = "interval"   # Intense work
    RECOVERY = "recovery"   # Active recovery / jog
    COOLDOWN = "cooldown"   # Cool-down
    STEADY = "steady"       # Steady pace
    UNKNOWN = "unknown"     # Unclassified
```

### Training Subtypes (Enum)
```python
class TrainingSubtype(str, Enum):
    INTERVAL = "interval"   # Interval training
    TEMPO = "tempo"         # Tempo run
    LONGRUN = "longrun"     # Long run
    RECOVERY = "recovery"   # Recovery run
```

### HR Zones (3-Zone System)
```
Zone 1 (<150 bpm):  Recovery
Zone 2 (150-160):   Base
Zone 3 (>160 bpm):  Tempo/Intense
```

### Running Dynamics (FIT Files Only!)
```
Available ONLY in FIT files, NOT in CSV!
- Cadence (steps per minute)
- Ground Contact Time (milliseconds)
- Vertical Oscillation (centimeters)
- Vertical Ratio (efficiency %)
- Power (optional, not all watches)
```

---

## 📝 Code Conventions

### Python (Backend)
```python
# Type hints everywhere
def parse_fit_file(file_path: Path) -> TrainingSession:
    ...

# Async/await for I/O
async def get_session(session_id: UUID) -> TrainingSession:
    ...

# Pydantic for validation
class SessionCreate(BaseModel):
    date: datetime
    training_type: TrainingType
    
# Error handling
try:
    result = parse_fit(file)
except FITParseError as e:
    logger.error(f"FIT parsing failed: {e}")
    raise HTTPException(status_code=400, detail=str(e))
```

### TypeScript (Frontend)
```typescript
// Strict types
interface TrainingSession {
  id: string;
  date: string;
  trainingType: TrainingType;
  laps: Lap[];
}

// Async/await
const fetchSession = async (id: string): Promise<TrainingSession> => {
  const response = await fetch(`/api/v1/sessions/${id}`);
  return response.json();
};

// Error handling
try {
  await uploadFile(file);
} catch (error) {
  console.error('Upload failed:', error);
  setError(error.message);
}
```

---

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_fit_parser.py -v
```

### Frontend Tests
```bash
# Run tests
npm test

# Run with coverage
npm run test:coverage
```

---

## 🚀 Development Workflow

### Backend Development
```bash
# Activate venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn app.main:app --reload

# Run in Docker
docker-compose up backend
```

### Frontend Development
```bash
# Install dependencies
npm install

# Dev server
npm run dev

# Build
npm run build
```

---

## 🔧 Common Tasks

### Add New API Endpoint
```python
# 1. backend/app/routers/sessions.py
@router.post("/sessions/{id}/analyze")
async def analyze_session(id: UUID):
    ...

# 2. backend/app/services/ai_analysis.py
async def analyze_session(session: TrainingSession) -> Analysis:
    ...

# 3. tests/test_analysis.py
def test_analyze_session():
    ...
```

### Add New Frontend Component
```typescript
// 1. frontend/src/components/NewComponent.tsx
export const NewComponent: React.FC<Props> = ({ ... }) => {
  ...
};

// 2. Use in page
import { NewComponent } from '@/components/NewComponent';
```

---

## 📚 Essential Documentation

**READ BEFORE IMPLEMENTING:**
1. `docs/IMPLEMENTATION_STATUS.md` - Current status
2. `docs/DOMAIN_MODEL.md` - Data models
3. `docs/TRAINING_CONTEXT.md` - Training goals & constraints
4. `docs/USER_STORIES.md` - Requirements
5. Feature-specific docs (e.g., AI_ANALYSIS_INTEGRATION.md)

---

## 🎓 Training Context (Personal)

**User:** Nils-Christian  
**Goal:** Sub-2h Half-Marathon (end of March 2026)  
**Current Week:** KW07 (Phase 1 Build-up)  
**Training Plan:** See `docs/TRAINING_CONTEXT.md`

**Important for AI Analysis:**
- Runs 4×/week (Wed/Thu/Sat + 2× strength training)
- Main priority: Health > Performance
- Problem identified: Too intense long runs (HR too high)
- Need: Automatic session analysis with feedback

---

## ⚡ Quick References

### Environment Variables
```bash
# backend/.env
DATABASE_URL=postgresql://user:pass@localhost:5432/training_db
ANTHROPIC_API_KEY=sk-ant-...  # for AI Analysis
```

### Database
```bash
# Connect to DB
psql -h localhost -U training_user -d training_db

# Run migrations (if using Alembic)
alembic upgrade head
```

### Git Workflow
```bash
# Feature branch
git checkout -b feature/fit-import

# Commit
git add .
git commit -m "feat: Add FIT running dynamics parsing"

# Push (triggers auto-deploy on NAS!)
git push origin feature/fit-import
```

---

## 🆘 Troubleshooting

### FIT Parsing Issues
- **Problem:** fitparse can't read file
- **Check:** File is valid FIT format (not JSON/XML)
- **Debug:** `fitdump <file.fit>` in terminal

### Database Connection
- **Problem:** `connection refused`
- **Check:** PostgreSQL running? `docker ps`
- **Fix:** `docker-compose up -d db`

### Docker Build Fails
- **Problem:** `npm install` fails
- **Check:** package-lock.json present?
- **Fix:** Rebuild without cache: `docker-compose build --no-cache`

---

## 📞 Getting Help

**Documentation:**
- FastAPI Docs: http://localhost:8000/docs (when running locally)
- Project Docs: `/docs/*.md`
- API Spec: Will be in `/docs/API_SPEC.md` (to be created)

**External Resources:**
- fitparse: https://github.com/dtcooper/python-fitparse
- Anthropic API: https://docs.anthropic.com
- FastAPI: https://fastapi.tiangolo.com

---

## ✅ Before You Start (Checklist)

For Claude Code tasks:

- [ ] Read CONTEXT.md? (this file)
- [ ] Check IMPLEMENTATION_STATUS.md for current status?
- [ ] Check DOMAIN_MODEL.md for data models?
- [ ] Read feature-specific docs? (e.g., AI_ANALYSIS_INTEGRATION.md)
- [ ] Repo cloned locally & VS Code opened?
- [ ] Dependencies installed? (`pip install -r requirements.txt`, `npm install`)

---

## 🚀 Ready to Code!

**Your first task should be:**
1. Read this CONTEXT.md ✅
2. Read IMPLEMENTATION_STATUS.md
3. Read relevant feature docs
4. Then: Start concrete task!

**Happy Coding! 🎯**
