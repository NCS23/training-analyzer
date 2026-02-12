# 📋 Training Analyzer - Product Backlog

**Last Updated:** 2026-02-12  
**Current Sprint:** Week 7/2026 - PostgreSQL Integration

---

## 🎯 Active Epics

### Epic 1: Database Persistence 🔴 IN PROGRESS
**Priority:** CRITICAL  
**Timeline:** Week 7-9 (3 weeks)  
**Goal:** Trainings persistent speichern

#### Story 1.1: PostgreSQL Setup ✅ DONE
**Status:** ✅ DONE  
**Priority:** 🔴 CRITICAL

- [x] Task: Add PostgreSQL to docker-compose.yml
- [x] Task: Configure environment variables
- [x] Task: Test database connection
- [x] Task: Setup pgAdmin (optional)

#### Story 1.2: SQLAlchemy Models 🔄 IN PROGRESS
**Status:** 🔄 IN PROGRESS  
**Priority:** 🔴 CRITICAL  
**Assignee:** Claude

- [x] Task: Define Athlete model
- [ ] Task: Define TrainingSession model
- [ ] Task: Define TrainingLap model
- [ ] Task: Define HRZoneConfig model
- [ ] Task: Define relationships between models
- [ ] Task: Add indexes for performance

**Acceptance Criteria:**
- All models match DOMAIN_MODEL.md
- Relationships properly defined
- Indexes on frequently queried fields
- All fields have proper types & constraints

#### Story 1.3: Database Migrations 📋 PLANNED
**Status:** 📋 PLANNED  
**Priority:** 🔴 CRITICAL

- [ ] Task: Setup Alembic
- [ ] Task: Create initial migration
- [ ] Task: Test migration up/down
- [ ] Task: Document migration workflow

#### Story 1.4: Session Management API 📋 PLANNED
**Status:** 📋 PLANNED  
**Priority:** 🔴 CRITICAL

- [ ] Task: POST /api/v1/sessions (create from CSV/FIT)
- [ ] Task: GET /api/v1/sessions (list with filters)
- [ ] Task: GET /api/v1/sessions/{id} (detail view)
- [ ] Task: DELETE /api/v1/sessions/{id}
- [ ] Task: PATCH /api/v1/sessions/{id} (update lap types)

**Acceptance Criteria:**
- All endpoints RESTful
- Proper error handling
- Input validation with Pydantic
- Swagger docs complete
- Integration tests passing

#### Story 1.5: Frontend Session Management 📋 PLANNED
**Status:** 📋 PLANNED  
**Priority:** 🟠 HIGH

- [ ] Task: Create SessionList component
- [ ] Task: Create SessionDetail component
- [ ] Task: Add session filters (date, type)
- [ ] Task: Add delete confirmation dialog
- [ ] Task: Add loading/error states

---

### Epic 2: AI Analysis Integration ⏳ PLANNED
**Priority:** HIGH  
**Timeline:** Week 10-11 (2 weeks)  
**Goal:** Automatic training analysis with Claude API

#### Story 2.1: Backend AI Service 📋 PLANNED
**Status:** 📋 PLANNED  
**Priority:** 🟠 HIGH

- [ ] Task: Setup Anthropic API client
- [ ] Task: Implement AIAnalysisService
- [ ] Task: Create prompt templates
- [ ] Task: Add caching layer
- [ ] Task: Error handling & fallbacks

**Reference:** `docs/AI_ANALYSIS_INTEGRATION.md`

#### Story 2.2: Session Analysis Endpoint 📋 PLANNED
**Status:** 📋 PLANNED  
**Priority:** 🟠 HIGH

- [ ] Task: POST /api/v1/sessions/{id}/analyze
- [ ] Task: Store analysis in database
- [ ] Task: Return structured analysis response

#### Story 2.3: Frontend AI Display 📋 PLANNED
**Status:** 📋 PLANNED  
**Priority:** 🟠 HIGH

- [ ] Task: Create AnalysisResult component
- [ ] Task: Add "Analyze" button to SessionDetail
- [ ] Task: Show Insights/Warnings/Recommendations
- [ ] Task: Loading state during analysis

---

### Epic 3: Training Plan Management ⏳ PLANNED
**Priority:** MEDIUM  
**Timeline:** Week 12-14 (3 weeks)  
**Goal:** Create and manage training plans

#### Story 3.1: Plan Editor (Backend) 📋 PLANNED
**Status:** 📋 PLANNED  
**Priority:** 🟡 MEDIUM

- [ ] Task: TrainingPlan model
- [ ] Task: TrainingPhase model
- [ ] Task: PlannedTraining model
- [ ] Task: TrainingTarget model
- [ ] Task: CRUD API endpoints

#### Story 3.2: Plan Editor (Frontend) 📋 PLANNED
**Status:** 📋 PLANNED  
**Priority:** 🟡 MEDIUM

- [ ] Task: Plan creation form
- [ ] Task: Phase management UI
- [ ] Task: Weekly planner
- [ ] Task: Drag & drop interface

#### Story 3.3: Soll/Ist Comparison 📋 PLANNED
**Status:** 📋 PLANNED  
**Priority:** 🟡 MEDIUM

- [ ] Task: Match actual to planned sessions
- [ ] Task: Calculate deviation metrics
- [ ] Task: Generate warnings
- [ ] Task: Display side-by-side comparison

---

### Epic 4: FIT File Support ⏳ PLANNED
**Priority:** MEDIUM  
**Timeline:** Week 15-16 (2 weeks)  
**Goal:** Support FIT uploads with Running Dynamics

**Reference:** `docs/FIT_IMPORT_NOTES.md`

#### Story 4.1: FIT Parser Implementation 📋 PLANNED
**Status:** 📋 PLANNED  
**Priority:** 🟡 MEDIUM

- [ ] Task: Integrate fitparse library
- [ ] Task: Extract session metadata
- [ ] Task: Extract laps with running dynamics
- [ ] Task: Extract workout structure
- [ ] Task: Handle missing fields gracefully

#### Story 4.2: Running Dynamics UI 📋 PLANNED
**Status:** 📋 PLANNED  
**Priority:** 🟡 MEDIUM

- [ ] Task: Display cadence charts
- [ ] Task: Display ground contact time
- [ ] Task: Display vertical oscillation
- [ ] Task: Add explanations for metrics

---

## 🔥 Hotfixes & Bugs

### 🐛 Bug: None currently reported ✅

---

## 💡 Ideas & Future Features

### Future Epic: Equipment Tracking
- Track running shoes
- Kilometer counting
- Replacement warnings

### Future Epic: Weather Integration
- Fetch weather data for sessions
- Correlate with performance
- Adjust expectations

### Future Epic: Injury Tracking
- Document injuries
- Track recovery
- Prevent patterns

### Future Epic: Charts & Visualizations
- HR over time charts
- Pace progression
- Training load trends
- Weekly/monthly summaries

---

## ✅ Recently Completed

### Week 6 (Feb 3-9)
- [x] Epic: Lap Classification & HR Zones
- [x] Story: Automatic lap type suggestion
- [x] Story: User override UI
- [x] Story: Dual HR zones (Total + Working Laps)
- [x] Story: Confidence scoring

### Week 5 (Jan 27 - Feb 2)
- [x] Epic: CSV Upload & Parsing
- [x] Story: Running CSV parsing
- [x] Story: Strength CSV parsing
- [x] Story: Basic frontend upload UI

---

## 📅 Sprint Planning

### Current Sprint (Week 7): PostgreSQL Integration
**Goal:** Database persistence working

**Sprint Backlog:**
1. ✅ PostgreSQL Docker setup
2. 🔄 SQLAlchemy models (in progress)
3. ⏳ Alembic migrations
4. ⏳ Repository pattern
5. ⏳ Basic CRUD API

**Daily Goals:**
- **Wednesday:** Complete TrainingSession model
- **Thursday:** Complete TrainingLap model + relationships
- **Friday:** First migration working
- **Saturday:** Repository pattern + first endpoint

### Next Sprint (Week 8): Session API
**Goal:** Full CRUD API for sessions

**Sprint Backlog:**
1. Complete all REST endpoints
2. Input validation
3. Error handling
4. Integration tests
5. Swagger docs

---

## 🎯 Backlog Grooming Notes

### Decisions Needed:
- [ ] AI Analysis: Which provider as primary? (Claude vs Ollama)
- [ ] Training Plans: Single user or multi-user first?
- [ ] FIT Import: Store original files or just parsed data?

### Tech Debt:
- [ ] Add proper logging throughout backend
- [ ] Improve error messages in frontend
- [ ] Add loading states everywhere
- [ ] Extract magic numbers to constants
- [ ] Add API rate limiting

### Blocked Items:
- None currently

---

## 📊 Velocity Tracking

### Week 6 Velocity: 8 story points
- Lap Classification (3 pts) ✅
- User Override UI (2 pts) ✅
- HR Zones Calculation (3 pts) ✅

### Week 7 Target: 8 story points
- PostgreSQL Setup (1 pt) ✅
- SQLAlchemy Models (4 pts) 🔄
- Alembic Migrations (2 pts) ⏳
- First API endpoint (1 pt) ⏳

---

**Update dieses Backlog nach jeder Session!** 📝
