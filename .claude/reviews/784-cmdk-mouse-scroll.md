# Design Review — Combobox Maus-Scroll Fix (#784)

> Folge zu #774/#776/#778/#780/#782. User: "Ich kann mit der maus nicht
> sinnvoll scrollen in den dropdowns". Bekannter cmdk-Bug — onPointerMove
> auf Items ändert die Selektion bei Maus-Move + scrollt automatisch dahin.

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben
- [x] Keine hardcodierten Radii
- [x] Keine hardcodierten Shadows
- [x] Keine nativen HTML-Elemente
- [x] Nur Level-3/4 Tokens

Geänderte/neue Dateien:
- `frontend/src/utils/cmdkScrollFix.ts` — Wheel-Listener (idempotent)
- `frontend/src/utils/cmdkScrollFix.test.ts` — 4 Tests
- `frontend/src/main.tsx` — installCmdkScrollFix() Init
- `frontend/src/index.css` — `[cmdk-list].cmdk-scrolling [cmdk-item] { pointer-events: none; }` + `scroll-behavior: auto`

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-combobox-scroll.png

(Wiederverwendet — der Fix ist Verhaltens-, kein Layout-Change.)

**Wirkung:**
- Bei aktivem Wheel-Scroll im `[cmdk-list]` werden für 150ms Pointer-Events auf den Items deaktiviert
- cmdk's `onPointerMove` triggert nicht mehr → keine Auto-Selection-Änderung → kein scrollIntoView-Konflikt
- Nach 150ms ohne Wheel-Event sind Items wieder klickbar

## 3. Touch Targets

- [x] Touch-Targets unverändert
- [x] Klick auf Items funktioniert weiter (Pointer-Down/Up sind keine PointerMove)
- [x] Tastatur-Navigation (Arrow-Keys) funktioniert weiter (kein Pointer-Event)

## 4. Weissraum & Spacing

- [x] Keine Layout-Veränderungen
- [x] Combobox-Optik bleibt 1:1

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Bekannter cmdk-Workaround (Issue #267 dort): Wheel-Detect → temporär pointer-events disable → cmdk's onPointerMove triggert nicht mehr während Scroll. Saubere CSS+JS-Lösung ohne cmdk-Code zu patchen. Wenn NDS später `disablePointerSelection` durchreicht, kann das hier weg.

Quality Gates: ESLint, Prettier, TSC, Vitest 203 — alle grün.
