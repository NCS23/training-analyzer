# Workflow Checklist — Issue #159

## Phase 0: Pre-Code
- [x] GitHub Issue gelesen (Akzeptanzkriterien + Taskbreakdown)
- [x] PROJEKT_REGELN.md gelesen
- [x] DESIGN_REVIEW.md gelesen (bei UI-Aenderungen)
- [x] DOMAIN_MODEL.md gelesen (bei Datenmodell-Aenderungen)

## Phase 1: Branch & Board
- [x] Feature-Branch erstellt (kein main!)
- [x] Issue auf "In Progress" im Project Board gesetzt

## Phase 2: Implementation
- [x] Vite manualChunks konfiguriert (vendor-react + vendor-ui Split)
- [x] rollup-plugin-visualizer als devDependency installiert

## Phase 3: Quality Gates
- [x] ESLint 0 Warnings
- [x] Prettier check bestanden
- [x] TypeScript kompiliert
- [x] Vitest alle Tests gruen (148 tests)
- [x] Keine UI-Aenderungen — kein Design Review noetig

## Phase 4: Abschluss (post-push, not validated by hook)
- [ ] Commit + Push auf Feature-Branch
- [ ] CI gruen
- [ ] GitHub Issue kommentiert
- [ ] GitHub Issue geschlossen
- [ ] Project Board Status auf "Done"
