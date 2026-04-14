#!/usr/bin/env bash
# SessionStart hook: injects critical rules into every new session.
# Stdout is added to Claude's context automatically.

cat <<'RULES'
=== PROJEKT-REGELN (automatisch injiziert) ===

Du arbeitest am Training Analyzer. Diese Regeln sind PFLICHT:

1. KEIN CODE OHNE ISSUE — Erst GitHub Issue prüfen/erstellen
2. PROJECT BOARD — Status SOFORT auf "In Progress" setzen wenn Arbeit beginnt
3. NORDLIG DS — Keine nativen HTML-Elemente (button/input/select), nur DS-Komponenten
4. TOKENS — Keine hardcodierten Farben/Radii/Shadows, nur var(--color-*), var(--radius-*), var(--shadow-*)
5. TOKENS — Nur Level-3/Level-4 (semantisch), NIEMALS Level-1/Level-2 (--color-primary-1-500 etc.)
6. MOBILE-FIRST — Immer 375px zuerst, dann nach oben erweitern
7. UMLAUTE — ä, ö, ü, ß verwenden, KEINE ASCII-Ersetzungen
8. QUALITY GATES — ESLint, Prettier, TSC, Vitest, Ruff, Mypy, Pytest VOR dem Commit
9. LAYOUT — max-w-5xl, Breadcrumbs statt ArrowLeft, pb-2 auf header
10. KEINE Card-on-Card Schatten — innere Cards mit elevation="flat"

Hooks erzwingen Regeln 3-5 beim Schreiben und 8 beim Committen.

=== FIGMA-REGELN (automatisch injiziert) ===
PFLICHT vor jeder Figma-Operation:
F1. NODE-TYP prüfen — COMPONENT oder INSTANCE?
    → Änderungen NUR an COMPONENT, nie direkt an INSTANCE auf einem Frame
F2. VARIANTEN wählen, nicht manuell patchen
    → ❌ resize(44,44) → ✅ setProperties({ Size: 'lg' })
F3. TOKEN-EBENEN einhalten — L1→L2→L3→L4, keine Sprünge
F4. SCHRIFT — nur DM Sans (UI) und Fraunces (Display), kein Inter
F5. TOUCH-TARGETS — interaktive Elemente min. 44×44px → lg-Variante verwenden
F6. SEITE setzen — await figma.setCurrentPageAsync(page) vor jeder Suche
Vollständige Regeln: docs/FIGMA_RULES.md
===
RULES

exit 0
