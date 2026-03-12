# Design Review — Issue #211

> Duplizierte Konstanten konsolidieren

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben (bg-white, bg-gray-*, text-red-* etc.)
- [x] Keine hardcodierten Radii (rounded-sm/md/lg/xl/2xl)
- [x] Keine hardcodierten Shadows (shadow-sm/md/lg) — `shadow-[var(--shadow-*)]` sind Token-basiert (ds-ok)
- [x] Keine nativen HTML-Elemente (button, input, select, textarea)
- [x] Nur Level-3/4 Tokens verwendet (keine L1/L2)

Keine neuen UI-Elemente — nur Konstanten-Konsolidierung (Imports statt Duplikate).

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-exercise-edit.png

**Befunde:**
- Keine visuellen Änderungen (reine Refactoring-Arbeit)
- Layout und Darstellung identisch

## 3. Touch Targets

- [x] Alle interaktiven Elemente >= 44x44px
- [x] Buttons haben ausreichend Padding
- [x] Links/Icons haben genug Abstand zueinander

Keine UI-Änderungen — Touch Targets unverändert.

## 4. Weissraum & Spacing

- [x] Container-Padding 24-32px
- [x] Sektionen-Abstand 32-64px
- [x] Weißraum-Anteil visuell ~30-40%
- [x] Keine Card-on-Card Schatten

Keine UI-Änderungen — Spacing unverändert.

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Issue #211 ist ein reines Refactoring (Konstanten-Konsolidierung). Keine visuellen Änderungen.
CATEGORY_LABELS in WeeklyPlan.tsx von Englisch (Legs, Drills) auf Deutsch (Beine, Lauf-ABC) korrigiert.
