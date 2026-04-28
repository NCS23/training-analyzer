# Design Review — Dialog Flex-Scroll-Fix (#778)

> Folge zu #774/#776. Inner-Scroll-Container im Dialog war Flex-Child
> ohne `min-height: 0` → Overflow-Scroll war im Chrome unflüssig.

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben
- [x] Keine hardcodierten Radii
- [x] Keine hardcodierten Shadows
- [x] Keine nativen HTML-Elemente — nur Style-Properties am bestehenden div
- [x] Nur Level-3/4 Tokens — keine Token-Verwendung berührt

Geänderte Datei: `frontend/src/components/day-card/SessionDetailDialog.tsx` — zwei zusätzliche Flex-Properties (`flex: 1 1 auto`, `min-height: 0`) am bestehenden Scroll-Container.

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-combobox-scroll.png

(Wiederverwendet aus #774 — kein neues visuelles Layout, nur Render-/Scroll-Verhalten verbessert.)

**Bekanntes Flex-Scroll-Verhalten:**
- Default Flex-Item hat `min-height: auto` → schrumpft NICHT unter intrinsische Content-Höhe → `overflow-y: auto` greift nicht zuverlässig
- Mit `min-height: 0` + `flex: 1 1 auto` schrumpft das Item sauber innerhalb des Flex-Parents → `overflow-y: auto` arbeitet wie erwartet

## 3. Touch Targets

- [x] Keine Touch-Target-Änderungen
- [x] Touch-Scroll bleibt aktiv (Properties aus #776 unverändert)

## 4. Weissraum & Spacing

- [x] Keine Layout-Veränderung
- [x] `space-y-4` bleibt
- [x] Bestehende max-height (`calc(100dvh - 180px)`) bleibt

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Bekanntes CSS-Flex-Scroll-Pattern: `flex: 1 1 auto; min-height: 0; overflow-y: auto`. Behebt das ruckelige Verhalten in Chrome ohne andere Layout-Eigenschaften zu verändern.

Quality Gates: ESLint, Prettier, TSC, Vitest 199 — alle grün.
