# Design Review — Combobox-Dropdown Scroll-Fix (#774)

> Globaler CSS-Override für `[cmdk-list]` damit Dropdown-Listen scrollen
> und alle Optionen erreichbar sind. Reine CSS-Änderung, kein React-UI.

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben
- [x] Keine hardcodierten Radii
- [x] Keine hardcodierten Shadows
- [x] Keine nativen HTML-Elemente — der Override betrifft nur das interne `[cmdk-list]` Element des Nordlig Combobox
- [x] Nur Level-3/4 Tokens — keine Farb-Tokens berührt

Nur 1 geänderte Datei: `frontend/src/index.css` — ergänzt einen `[cmdk-list]` Override für max-height + touch/scroll-Verhalten.

**Hinweis:** Dies ist ein Workaround weil das Nordlig Combobox-Component intern `max-h-[240px]` hardcoded hat und Touch-Scroll innerhalb Radix-Popover nicht zuverlässig funktioniert. Echter Fix folgt als Issue im NDS-Repo.

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-combobox-scroll.png

**Berechnung:**
- iPhone 13 Höhe ~ 700px Viewport → `60vh` = ~420px
- 18 drills × ~40px = 720px → mit 420px sichtbarer Höhe ist ~50% sichtbar, Rest scrollbar
- Cap bei 480px für Desktop verhindert übertriebene Höhe auf 4K-Monitoren

## 3. Touch Targets

- [x] Touch-Scroll: `touch-action: pan-y` + `-webkit-overflow-scrolling: touch` + `overscroll-behavior: contain` stellen sicher dass das Wischen innerhalb der Liste landet, nicht im Body
- [x] Bestehende Combobox-Items sind bereits 40px hoch (gut für Touch)

## 4. Weissraum & Spacing

- [x] Keine Layout-Veränderungen — nur die scrollbare Höhe wächst
- [x] Bestehende Combobox-Padding bleiben unverändert

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Minimal-invasiver Quick-Fix gegen einen UX-Showstopper (User konnte Lauf-ABC + 12 weitere drills nicht erreichen). Die Werte (`60vh` mobile, `480px` cap) sind konservativ. Das echte Fix gehört ins Nordlig DS — separates Issue dort.

Quality Gates: ESLint (CSS file ignored — normal), Prettier, TSC, Vitest 199, Vite Build — alles grün.
