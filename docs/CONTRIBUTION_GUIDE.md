# Contribution Guide — Training Analyzer

**Zweck:** Regelwerk fuer strukturiertes Arbeiten mit Claude AI
**Ziel:** Erstklassige Code-Qualitaet, nachvollziehbare Entscheidungen, wartbarer Code

---

## Arbeits-Philosophie

1. **Issue First** — Keine Arbeit ohne GitHub Issue
2. **Small Steps** — Lieber 5 kleine Commits als 1 grosser
3. **Test Before Deploy** — Kein Code ohne Tests
4. **Review Everything** — Auch AI-generierter Code wird geprueft
5. **Health > Features** — Code-Qualitaet vor neuen Features

---

## Backlog-Struktur

### GitHub Project Board

Das Backlog wird im [GitHub Project Board](https://github.com/orgs/NCS23/projects/1) verwaltet.

**Custom Fields:**
- **Priority:** P0-MVP, P1-High, P2-Medium, P3-Low, P4-Future
- **Type:** Epic, Story, Bug, Tech, Documentation, Figma
- **Size:** S, M, L, XL
- **Product:** Training Analyzer, Nordlig DS

### Hierarchie: Epic → Story (Sub-Issues)

```
Epic (GitHub Issue mit Label "epic")
├── Story (Sub-Issue, linked via GitHub Sub-Issues API)
│   └── Tasks (Checkboxen im Issue-Body)
├── Story
└── Story
```

Epics: #77–#90 (Training Analyzer)

### Issue erstellen

```bash
# Story erstellen
gh issue create -R NCS23/training-analyzer \
  --title "Story-Titel" \
  --label "story,P1-High" \
  --body "## Beschreibung\n..."

# Als Sub-Issue eines Epics verlinken
STORY_ID=$(gh api repos/NCS23/training-analyzer/issues/STORY_NUM --jq .id)
gh api repos/NCS23/training-analyzer/issues/EPIC_NUM/sub_issues \
  -X POST -F sub_issue_id=$STORY_ID

# Zum Project Board hinzufuegen
gh project item-add 1 --owner NCS23 --url ISSUE_URL
```

---

## Coding Standards

### Python (Backend)

- Type Hints ueberall — mypy strict muss bestehen
- Async/Await konsequent
- Pydantic Models fuer Request/Response Validation
- Spezifische Exceptions statt generisches `except`
- Logging mit `logging.getLogger(__name__)`

### TypeScript (Frontend)

- Strict TypeScript — keine `any`, keine `@ts-ignore`
- Functional Components mit TypeScript Props Interface
- `forwardRef` + `displayName` fuer wiederverwendbare Komponenten
- Named Exports (kein `export default`)
- Max. 300 Zeilen pro Datei

### Error Handling

```python
# Backend — Spezifische Exceptions
try:
    data = parse_fit(file)
except FITParseError as e:
    logger.error(f"FIT parsing failed: {e}")
    raise HTTPException(status_code=400, detail="Invalid FIT file")
```

```typescript
// Frontend — Typed Error Handling
try {
  const response = await fetch('/api/sessions');
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  const data: TrainingSession[] = await response.json();
} catch (error) {
  setError(error instanceof Error ? error.message : 'Unknown error');
}
```

---

## Git Workflow

### Branch Naming

```bash
feature/fit-import           # Neue Features
fix/hr-zones-calculation     # Bugfixes
docs/update-architecture     # Dokumentation
refactor/csv-parser          # Code-Refactoring
test/session-api             # Nur Tests
chore/update-dependencies    # Dependencies, Config
```

### Commit Messages (Conventional Commits)

```bash
feat(backend): Add FIT file upload endpoint
fix(frontend): Fix HR zones calculation for strength training
docs(domain): Update entity relationship diagram
refactor(parser): Extract lap classification to separate service
test(api): Add integration tests for session endpoints
chore(deps): Update FastAPI to 0.104.1
```

### Commit-Haeufigkeit

```
GOOD: Viele kleine Commits
  - feat(parser): Add FIT file reader
  - feat(parser): Extract running dynamics
  - test(parser): Add FIT parser tests

BAD: Ein riesiger Commit
  - feat(parser): Complete FIT implementation with tests and docs
```

---

## Testing Standards

### Test Coverage Ziele

- **Backend:** >80% (Statements + Functions)
- **Frontend:** >80% (Statements), >70% (Branches)
- **Critical Paths:** 100% (CSV/FIT Parsing, HR Zones)

### Was testen

**Backend:** CSV/FIT Parser, API Endpoints, Business Logic, DB CRUD, Fehlerbehandlung
**Frontend:** Rendering, User-Interaktionen, Bedingte Darstellung, API-Integration

---

## Quality Gates

### Vor jedem Commit

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

### Definition of Done

- [ ] Alle Akzeptanzkriterien aus dem Issue erfuellt
- [ ] Frontend: ESLint 0 Warnings, TypeScript kompiliert
- [ ] Backend: Ruff + Mypy bestehen
- [ ] Unit Tests geschrieben und gruen (Coverage >= 80%)
- [ ] UX/Design Review durchgefuehrt (DESIGN_REVIEW.md)
- [ ] Mobile-First geprueft (375px iPhone SE)
- [ ] Touch-Targets >= 44x44px
- [ ] Nordlig DS Komponenten verwendet (keine eigenen Primitives)
- [ ] CI-Pipeline gruen
- [ ] GitHub Issue kommentiert und geschlossen

---

## Wichtige Dokumente

**VOR Implementation lesen:**
1. `CLAUDE.md` — Einstiegspunkt + Workflow
2. `docs/PROJEKT_REGELN.md` — Technische Regeln
3. `docs/DESIGN_REVIEW.md` — UX & Design Checkliste
4. `docs/DOMAIN_MODEL.md` — Datenmodelle

**NACH Implementation updaten:**
1. GitHub Issue kommentieren + schliessen
2. `docs/CHANGELOG.md` (bei Releases)
