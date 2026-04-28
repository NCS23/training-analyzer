# Design Review — Dialog-Scroll auf Mobile (#776)

> Folge zu #774. SessionDetailDialog hatte einen verschachtelten
> `max-h-[60vh] overflow-y-auto` Container der auf Mobile zu eng war
> und mit dem Combobox-Dropdown-Override (#774) konkurrierte.

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben
- [x] Keine hardcodierten Radii
- [x] Keine hardcodierten Shadows
- [x] Keine nativen HTML-Elemente — Änderung am bereits vorhandenen `<div>`
- [x] Nur Level-3/4 Tokens — keine Farb-Tokens berührt

Geänderte Datei: `frontend/src/components/day-card/SessionDetailDialog.tsx` — der innere Scroll-Container des Dialogs wird auf `calc(100dvh - 180px)` gesetzt mit Touch-Scroll-Properties.

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-combobox-scroll.png

(Bestehender Screenshot aus #774 dokumentiert das Combobox-Verhalten — der Dialog-Scroll-Fix ist visuell nur durch die größere Höhe sichtbar, nicht durch separates Layout.)

**Berechnung iPhone 13 Mobile (~700px Höhe):**
- Vorher: `60vh` = 420px für den Dialog-Inhalt
- Nachher: `calc(100dvh - 180px)` = ~520px (Header ~60px + Footer ~60px + Padding ~60px)
- → ~25% mehr nutzbarer Platz, alle Form-Felder besser erreichbar

**Touch-Scroll-Verhalten:**
- `overscroll-behavior: contain` — Wischen am Listen-Ende reisst nicht den Body mit
- `touch-action: pan-y` — vertikales Wischen explizit erlaubt
- `WebkitOverflowScrolling: touch` — Momentum-Scroll auf iOS

## 3. Touch Targets

- [x] Keine Touch-Target-Änderungen — nur Container-Höhe
- [x] Touch-Scroll-Verhalten verbessert (war vorher unzuverlässig)

## 4. Weissraum & Spacing

- [x] Keine Layout-Veränderung — `space-y-4` bleibt
- [x] Bestehende Card/Sektionen unverändert

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Minimal-invasive Anpassung: nur die max-height und Touch-Scroll-Properties. Behebt User-Bug "Scrollen funktioniert gar nicht gut in dem Dialog". Funktioniert mit dem Combobox-Override aus #774 zusammen, weil dort `min(60vh, 480px)` durch das Popover-Portal außerhalb dieses Dialog-Body-Scrolls liegt.

Quality Gates: ESLint, Prettier, TSC, Vitest 199, Vite Build — alle grün.
