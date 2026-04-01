# Design Review — Issue #609

> RouteEditor UI — Cards mit Schatten und Route sichtbar auf Karte

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben (bg-white, bg-gray-*, text-red-* etc.)
- [x] Keine hardcodierten Radii (rounded-sm/md/lg/xl/2xl)
- [x] Keine hardcodierten Shadows — `shadow-[var(--shadow-card-raised)]` ist Token-basiert
- [x] Keine nativen HTML-Elemente (button, input, select, textarea)
- [x] Nur Level-3/4 Tokens verwendet — `--color-bg-primary` für Routenlinie via getComputedStyle

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-route-editor-ui.png

**Befunde:**
- Cards mit sichtbarem Schatten (elevation="raised")
- Kein Card-on-Card: Map-Container hat shadow direkt
- Routenlinie: --color-bg-primary + weiße Casing-Kontur

## 3. Touch Targets

- [x] Alle interaktiven Elemente >= 44x44px
- [x] Keine neuen interaktiven Elemente hinzugefügt

## 4. Weissraum & Spacing

- [x] Container-Padding unverändert
- [x] Card-Abstände konsistent (space-y-4)
- [x] Kein Card-on-Card Schatten

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Reine visuelle Konsistenz-Fixes. Keine Layout-Änderungen, nur elevation und Routenfarbe.
