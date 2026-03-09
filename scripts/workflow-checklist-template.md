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
- [ ] Keine hardcodierten Farben/Radii/Shadows (Audit geprueft)
- [ ] Nordlig DS Komponenten verwendet (keine nativen HTML-Elemente)
- [ ] TypeScript strict (kein any, kein @ts-ignore)

## Phase 3: Quality Gates
- [ ] ESLint 0 Warnings
- [ ] Prettier check bestanden
- [ ] TypeScript kompiliert
- [ ] Vitest alle Tests gruen
- [ ] UX/Design Review durchgefuehrt (DESIGN_REVIEW.md Checkliste)
- [ ] Mobile-First geprueft (375px)
- [ ] Touch-Targets >= 44x44px

## Phase 4: Abschluss
- [ ] Commit + Push auf Feature-Branch
- [ ] CI gruen
- [ ] GitHub Issue kommentiert
- [ ] GitHub Issue geschlossen
- [ ] Project Board Status auf "Done"
