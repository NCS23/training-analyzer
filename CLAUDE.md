# Training Analyzer — Claude Code Regeln

## Quick Links

- [PROJEKT_REGELN.md](docs/PROJEKT_REGELN.md) — Technische Regeln (Frontend, Backend, Testing)
- [DESIGN_REVIEW.md](docs/DESIGN_REVIEW.md) — UX & Design Review Checkliste
- [DOMAIN_MODEL.md](docs/DOMAIN_MODEL.md) — Domaenenmodell (15 Entities, 200+ Felder)
- [TRAINING_CONTEXT.md](docs/TRAINING_CONTEXT.md) — Trainingskontext (HM Sub-2h)

---

## Grundregel: Kein Code ohne Issue

**Es wird NICHTS ohne GitHub Issue gemacht.** Kein Feature, kein Bugfix, kein Refactoring, keine Config-Aenderung.

- Vor jeder Arbeit MUSS ein Issue existieren oder erstellt werden
- Das Issue MUSS Akzeptanzkriterien und Taskbreakdown enthalten
- Stories MUESSEN als Sub-Issue eines Epics angelegt werden
- Der Branch-Name referenziert das Issue (z.B. `feature/E01-S01-csv-upload`)
- Commits referenzieren das Issue im Body
- Erst wenn das Issue geschlossen ist, ist die Arbeit abgeschlossen

---

## Pflicht-Workflow (4 Phasen)

Jedes Feature, jeder Bugfix, jede Aenderung durchlaeuft diese Phasen.
**Keine Abkuerzungen. Keine Ausnahmen.**

### Phase 0: Pre-Code Pflichtlektuere

Vor der ersten Zeile Code:

1. **PROJEKT_REGELN.md lesen** — Mobile-First, Nordlig DS, API-Design, Testing
2. **DESIGN_REVIEW.md lesen** — 5 Saeulen, 7 Kriterien, Nordlig-Heuristik
3. **DOMAIN_MODEL.md lesen** — Entities und deren Beziehungen verstehen
4. Bei UI-Aenderungen: relevante Nordlig DS Komponenten in Storybook pruefen

### Phase 1: Issue & Branch

1. **GitHub Issue pruefen** — Akzeptanzkriterien und Taskbreakdown lesen
2. **Issue im Project Board** — Issue muss im "Development Backlog" Project sein
3. **Sub-Issue Hierarchie** — Neue Stories als Sub-Issue des passenden Epics anlegen
4. **Branch erstellen** — `feature/E01-S01-csv-upload` oder `fix/hr-zone-calc`
5. **Scope klaeren** — Nur das umsetzen was im Issue steht, nicht mehr

### Phase 2: Implementation

**Frontend:**
- Mobile-First: Immer zuerst fuer 375px designen, dann nach oben erweitern
- Nordlig DS Komponenten verwenden — KEINE eigenen Buttons, Inputs, Cards etc.
- Nur `var(--*)` Tokens — KEINE hardcodierten Farben, Spacing, Radii
- TypeScript strict — keine `any`, keine `@ts-ignore`
- React Query fuer Server-State, Zustand fuer Client-State

**Backend:**
- Clean Architecture: Domain → Application → Infrastructure → API
- Pydantic Models fuer Request/Response Validation
- Async/Await konsequent
- Type Hints ueberall — mypy strict muss bestehen
- Tests parallel zur Implementation schreiben

**Fuer beide:**
- Kleine, fokussierte Commits
- Tests MUESSEN vor dem Commit gruen sein

### Phase 3: Quality Gates

**Vor jedem Commit muessen ALLE Gates bestehen:**

```bash
# Frontend (ALLE muessen bestehen)
cd frontend
npx eslint src/ --max-warnings 0
npx prettier --check "src/**/*.{ts,tsx,css}"
npx tsc --noEmit
npx vitest --run

# Backend (ALLE muessen bestehen)
cd backend
ruff check app/
ruff format --check app/
mypy app/
pytest app/tests/ -x
```

**Automatische Durchsetzung (Claude Code Hooks):**
Diese Quality Gates werden durch Hooks in `.claude/hooks/` erzwungen:
- `git commit` wird BLOCKIERT wenn Gates nicht bestanden haben
- `git push` wird BLOCKIERT bei Push auf main ohne Feature-Branch
- Nach `git push` wird CI-Monitoring erzwungen
- Bypass nur mit expliziter User-Genehmigung ("skip checks")

**UX & Design Review (selbst durchgefuehrt):**
- DESIGN_REVIEW.md Checkliste durchgehen
- Auf iPhone-Viewport (375px) pruefen
- Touch-Targets pruefen (min. 44×44px)
- Alle Nordlig Gestaltungskriterien pruefen
- Kritische + schwerwiegende Findings VOR Commit fixen

### Phase 4: Abschluss

1. Commit + Push
2. CI-Workflow abwarten — MUSS gruen sein
3. Bei CI-Fehler: lokal fixen, neu pushen
4. GitHub Issue kommentieren (was wurde gemacht, Review-Ergebnisse)
5. GitHub Issue schliessen

---

## Projekt-Stack

| Layer | Technologie |
|-------|-------------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS |
| **UI** | Nordlig Design System (`@nordlig/components`) |
| **State** | Zustand (Client), React Query (Server) |
| **Charts** | Recharts |
| **Karten** | Leaflet / MapLibre (TBD) |
| **Backend** | FastAPI, Python 3.11+, Pydantic |
| **Datenbank** | PostgreSQL 15, SQLAlchemy 2.0, Alembic |
| **AI** | Claude API, Ollama (Fallback) |
| **Tests FE** | Vitest, Testing Library, Playwright |
| **Tests BE** | Pytest, pytest-asyncio |
| **CI** | GitHub Actions |
| **Deployment** | Docker Compose via Coolify (Hetzner) |

---

## GitHub

- **Repo:** `NCS23/training-analyzer` (privat)
- **Issues:** `gh issue list -R NCS23/training-analyzer`
- **Milestones:** MVP (P0), Release 1.1 (P1), Release 1.2 (P2), Post-Launch (P3-P4)
- **Project Board:** `gh project view 1 --owner NCS23` (repo-uebergreifend mit NDS)

### Project Board Workflow

Alle Issues werden im **"Development Backlog"** Project verwaltet. Custom Fields:
- **Priority:** P0-MVP, P1-High, P2-Medium, P3-Low, P4-Future
- **Type:** Epic, Story, Bug, Tech, Docs, Figma
- **Size:** S, M, L, XL
- **Product:** Training Analyzer, Nordlig DS

### Epics & Sub-Issues

Epics sind uebergeordnete Tracking-Issues (#77-#90). Stories werden als **Sub-Issues** angelegt — das gibt automatischen Fortschritts-Tracking im Epic.

```bash
# Issues auflisten
gh issue list -R NCS23/training-analyzer --state open

# Issue erstellen
gh issue create -R NCS23/training-analyzer --title "..." --body "..."

# Issue zum Project hinzufuegen
gh project item-add 1 --owner NCS23 --url <issue-url>

# Story als Sub-Issue eines Epics verlinken
STORY_ID=$(gh api repos/NCS23/training-analyzer/issues/<story-nr> --jq .id)
gh api repos/NCS23/training-analyzer/issues/<epic-nr>/sub_issues -X POST -F sub_issue_id=$STORY_ID

# Neues Epic erstellen (wenn neues Thema)
gh api repos/NCS23/training-analyzer/issues -X POST \
  -f title="Epic: <Thema>" -f 'labels[]=epic' -f body="## Stories\n- [ ] #XX"
```

---

## Verbotene Muster

### Frontend
- ❌ `bg-white`, `bg-gray-*`, `text-gray-*` → ✅ `bg-[var(--color-bg-base)]`
- ❌ `px-4`, `py-2` fuer Komponenten-Spacing → ✅ `p-[var(--spacing-*)]`
- ❌ `rounded-md`, `rounded-lg` → ✅ `rounded-[var(--radius-*)]`
- ❌ `shadow-sm`, `shadow-md` → ✅ `shadow-[var(--shadow-*)]`
- ❌ Eigene `<button>`, `<input>`, `<select>` → ✅ Nordlig `<Button>`, `<Input>`, `<Select>`
- ❌ `any` Type → ✅ Explizite Types
- ❌ `@ts-ignore` → ✅ Problem loesen
- ❌ Desktop-First Media Queries → ✅ Mobile-First (`min-width`)

### Backend
- ❌ `dict` als API Response → ✅ Pydantic Model
- ❌ Raw SQL → ✅ SQLAlchemy ORM
- ❌ `# type: ignore` → ✅ Problem loesen
- ❌ Synchrone DB-Operationen → ✅ Async
- ❌ Hardcodierte Konfiguration → ✅ Pydantic Settings / Environment

---

## Definition of Done

Ein Feature ist DONE wenn:

- [ ] Alle Akzeptanzkriterien aus dem Issue erfuellt
- [ ] Frontend: ESLint 0 Warnings, TypeScript kompiliert
- [ ] Backend: Ruff + Mypy bestehen
- [ ] Unit Tests geschrieben und gruen (Coverage >= 80%)
- [ ] UX/Design Review durchgefuehrt (DESIGN_REVIEW.md)
- [ ] Mobile-First geprueft (375px iPhone SE)
- [ ] Touch-Targets >= 44×44px
- [ ] Nordlig DS Komponenten verwendet (keine eigenen Primitives)
- [ ] CI-Pipeline gruen
- [ ] GitHub Issue kommentiert und geschlossen
