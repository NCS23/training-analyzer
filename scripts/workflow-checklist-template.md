# Workflow Checklist — Issue #ISSUE_NUMBER

## Phase 0: Pre-Code
- [ ] GitHub Issue gelesen (Akzeptanzkriterien + Taskbreakdown)
- [ ] PROJEKT_REGELN.md gelesen
- [ ] DESIGN_REVIEW.md gelesen (bei UI-Aenderungen)
- [ ] DOMAIN_MODEL.md gelesen (bei Datenmodell-Aenderungen)

## Phase 1: Branch & Board
- [ ] Feature-Branch erstellt (kein main!)
- [ ] Issue auf "In Progress" im Project Board gesetzt

## Phase 2: Implementation
- [ ] Tests geschrieben (Unit/Integration)
- [ ] TypeScript strict (kein any, kein @ts-ignore)

## Phase 3: Quality Gates
- [ ] ESLint 0 Warnings
- [ ] Prettier check bestanden
- [ ] TypeScript kompiliert
- [ ] Vitest alle Tests gruen
- [ ] UX/Design Review Report erstellt (siehe .claude/design-review.md)

## Phase 4: Abschluss
- [ ] Commit + Push auf Feature-Branch
- [ ] CI gruen
- [ ] GitHub Issue kommentiert
- [ ] GitHub Issue geschlossen
- [ ] Project Board Status auf "Done"
