# Changelog

> **Hinweis:** Das Repository wurde im Februar 2026 von Gitea (Self-Hosted) nach GitHub migriert.
> Aeltere Eintraege referenzieren Gitea Webhooks und Gitea CI — diese wurden durch GitHub Actions ersetzt.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- PostgreSQL database integration (in progress)
- SQLAlchemy models for persistence
- Alembic migrations setup

---

## [0.2.0] - 2026-02-11

### Added
- Lap classification with automatic type suggestion
- User override UI for lap types (dropdown per lap)
- Confidence scoring for lap classifications (high/medium/low)
- Dual HR zones display (Total Session + Working Laps)
- "Arbeits-Laps HF-Zonen berechnen" button
- Lap-based HR zones calculation (instead of total session)
- Training subtype-based auto-suggestions
- Confidence badges with color coding
- Empty state for Working Laps HR zones

### Changed
- HR Zones calculation now uses all laps (fixed bug using only Lap 1)
- CSV parser returns lap classification suggestions
- Upload UI restructured with better UX
- HF-Zonen boxes moved above lap table

### Fixed
- HR Zones calculation bug (was only using first lap)
- Lap classification for strength training sessions
- File casing issue (upload.tsx → Upload.tsx)

### Documentation
- Added DOMAIN_MODEL.md (15 entities, 200+ fields)
- Added IMPLEMENTATION_STATUS.md
- Updated all documentation with current status

---

## [0.1.0] - 2026-02-05

### Added
- CSV upload functionality (Running & Strength)
- CSV parsing service (backend)
- Basic session metrics (pace, HR, distance, duration)
- Lap-by-lap breakdown
- Frontend Upload UI with Drag & Drop
- Training type & subtype selection
- Docker Compose deployment
- Gitea webhook auto-deployment
- FastAPI backend
- React + TypeScript frontend
- Tailwind CSS styling

### Infrastructure
- Docker Compose setup
- Nginx reverse proxy configuration
- CI/CD Pipeline (GitHub Actions)
- Hetzner VPS Deployment via Coolify

---

## [0.0.1] - 2026-01-28

### Added
- Initial project setup
- Repository structure
- Basic documentation
- Development environment configuration

---

## Version Guidelines

### Version Format: MAJOR.MINOR.PATCH

**MAJOR** - Breaking changes
- Database schema changes requiring migration
- API endpoint changes (removed/renamed)
- Major UI redesigns

**MINOR** - New features (backward compatible)
- New endpoints
- New UI components
- New parsing features
- New analysis capabilities

**PATCH** - Bug fixes & small improvements
- Bug fixes
- Performance improvements
- Documentation updates
- Small UI tweaks

---

## Change Categories

### Added
New features, endpoints, or capabilities

### Changed
Changes to existing functionality

### Deprecated
Features that will be removed in future versions

### Removed
Features that have been removed

### Fixed
Bug fixes

### Security
Security fixes or improvements

---

## Commit Message to Changelog Mapping

```
feat(backend): Add FIT file upload endpoint
→ [MINOR] Added: FIT file upload endpoint

fix(frontend): Fix HR zones calculation
→ [PATCH] Fixed: HR zones calculation for strength training

docs(domain): Update entity diagram
→ [PATCH] Documentation updates

refactor(parser): Extract lap classification
→ [PATCH] Internal refactoring (mention if notable)

BREAKING: Remove CSV v1 parser
→ [MAJOR] Removed: Legacy CSV parser (breaking change)
```

---

## Roadmap

Die Roadmap wird ueber das [GitHub Project Board](https://github.com/orgs/NCS23/projects/1) verwaltet.
Epics (#77–#90) definieren die groesseren Initiativen, Stories sind als Sub-Issues verlinkt.
