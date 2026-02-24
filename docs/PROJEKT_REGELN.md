# Projektregeln — Training Analyzer

Dieses Dokument definiert die verbindlichen technischen Regeln fuer die Entwicklung.
Jede Abweichung muss begruendet und dokumentiert werden.

---

## 1. Mobile-First & Responsive Design

### Grundsatz

**Mobile-First ist PFLICHT.** Die App wird primaer auf iPhones genutzt.
Jedes UI-Element wird zuerst fuer den kleinsten Viewport designt und implementiert.

### Breakpoints

```
Default (kein Prefix):  375px — iPhone SE / iPhone Mini (BASE)
sm:                     640px — Groessere Phones im Landscape
md:                     768px — Tablets
lg:                    1024px — Desktop
xl:                    1280px — Grosse Desktops
```

### Regeln

1. **CSS/Tailwind: Immer Mobile-Basis + `min-width` Erweiterungen**
   ```tsx
   // ✅ RICHTIG — Mobile-First
   <div className="flex flex-col gap-4 md:flex-row md:gap-6">

   // ❌ FALSCH — Desktop-First
   <div className="flex flex-row gap-6 max-md:flex-col max-md:gap-4">
   ```

2. **Touch-Targets: Minimum 44×44px** (Apple HIG)
   ```tsx
   // ✅ Buttons, Links, interaktive Elemente
   className="min-h-[44px] min-w-[44px]"
   ```

3. **Kein Hover-Only Content** — Alles was auf Hover sichtbar wird,
   muss auch per Touch/Tap erreichbar sein

4. **Scrollverhalten:** Natuerliches vertikales Scrollen bevorzugen.
   Horizontales Scrollen nur fuer Tabellen oder Karussells.

5. **Formulare:** Eingabefelder muessen auf iPhone bequem bedienbar sein.
   Labels ueber den Feldern (nicht daneben). Input-Type korrekt setzen
   (`type="email"`, `type="tel"`, `inputMode="numeric"`).

6. **Viewport-Test:** Jedes Feature MUSS auf 375px (iPhone SE) geprueft werden.

---

## 2. Nordlig Design System Integration

### Grundsatz

Die App verwendet das **Nordlig Design System** fuer alle UI-Komponenten.
Eigene Primitives (Button, Input, Card, etc.) sind VERBOTEN.

### Verfuegbare Komponenten

Import aus `@nordlig/components`:
- **Atoms:** Button, Input, Label, Text, Heading, Badge, Kbd, Link, Separator, Spinner, Tag, Toggle
- **Molecules:** InputField, Select, Textarea, DatePicker, CheckboxField, FileUpload, PasswordInput, ToggleGroup, Alert
- **Organisms:** DataTable, Card (CardHeader, CardBody, CardFooter)
- **Layout:** Container

### Token-Nutzung

Alle visuellen Werte MUESSEN ueber CSS Custom Properties (Tokens) gesetzt werden:

```tsx
// ✅ RICHTIG
className="bg-[var(--color-bg-base)] text-[var(--color-text-base)] rounded-[var(--radius-component-md)]"

// ❌ VERBOTEN
className="bg-white text-gray-900 rounded-md"
```

**Ausnahmen (erlaubt):**
- Tailwind Utility-Klassen fuer Layout: `flex`, `grid`, `gap-4`, `w-full`, `p-4`
- Tailwind fuer Spacing wo kein semantischer Token existiert: `mt-2`, `mb-4`
- Explizite Groessen: `h-[44px]`, `max-w-[600px]`

### Farb-Tokens fuer Training-spezifische Konzepte

Definiert in `tailwind.config.js`:
```
workout.quality:   #8b5cf6  (Lila — Intervalle, Tempo)
workout.recovery:  #10b981  (Gruen — Erholung)
workout.longrun:   #3b82f6  (Blau — Longrun)
workout.strength:  #f97316  (Orange — Krafttraining)

hr.zone1:          #10b981  (Gruen — <150 bpm)
hr.zone2:          #f59e0b  (Gelb — 150-160 bpm)
hr.zone3:          #ef4444  (Rot — >160 bpm)
```

---

## 3. Frontend-Architektur

### Ordnerstruktur

```
frontend/src/
├── layouts/           # App Layout (Sidebar, TopBar)
├── pages/             # Route-Komponenten (1:1 mit Routing)
│   ├── dashboard/
│   ├── sessions/
│   ├── plan/
│   ├── goals/
│   ├── analytics/
│   └── settings/
├── features/          # Feature-spezifische Komponenten
│   ├── sessions/      # SessionCard, LapTable, HRZoneChart, etc.
│   ├── maps/          # RouteMap, ElevationProfile, HeatMap
│   ├── strength/      # ExerciseForm, ProgressionChart
│   └── dashboard/     # WeekSummary, QuickInsights
├── api/               # API Client (Fetch/Axios Wrapper)
├── stores/            # Zustand Stores
├── hooks/             # Shared React Hooks
├── types/             # Shared TypeScript Types (aus Domain Model)
└── utils/             # Pure Utility Functions
```

### State Management

| State-Typ | Loesung | Beispiel |
|-----------|---------|----------|
| Server-State | React Query (`@tanstack/react-query`) | Sessions, Plans, Goals |
| Client-UI-State | Zustand | Sidebar offen/zu, aktive Filter |
| Form-State | React Hook Form oder lokaler State | Upload-Formular |
| URL-State | React Router Search Params | Filter, Pagination |

### Routing

React Router v6 mit Lazy Loading:

```tsx
// Alle Routes unter AppLayout (Sidebar + TopBar)
<Route element={<AppLayout />}>
  <Route path="/dashboard" element={<Dashboard />} />
  <Route path="/sessions" element={<SessionList />} />
  <Route path="/sessions/:id" element={<SessionDetail />} />
  <Route path="/sessions/new" element={<SessionNew />} />
  <Route path="/plan" element={<Plan />} />
  <Route path="/goals" element={<Goals />} />
  <Route path="/analytics" element={<Analytics />} />
  <Route path="/settings" element={<Settings />} />
</Route>
```

### Komponenten-Regeln

1. **Functional Components** mit TypeScript Props Interface
2. **forwardRef** fuer wiederverwendbare Komponenten
3. **Named Exports** (kein `export default`)
4. **Co-Location:** Test + Komponente im gleichen Verzeichnis
5. **Max. 300 Zeilen** pro Datei — bei Ueberschreitung aufteilen

---

## 4. Backend-Architektur

### Clean Architecture (Schichten)

```
backend/app/
├── api/v1/            # API-Schicht: Routes, Request/Response Handling
├── services/          # Application-Schicht: Business Logic, Use Cases
├── domain/            # Domain-Schicht: Entities, Interfaces, Value Objects
│   ├── entities/
│   └── interfaces/
├── infrastructure/    # Infrastruktur: DB, AI, externe APIs
│   ├── database/
│   ├── ai/
│   └── external/
├── models/            # Pydantic Schemas (Request/Response Models)
├── core/              # Configuration, Dependencies
└── tests/             # Tests (spiegeln Quellstruktur)
```

### Abhaengigkeitsrichtung

```
API → Services → Domain ← Infrastructure
```

Domain hat KEINE Abhaengigkeiten nach aussen. Infrastructure implementiert Domain-Interfaces.

### API-Design Regeln

1. **RESTful Konventionen:**
   - `GET /api/v1/sessions` — Liste
   - `GET /api/v1/sessions/{id}` — Einzeln
   - `POST /api/v1/sessions` — Erstellen
   - `PUT /api/v1/sessions/{id}` — Aktualisieren
   - `DELETE /api/v1/sessions/{id}` — Loeschen

2. **Pydantic Models fuer ALLES:**
   ```python
   # ✅ RICHTIG
   @router.post("/sessions", response_model=TrainingSessionResponse)
   async def create_session(data: TrainingSessionCreate, db: AsyncSession = Depends(get_db)):

   # ❌ VERBOTEN
   @router.post("/sessions")
   async def create_session(data: dict):
   ```

3. **Fehlerbehandlung:**
   ```python
   raise HTTPException(status_code=404, detail="Session nicht gefunden")
   ```

4. **Pagination:**
   ```python
   @router.get("/sessions")
   async def list_sessions(skip: int = 0, limit: int = 20):
   ```

### Datenbank-Regeln

1. **Async SQLAlchemy** — Alle DB-Operationen async
2. **Alembic Migrations** — Schema-Aenderungen IMMER als Migration
3. **JSONB** fuer flexible Felder (weather, timeseries, etc.)
4. **UUID** als Primary Key fuer alle neuen Tabellen
5. **Timestamps** auf allen Tabellen (`created_at`, `updated_at`)

---

## 5. Testing

### Frontend (Vitest + Testing Library)

**Coverage-Schwellenwerte (CI-enforced):**
- Statements: 80%
- Branches: 70%
- Functions: 80%
- Lines: 80%

**Was testen:**
- Rendering mit korrekten Props
- User-Interaktionen (Click, Input, Submit)
- Bedingte Darstellung (Loading, Error, Empty State)
- API-Integration (Mock mit MSW oder vi.mock)
- Responsive Verhalten (Viewport-abhaengige Logik)

**Test-Namenskonvention:**
```
ComponentName.test.tsx   — neben der Komponente
hookName.test.ts         — neben dem Hook
```

**Beispiel:**
```tsx
describe('SessionCard', () => {
  it('zeigt ActivityType Badge', () => {
    render(<SessionCard session={mockRunningSession} />);
    expect(screen.getByText('Laufen')).toBeInTheDocument();
  });

  it('zeigt Kraft-spezifische Metriken fuer Strength Sessions', () => {
    render(<SessionCard session={mockStrengthSession} />);
    expect(screen.getByText('Tonnage')).toBeInTheDocument();
  });
});
```

### Backend (Pytest)

**Coverage-Schwellenwerte (CI-enforced):**
- Statements: 80%
- Functions: 80%

**Test-Kategorien (Marker):**
- `@pytest.mark.unit` — Isolierte Logik (Parser, Berechnungen)
- `@pytest.mark.integration` — DB-Operationen, API-Endpoints
- `@pytest.mark.e2e` — Komplette Flows (Upload → Parse → Save → Query)
- `@pytest.mark.slow` — Tests >5s (separat ausfuehrbar)

**Was testen:**
- CSV/FIT Parser mit echten und synthetischen Dateien
- API-Endpoints (Request/Response Validation)
- Business Logic (HR-Zonen Berechnung, Lap-Klassifizierung)
- DB CRUD Operationen
- Fehlerbehandlung (invalide Dateien, fehlende Felder)

**Beispiel:**
```python
@pytest.mark.unit
def test_hr_zone_karvonen():
    zones = calculate_hr_zones(resting_hr=50, max_hr=190, method="karvonen")
    assert zones[0].hr_max == 150  # Zone 1 obere Grenze
    assert zones[2].hr_min == 160  # Zone 3 untere Grenze
```

---

## 6. Code Quality Tools

### Frontend

| Tool | Zweck | Command |
|------|-------|---------|
| ESLint | Linting + Accessibility | `npx eslint src/ --max-warnings 0` |
| Prettier | Formatierung | `npx prettier --check "src/**/*.{ts,tsx}"` |
| TypeScript | Type Safety | `npx tsc --noEmit` |
| Vitest | Tests + Coverage | `npx vitest --run` |

### Backend

| Tool | Zweck | Command |
|------|-------|---------|
| Ruff | Linting + Formatting | `ruff check app/` |
| Mypy | Type Safety (strict) | `mypy app/` |
| Black | Formatierung | `black --check app/` |
| Pytest | Tests + Coverage | `pytest app/tests/ --cov=app --cov-fail-under=80` |

---

## 7. Commit-Konventionen

### Format

```
type(scope): kurze Beschreibung

- Detail 1
- Detail 2

Closes #123
```

### Types

- `feat` — Neues Feature
- `fix` — Bugfix
- `refactor` — Code-Umbau ohne Verhaltensaenderung
- `test` — Tests hinzufuegen/aendern
- `docs` — Dokumentation
- `chore` — Build, CI, Dependencies
- `style` — Formatierung (kein Code-Change)

### Scope

- `fe` — Frontend
- `be` — Backend
- `ci` — CI/CD
- `docs` — Dokumentation

**Beispiele:**
```
feat(fe): Session Detail View mit adaptivem Layout
fix(be): HR-Zonen Berechnung fuer Karvonen-Methode
test(be): CSV Parser Unit Tests fuer Apple Watch Format
chore(ci): Coverage-Schwellenwerte in CI Pipeline
```

---

## 8. Informationsarchitektur

### Session-zentrisch

Alles ist eine `TrainingSession` mit unterschiedlichem `activity_type`.
Es gibt KEINE separaten Bereiche fuer verschiedene Sportarten.

### Navigation (Sidebar)

```
📊 Dashboard        /dashboard
🏋️ Sessions         /sessions
📅 Plan             /plan           [ab P1]
🎯 Ziele            /goals          [ab P1]
📈 Analyse          /analytics      [ab P2]
⚙️ Einstellungen    /settings
```

### Mobile Navigation

Auf Viewports < 768px:
- Sidebar wird zu Bottom Navigation Bar (5 Icons max)
- Aktive Seite hervorgehoben
- Touch-Targets 44×44px

---

## 9. Abhaengigkeiten zum Nordlig Design System

### Installierte Pakete

```
@nordlig/components  — React-Komponenten
@nordlig/styles      — CSS mit Token-basierten Styles
@nordlig/tokens      — Design Tokens (CSS Custom Properties)
```

### Update-Prozess

1. Neue `.tgz` Dateien in `frontend/packages/` ablegen
2. `npm install ./packages/nordlig-*.tgz`
3. Pruefen ob Breaking Changes vorliegen
4. Anpassen und testen
