# Workflow Checklist — Issue #211

## Phase 0: Pre-Code
- [x] GitHub Issue gelesen (Akzeptanzkriterien + Taskbreakdown)
- [x] PROJEKT_REGELN.md gelesen
- [x] DESIGN_REVIEW.md gelesen (bei UI-Änderungen)
- [x] CLEAN_CODE.md gelesen

## Phase 1: Branch & Board
- [x] Feature-Branch erstellt (feature/211-consolidate-constants)
- [x] Issue auf "In Progress" im Project Board gesetzt

## Phase 2: Implementation
- [x] constants/plan.ts erstellt (DAY_LABELS, RUN_TYPE_LABELS, SESSION_TYPE_OPTIONS)
- [x] constants/training.ts erweitert (CATEGORY_LABELS)
- [x] DayCard.tsx — lokale DAY_LABELS, RUN_TYPE_LABELS, SESSION_TYPE_OPTIONS entfernt → Import
- [x] MoveSessionDialog.tsx — lokale DAY_LABELS entfernt → Import
- [x] PhaseWeeklyTemplateEditor.tsx — lokale DAY_LABELS, SESSION_TYPE_OPTIONS entfernt → Import
- [x] TemplatePickerDialog.tsx — lokale RUN_TYPE_LABELS entfernt → Import
- [x] WeeklyPlan.tsx — lokale RUN_TYPE_LABELS + CATEGORY_LABELS (EN→DE) entfernt → Import
- [x] StrengthProgression.tsx — lokale CATEGORY_LABELS entfernt → Import
- [x] exercise-helpers.ts — lokale CATEGORY_LABELS → Re-Export aus constants/training.ts
- [x] plan-helpers.ts — lokale DAY_LABELS → Re-Export aus constants/plan.ts

## Phase 3: Quality Gates
- [x] TSC --noEmit bestanden
- [x] ESLint 0 Warnings
- [x] Vitest 145 Tests bestanden

## Phase 4: Abschluss (post-push, not validated by hook)
- [ ] Commit + Push auf Feature-Branch
- [ ] CI grün
- [ ] GitHub Issue kommentiert
- [ ] GitHub Issue geschlossen
- [ ] Project Board Status auf "Done"
