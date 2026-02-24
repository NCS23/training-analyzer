# Training Analyzer — Claude Code Regeln

## Quick Links

- [PROJEKT_REGELN.md](docs/PROJEKT_REGELN.md) — Technische Regeln (Frontend, Backend, Testing)
- [DESIGN_REVIEW.md](docs/DESIGN_REVIEW.md) — UX & Design Review Checkliste
- [DOMAIN_MODEL.md](docs/DOMAIN_MODEL.md) — Domaenenmodell (15 Entities, 200+ Felder)
- [TRAINING_CONTEXT.md](docs/TRAINING_CONTEXT.md) — Trainingskontext (HM Sub-2h)

---

## Grundregel: Kein Code ohne Issue

**Es wird NICHTS ohne Gitea Issue gemacht.** Kein Feature, kein Bugfix, kein Refactoring, keine Config-Aenderung.

- Vor jeder Arbeit MUSS ein Issue existieren oder erstellt werden
- Das Issue MUSS Akzeptanzkriterien und Taskbreakdown enthalten
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

1. **Gitea Issue pruefen** — Akzeptanzkriterien und Taskbreakdown lesen
2. **Branch erstellen** — `feature/E01-S01-csv-upload` oder `fix/hr-zone-calc`
3. **Scope klaeren** — Nur das umsetzen was im Issue steht, nicht mehr

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
# Frontend
cd frontend
npx eslint src/ --max-warnings 0
npx vitest --run
npx tsc --noEmit

# Backend
cd backend
ruff check app/
mypy app/
pytest app/tests/ -x
```

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
4. Gitea Issue kommentieren (was wurde gemacht, Review-Ergebnisse)
5. Gitea Issue schliessen

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
| **CI** | Gitea Actions |
| **Deployment** | Docker Compose auf NAS |

---

## Gitea API

```bash
# Token abrufen
TOKEN=$(cd /Users/Nils/Projects/training-analyzer && git config --local gitea.token)

# API Beispiel
curl -s -H "Authorization: token $TOKEN" \
  "http://192.168.68.52:3001/api/v1/repos/NCSNASadmin/training-analyzer/issues"
```

**NIEMALS** URLs oder Owner aus Session-Summaries uebernehmen — IMMER `git remote -v` ausfuehren.

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
- [ ] Gitea Issue kommentiert und geschlossen
