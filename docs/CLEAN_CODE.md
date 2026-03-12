# Clean Code & SOLID — Projektregeln

> Referenz für alle Entwickler (Mensch und KI). Basierend auf Robert C. Martin.

---

## SOLID-Prinzipien

### Single Responsibility (SRP)

**Eine Klasse/Funktion/Komponente hat genau einen Grund, sich zu ändern.**

Projektbeispiele:
- `csv_parser.py` — nur CSV-Parsing, keine Validierung oder DB-Logik
- `training_type_classifier.py` — nur Klassifizierung, kein Datenbankzugriff
- Jede React-Komponente rendert eine Sache, Business-Logik in Custom Hooks

Verstöße (werden in E16 behoben):
- `SessionDetail.tsx` (1656 Zeilen) — Daten laden, rendern, editieren, Karte, Notes, Laps
- `DayCard.tsx` (1344 Zeilen) — Card-Rendering + 2 Dialoge + Utilities

### Open/Closed (OCP)

**Offen für Erweiterung, geschlossen für Modifikation.**

Projektbeispiele:
- `TrainingParser` Interface — neuer Parser (FIT, TCX) ohne bestehenden Code zu ändern
- AI Provider Strategy — Claude, OpenAI, Ollama über gemeinsames Interface
- Segment-Type-System — neue Types über `taxonomy.py` ohne Classifier-Änderung

### Liskov Substitution (LSP)

**Subtypen müssen ihre Basistypen ersetzen können.**

Projektbeispiele:
- Alle `TrainingParser`-Implementierungen liefern dasselbe `ParsedWorkout`-Format
- AI Provider liefern alle `AnalysisResult` unabhängig vom Backend

### Interface Segregation (ISP)

**Viele spezifische Interfaces statt eines großen.**

Projektbeispiele:
- API-Routers aufgeteilt: `sessions.py`, `training_plans.py`, `weekly_plan.py`
- Frontend API-Layer: `sessionsApi.ts`, `plansApi.ts`, `goalsApi.ts`

### Dependency Inversion (DIP)

**Abhängigkeit von Abstraktionen, nicht von Implementierungen.**

Projektbeispiele:
- Endpoints hängen von `TrainingParser` ab, nicht von `CSVParser`
- AI Service hängt von Provider-Interface ab, nicht von `AnthropicClient`
- React Query als Abstraktion über HTTP-Calls

---

## Clean Code Grenzwerte

| Metrik | Zielwert | Hartes Maximum | Durchgesetzt durch |
|--------|----------|----------------|--------------------|
| Funktionslänge | < 40 Zeilen | < 80 Zeilen | ESLint `max-lines-per-function`, Ruff `PLR0915` |
| Komponenten-Länge | < 300 Zeilen | < 500 Zeilen | Code Review |
| Cyclomatic Complexity | < 10 | < 15 | ESLint `complexity`, Ruff `C901` |
| Parameter pro Funktion | < 4 | < 6 | ESLint `max-params`, Ruff `PLR0913` |
| Verschachtelungstiefe | < 3 | < 4 | ESLint `max-depth` |
| useState pro Komponente | < 5 | < 8 | Code Review |
| Branches (if/elif/else) | < 8 | < 12 | Ruff `PLR0912` |
| Return Statements | < 4 | < 6 | Ruff `PLR0911` |

**Aktuell gelten die harten Maxima als warn-Level.** Nach Abschluss der E16-Stories (B1-B2, F1-F4) werden die Zielwerte als error-Level aktiviert.

---

## Clean Code Regeln

### 1. Kleine Funktionen

```python
# Schlecht: 100+ Zeilen mit mehreren Verantwortlichkeiten
def upload_csv(file, date, type, subtype, notes, rpe, overrides, type_override, planned_id, db):
    # Validierung, Parsing, Mapping, DB-Speicherung — alles in einer Funktion
    ...

# Gut: Kleine Funktionen mit einer Aufgabe
async def upload_csv(file: UploadFile, form: SessionUploadForm, db: AsyncSession):
    content = await validate_upload_file(file, ".csv")
    return await process_upload(content, csv_parser, form, db)
```

### 2. Aussagekräftige Namen

```typescript
// Schlecht
const d = new Date();
const arr = sessions.filter(s => s.t === "interval");
function calc(a: number, b: number) { ... }

// Gut
const trainingDate = new Date();
const intervalSessions = sessions.filter(s => s.type === "interval");
function calculateWeeklyVolume(distanceKm: number, durationMin: number) { ... }
```

### 3. DRY — Don't Repeat Yourself

```typescript
// Schlecht: Konstanten in 3 Dateien dupliziert
// DayCard.tsx
const RUN_TYPE_LABELS = { easy: "Lockerer Lauf", ... };
// TemplatePickerDialog.tsx
const RUN_TYPE_LABELS = { easy: "Lockerer Lauf", ... };

// Gut: Eine Quelle der Wahrheit
// constants/plan.ts
export const RUN_TYPE_LABELS = { easy: "Lockerer Lauf", ... } as const;
```

### 4. Keine Magic Values

```python
# Schlecht
if heart_rate > 180:
    return "too_high"
if pace < 3.5:
    return "sprint"

# Gut
MAX_HEART_RATE = 180
SPRINT_PACE_THRESHOLD = 3.5

if heart_rate > MAX_HEART_RATE:
    return "too_high"
if pace < SPRINT_PACE_THRESHOLD:
    return "sprint"
```

### 5. God-Components aufbrechen

```typescript
// Schlecht: 1600 Zeilen, 24 useState, 4 useEffect
function SessionDetail() {
  const [session, setSession] = useState(null);
  const [gpsData, setGpsData] = useState(null);
  const [notes, setNotes] = useState("");
  // ... 21 weitere useState

  useEffect(() => { /* Daten laden */ }, []);
  useEffect(() => { /* Notes auto-save */ }, [notes]);
  // ... 2 weitere useEffect

  return (/* 500 Zeilen JSX */);
}

// Gut: Custom Hooks + Sub-Components
function SessionDetail() {
  const { session, gpsData, isLoading } = useSessionData(id);
  const { notes, updateNotes } = useSessionNotes(id);
  const { editState, handlers } = useSessionEditing(session);

  if (isLoading) return <LoadingSkeleton />;

  return (
    <SessionHeader session={session} />
    <SessionMapSection gpsData={gpsData} />
    <SessionLapsSection laps={session.laps} />
    <SessionNotesSection notes={notes} onChange={updateNotes} />
  );
}
```

### 6. Parameter-Objekte statt langer Parameterlisten

```python
# Schlecht: 10 Parameter
@router.post("/upload/csv")
async def upload_csv(
    csv_file: UploadFile,
    training_date: date = Form(...),
    training_type: str = Form(...),
    training_subtype: str | None = Form(None),
    notes: str | None = Form(None),
    rpe: int | None = Form(None),
    lap_overrides_json: str | None = Form(None),
    training_type_override: str | None = Form(None),
    planned_entry_id: int | None = Form(None),
    db: AsyncSession = Depends(get_db),
): ...

# Gut: Parameter-Objekt
@router.post("/upload/csv")
async def upload_csv(
    csv_file: UploadFile,
    form: SessionUploadForm = Depends(),
    db: AsyncSession = Depends(get_db),
): ...
```

---

## Self-Review Checkliste

Vor jedem Commit prüfen:

### Funktionen
- [ ] Keine Funktion > 80 Zeilen?
- [ ] Jede Funktion hat genau eine Aufgabe?
- [ ] Max 5 Parameter (sonst Parameter-Objekt)?
- [ ] Complexity < 10 (wenige if/elif/else)?
- [ ] Aussagekräftige Funktionsnamen?

### Komponenten (Frontend)
- [ ] Keine Komponente > 500 Zeilen?
- [ ] Max 8 useState (sonst useReducer/Custom Hook)?
- [ ] Business-Logik in Custom Hooks, nicht in Komponenten?
- [ ] Keine inline definierten Sub-Components > 30 Zeilen?

### Duplikation
- [ ] Keine kopierten Konstanten (DRY)?
- [ ] Keine kopierten Logik-Blöcke?
- [ ] Gemeinsame Patterns extrahiert?

### Types & Unterdrückung
- [ ] Keine neuen `# type: ignore` ohne Begründung?
- [ ] Keine neuen `// eslint-disable` ohne Begründung?
- [ ] Keine neuen `# noqa` ohne Begründung?

---

## Linter-Konfiguration

### ESLint (Frontend)

Aktive Clean Code Regeln in `frontend/eslint.config.js`:
```js
complexity: ["warn", { max: 15 }],           // Ziel: 10
"max-depth": ["warn", { max: 4 }],           // Ziel: 3
"max-params": ["warn", { max: 5 }],          // Ziel: 4
"max-lines-per-function": ["warn", { max: 100 }],  // Ziel: 80
```

### Ruff (Backend)

Aktive Clean Code Regeln in `backend/pyproject.toml`:
```toml
[tool.ruff.lint]
select = ["C90", "PLR"]  # mccabe + pylint refactor

[tool.ruff.lint.mccabe]
max-complexity = 15       # Ziel: 10

[tool.ruff.lint.pylint]
max-args = 8              # Ziel: 6
max-branches = 12         # Ziel: 10
max-returns = 6           # Ziel: 4
max-statements = 50       # Ziel: 40
```

---

## Refactoring-Roadmap (Epic E16)

| Phase | Stories | Beschreibung |
|-------|---------|--------------|
| 1 (Done) | W1, W2 | Linter-Regeln + Dokumentation |
| 2 | F3, B4 | Konstanten konsolidieren, Parameter-Objekte |
| 3 | B1, B2 | Backend Upload-Duplikation, Classifier |
| 4 | F1, F2 | SessionDetail + DayCard aufbrechen |
| 5 | B3, F4 | type:ignore beseitigen, restliche Komponenten |
| 6 | — | Thresholds auf Zielwerte verschärfen |
