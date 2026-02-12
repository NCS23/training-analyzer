# 🤝 Contribution Guide - Training Analyzer

**Zweck:** Regelwerk für strukturiertes Arbeiten mit Claude AI  
**Ziel:** Erstklassige Code-Qualität, nachvollziehbare Entscheidungen, wartbarer Code

**Last Updated:** 2026-02-12

---

## 🎯 Arbeits-Philosophie

### Unsere Prinzipien:
1. **Dokumentation First** - Jede Entscheidung wird dokumentiert
2. **Small Steps** - Lieber 5 kleine Commits als 1 großer
3. **Test Before Deploy** - Kein Code ohne Tests
4. **Review Everything** - Auch AI-generierter Code wird geprüft
5. **Health > Features** - Code-Qualität vor neuen Features

---

## 📊 Backlog-Struktur

### Hierarchie: Epic → Story → Task

```
Epic (große Initiative, mehrere Wochen)
├── Story (User-facing Feature, 1-2 Wochen)
│   ├── Task (konkrete Implementation, 1-3 Tage)
│   ├── Task
│   └── Task
├── Story
└── Story
```

### Beispiel:

```markdown
Epic: Database Persistence
├── Story: PostgreSQL Integration
│   ├── Task: Setup PostgreSQL in Docker Compose
│   ├── Task: Create SQLAlchemy Models
│   ├── Task: Create Alembic Migrations
│   ├── Task: Implement Repository Pattern
│   └── Task: Write Integration Tests
├── Story: Session Management API
│   ├── Task: POST /sessions endpoint
│   ├── Task: GET /sessions endpoint
│   ├── Task: GET /sessions/{id} endpoint
│   └── Task: DELETE /sessions/{id} endpoint
└── Story: Frontend Session List
    ├── Task: Create SessionList component
    ├── Task: Create SessionDetail component
    └── Task: Add Loading/Error states
```

### Status Labels:
- 🆕 **NEW** - Neu, noch nicht begonnen
- 📋 **PLANNED** - Geplant, Requirements klar
- 🔄 **IN PROGRESS** - Aktiv in Bearbeitung
- 👀 **REVIEW** - Code Review ausstehend
- ✅ **DONE** - Abgeschlossen, deployed
- ❌ **BLOCKED** - Blockiert, wartet auf etwas
- 🔁 **REWORK** - Muss überarbeitet werden

### Priorität:
- 🔴 **CRITICAL** - Blocker, muss sofort
- 🟠 **HIGH** - Wichtig, nächste Woche
- 🟡 **MEDIUM** - Nice-to-have, bald
- ⚪ **LOW** - Backlog, irgendwann

---

## 📝 Documentation Standards

### Regel: **Dokumentiere BEVOR du implementierst!**

### Was dokumentieren?

#### 1. Entscheidungen (ARCHITECTURE_DECISIONS.md)
```markdown
## AD-001: 3-Zonen statt 5-Zonen HR-System

**Datum:** 2026-02-11
**Status:** Accepted
**Kontext:** HR-Zonen für Training-Analyse
**Entscheidung:** 3-Zonen System (<150, 150-160, >160 bpm)
**Alternativen:** 5-Zonen (komplexer, mehr Verwirrung)
**Konsequenzen:** 
  - ✅ Einfacher für Einstieg
  - ✅ Deckt Basics ab
  - ⚠️ Später erweiterbar zu 5-Zonen
**Rationale:** Einfachheit > Präzision für Phase 1
```

#### 2. API Changes (CHANGELOG.md)
```markdown
## [0.2.0] - 2026-02-12

### Added
- FIT file upload endpoint `/api/v1/upload/fit`
- Running Dynamics fields in TrainingLap
- Workout Structure parsing

### Changed
- CSV parser now returns `source_file_type` field
- HR Zones calculation includes confidence score

### Fixed
- Lap classification for strength training
- HR Zones calculation (was only using Lap 1)
```

#### 3. Code Kommentare
```python
# GOOD - Erklärt WARUM, nicht WAS
# Use lap-based analysis instead of total session because
# warm-up/cool-down would distort HR zone distribution
hr_zones = calculate_hr_zones(working_laps_only)

# BAD - Erklärt nur WAS der Code tut
# Calculate HR zones from laps
hr_zones = calculate_hr_zones(laps)
```

#### 4. TODOs im Code
```python
# TODO(priority:high, assignee:claude): Implement caching for AI analysis
#   - Use Redis or in-memory cache
#   - Cache key: session_id + analysis_type
#   - TTL: 24 hours
#   - Related: Issue #42

# TODO(priority:low): Extract magic numbers to constants
RECOVERY_HR_THRESHOLD = 150  # TODO: Make configurable per user
```

---

## 💻 Coding Standards

### Python (Backend)

#### File Structure
```python
"""
Module docstring - what this module does.

Example:
    from app.services.fit_parser import FITParser
    
    parser = FITParser()
    data = parser.parse_fit_file('workout.fit')
"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class FITParser:
    """Parse FIT files and extract training data.
    
    Attributes:
        strict_mode: If True, raise errors on missing fields.
                    If False, use None for missing fields.
    """
    
    def __init__(self, strict_mode: bool = False):
        self.strict_mode = strict_mode
    
    def parse_fit_file(self, file_path: Path) -> Dict:
        """Parse FIT file and extract session data.
        
        Args:
            file_path: Path to .fit file
            
        Returns:
            Dict with keys: session, laps, records
            
        Raises:
            FITParseError: If file is invalid or corrupted
            
        Example:
            >>> parser = FITParser()
            >>> data = parser.parse_fit_file('workout.fit')
            >>> print(data['session']['sport'])
            'running'
        """
        try:
            # Implementation
            pass
        except Exception as e:
            logger.error(f"FIT parsing failed: {e}")
            raise FITParseError(f"Could not parse {file_path}") from e
```

#### Type Hints - IMMER!
```python
# GOOD
def calculate_pace(distance_km: float, duration_sec: int) -> float:
    """Calculate pace in min/km."""
    return (duration_sec / 60) / distance_km

# BAD - Keine Type Hints
def calculate_pace(distance, duration):
    return (duration / 60) / distance
```

#### Error Handling
```python
# GOOD - Spezifische Exceptions
try:
    data = parse_fit(file)
except FITParseError as e:
    logger.error(f"FIT parsing failed: {e}")
    raise HTTPException(status_code=400, detail="Invalid FIT file")
except Exception as e:
    logger.exception("Unexpected error during FIT parsing")
    raise HTTPException(status_code=500, detail="Internal server error")

# BAD - Generisches except
try:
    data = parse_fit(file)
except:
    raise HTTPException(status_code=500)
```

#### Logging
```python
import logging

logger = logging.getLogger(__name__)

# Levels:
logger.debug("Detailed debug info")      # Development only
logger.info("Normal operation")          # Key events
logger.warning("Something unexpected")   # Recoverable issues
logger.error("Operation failed")         # Errors
logger.exception("Caught exception")     # Errors with stack trace
```

### TypeScript (Frontend)

#### Component Structure
```typescript
/**
 * SessionList component displays all training sessions.
 * 
 * @example
 * <SessionList 
 *   sessions={sessions}
 *   onSessionClick={handleClick}
 * />
 */

import React, { useState, useEffect } from 'react';

interface SessionListProps {
  /** Array of training sessions to display */
  sessions: TrainingSession[];
  /** Callback when session is clicked */
  onSessionClick?: (session: TrainingSession) => void;
  /** Optional filter by training type */
  filterType?: TrainingType;
}

export const SessionList: React.FC<SessionListProps> = ({ 
  sessions, 
  onSessionClick,
  filterType 
}) => {
  const [loading, setLoading] = useState(false);
  
  // Implementation
  
  return (
    <div className="session-list">
      {/* Component JSX */}
    </div>
  );
};
```

#### Type Safety
```typescript
// GOOD - Explicit types
interface TrainingSession {
  id: string;
  date: string;
  trainingType: 'running' | 'strength';
  duration: number;
}

const sessions: TrainingSession[] = [];

// BAD - any types
const sessions: any[] = [];
```

#### Error Handling
```typescript
// GOOD - Typed error handling
try {
  const response = await fetch('/api/sessions');
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }
  const data: TrainingSession[] = await response.json();
  setSessions(data);
} catch (error) {
  console.error('Failed to fetch sessions:', error);
  setError(error instanceof Error ? error.message : 'Unknown error');
}

// BAD - Silent failures
fetch('/api/sessions')
  .then(r => r.json())
  .then(setSessions);
```

---

## 🧪 Testing Standards

### Regel: **Kein Code ohne Tests!**

### Test Coverage Ziele:
- **Backend:** >80% coverage
- **Frontend:** >70% coverage
- **Critical Paths:** 100% coverage (CSV/FIT parsing, HR zones, etc.)

### Test Struktur

#### Unit Tests (Backend)
```python
# tests/unit/test_fit_parser.py

import pytest
from app.services.fit_parser import FITParser, FITParseError


class TestFITParser:
    """Unit tests for FIT file parsing."""
    
    @pytest.fixture
    def parser(self):
        """Create parser instance for tests."""
        return FITParser(strict_mode=False)
    
    def test_parse_valid_fit_file(self, parser):
        """Should successfully parse valid FIT file."""
        # Arrange
        file_path = Path('tests/fixtures/valid_workout.fit')
        
        # Act
        result = parser.parse_fit_file(file_path)
        
        # Assert
        assert result['session']['sport'] == 'running'
        assert len(result['laps']) > 0
        assert result['laps'][0]['avg_heart_rate'] > 0
    
    def test_parse_invalid_file_raises_error(self, parser):
        """Should raise FITParseError for invalid file."""
        # Arrange
        file_path = Path('tests/fixtures/corrupted.fit')
        
        # Act & Assert
        with pytest.raises(FITParseError):
            parser.parse_fit_file(file_path)
    
    @pytest.mark.parametrize("field,expected", [
        ('avg_cadence', 76),
        ('avg_heart_rate', 165),
        ('total_distance', 5000),
    ])
    def test_extract_lap_fields(self, parser, field, expected):
        """Should correctly extract lap fields."""
        # Arrange
        file_path = Path('tests/fixtures/interval_workout.fit')
        
        # Act
        result = parser.parse_fit_file(file_path)
        
        # Assert
        assert result['laps'][0][field] == expected
```

#### Integration Tests (Backend)
```python
# tests/integration/test_session_api.py

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestSessionAPI:
    """Integration tests for session endpoints."""
    
    async def test_upload_csv_creates_session(self, client: AsyncClient, db):
        """Should create session from CSV upload."""
        # Arrange
        csv_content = open('tests/fixtures/workout.csv', 'rb')
        
        # Act
        response = await client.post(
            '/api/v1/sessions/upload',
            files={'file': ('workout.csv', csv_content, 'text/csv')}
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert 'id' in data
        assert data['training_type'] == 'running'
        
        # Verify DB
        session = await db.get(TrainingSession, data['id'])
        assert session is not None
```

#### Component Tests (Frontend)
```typescript
// components/SessionList/SessionList.test.tsx

import { render, screen, fireEvent } from '@testing-library/react';
import { SessionList } from './SessionList';

describe('SessionList', () => {
  const mockSessions = [
    { id: '1', date: '2026-02-12', trainingType: 'running' },
    { id: '2', date: '2026-02-11', trainingType: 'strength' },
  ];
  
  it('renders all sessions', () => {
    render(<SessionList sessions={mockSessions} />);
    
    expect(screen.getByText(/2026-02-12/)).toBeInTheDocument();
    expect(screen.getByText(/2026-02-11/)).toBeInTheDocument();
  });
  
  it('calls onSessionClick when session is clicked', () => {
    const handleClick = jest.fn();
    render(
      <SessionList 
        sessions={mockSessions} 
        onSessionClick={handleClick}
      />
    );
    
    fireEvent.click(screen.getByText(/2026-02-12/));
    expect(handleClick).toHaveBeenCalledWith(mockSessions[0]);
  });
  
  it('filters by training type', () => {
    render(
      <SessionList 
        sessions={mockSessions} 
        filterType="running"
      />
    );
    
    expect(screen.getByText(/2026-02-12/)).toBeInTheDocument();
    expect(screen.queryByText(/2026-02-11/)).not.toBeInTheDocument();
  });
});
```

---

## 🔄 Git Workflow

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
# Format: <type>(<scope>): <subject>

feat(backend): Add FIT file upload endpoint
fix(frontend): Fix HR zones calculation for strength training
docs(domain): Update entity relationship diagram
refactor(parser): Extract lap classification to separate service
test(api): Add integration tests for session endpoints
chore(deps): Update FastAPI to 0.104.1
```

**Types:**
- `feat:` Neues Feature
- `fix:` Bugfix
- `docs:` Dokumentation
- `refactor:` Code-Refactoring (keine Funktionsänderung)
- `test:` Tests hinzufügen/ändern
- `chore:` Build, Dependencies, Config
- `perf:` Performance-Verbesserung

### Commit-Häufigkeit
```
✅ GOOD: Viele kleine Commits
  - feat(parser): Add FIT file reader
  - feat(parser): Extract running dynamics
  - feat(parser): Add workout structure parsing
  - test(parser): Add FIT parser tests
  
❌ BAD: Ein riesiger Commit
  - feat(parser): Complete FIT implementation with tests and docs
```

### Pull Request Template
```markdown
## Description
Kurze Beschreibung was geändert wurde und warum.

## Type of Change
- [ ] Bugfix
- [ ] New Feature
- [ ] Breaking Change
- [ ] Documentation Update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manually tested locally
- [ ] Tested on NAS deployment

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Commented hard-to-understand areas
- [ ] Updated documentation
- [ ] No new warnings
- [ ] Tests pass locally
- [ ] Added relevant labels

## Related Issues
Closes #123
Related to #456
```

---

## 👀 Code Review Process

### Vor dem Review (Author):
- [ ] Code selbst reviewen
- [ ] Tests geschrieben & passing
- [ ] Dokumentation aktualisiert
- [ ] Lint/Format checks passed
- [ ] Lokal getestet

### Während Review (Reviewer):
- [ ] Code verständlich?
- [ ] Tests ausreichend?
- [ ] Edge Cases beachtet?
- [ ] Performance OK?
- [ ] Security Aspekte OK?
- [ ] Dokumentation aktuell?

### Review-Kommentare:
```
🔴 CRITICAL: Muss gefixt werden
🟠 SUGGESTION: Sollte geändert werden
💡 IDEA: Optional, zur Diskussion
❓ QUESTION: Frage zum Code
✅ LGTM: Looks good to me
```

---

## 📦 Deployment Checklist

### Vor Deployment:
- [ ] Alle Tests passing (Backend + Frontend)
- [ ] Code Review abgeschlossen
- [ ] CHANGELOG.md aktualisiert
- [ ] DB Migrations getestet (falls vorhanden)
- [ ] Environment Variables dokumentiert
- [ ] Breaking Changes kommuniziert

### Deployment Steps:
```bash
# 1. Final Tests
pytest
npm test

# 2. Build
docker-compose build

# 3. Backup (wenn DB changes)
docker-compose exec postgres pg_dump > backup.sql

# 4. Deploy
git push origin main  # Webhook triggers deployment

# 5. Verify
curl http://192.168.68.52/health
docker-compose logs -f

# 6. Monitor
# Check logs for errors
# Test critical paths manually
```

### Nach Deployment:
- [ ] Health Check passed
- [ ] Critical Paths getestet
- [ ] Logs sauber (keine Errors)
- [ ] Performance OK
- [ ] Rollback-Plan bereit

---

## 🚨 Incident Response

### Bei Production Issues:

1. **STOP** - Keine Panik
2. **ASSESS** - Was ist kaputt?
3. **ROLLBACK** - Falls kritisch, sofort zurückrollen
4. **FIX** - Root Cause finden
5. **TEST** - Fix testen
6. **DEPLOY** - Neues Deployment
7. **DOCUMENT** - Post-Mortem schreiben

### Rollback:
```bash
# Check previous version
git log --oneline

# Revert to previous commit
git revert HEAD
git push origin main

# Or force rollback
git reset --hard <previous-commit>
git push --force origin main
```

---

## 📚 Documentation Maintenance

### Pflicht-Updates nach jeder Session:
- [ ] IMPLEMENTATION_STATUS.md (Was ist neu done?)
- [ ] CHANGELOG.md (Was hat sich geändert?)
- [ ] BACKLOG.md (Tasks aktualisieren)

### Regelmäßige Reviews:
- **Wöchentlich:** BACKLOG.md priorisieren
- **Monatlich:** Architecture Decisions reviewen
- **Quartalsweise:** Domain Model aktualisieren

---

## ✅ Quality Gates

### Keine Merge ohne:
- ✅ Alle Tests passing
- ✅ Code Review approval
- ✅ Dokumentation aktualisiert
- ✅ Lint checks passed
- ✅ No regressions

### Deployment blockers:
- 🔴 Critical bugs
- 🔴 Failing tests
- 🔴 Security issues
- 🔴 Breaking changes (ohne Communication)

---

## 🎯 Success Metrics

### Code Quality:
- Test Coverage >80% (Backend), >70% (Frontend)
- Linter Warnings: 0
- Deployment Success Rate >95%
- Rollback Rate <5%

### Process Quality:
- Dokumentation aktuell (<1 Woche alt)
- PRs reviewed within 24h
- Issues triaged within 48h
- Incidents documented within 24h

---

## 📖 Wichtige Dokumente

**IMMER lesen vor Implementation:**
1. `CONTEXT.md` - Projekt-Überblick
2. `IMPLEMENTATION_STATUS.md` - Aktueller Stand
3. `DOMAIN_MODEL.md` - Datenmodelle
4. Feature-spezifische Docs (z.B. FIT_IMPORT_NOTES.md)

**IMMER updaten nach Implementation:**
1. `IMPLEMENTATION_STATUS.md`
2. `CHANGELOG.md`
3. `BACKLOG.md`

---

## 💡 Best Practices

### DO:
✅ Kleine, fokussierte Commits  
✅ Tests schreiben BEVOR Code  
✅ Dokumentation parallel zum Code  
✅ Code selbst reviewen  
✅ Edge Cases bedenken  
✅ Errors richtig loggen  
✅ Type hints verwenden  
✅ Sprechende Variablennamen  

### DON'T:
❌ Riesige Commits mit vielen Changes  
❌ Code ohne Tests  
❌ TODO Comments ohne Kontext  
❌ Magic Numbers ohne Kommentar  
❌ Silent Failures (try/except ohne Logging)  
❌ `any` Types in TypeScript  
❌ Commented-out Code committen  
❌ Secrets in Git  

---

**Dieses Dokument ist lebend - bei neuen Erkenntnissen updaten!** 📝
