# Design Review — DialogContent direkt scrollbar (#780)

> Folge zu #774/#776/#778. Verschachtelter Inner-Scroll-Container raus,
> stattdessen DialogContent selbst scrollt. Eliminiert Konkurrenz mit
> Combobox-Popover und Radix Body-Scroll-Lock.

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben
- [x] Keine hardcodierten Radii
- [x] Keine hardcodierten Shadows
- [x] Keine nativen HTML-Elemente — nur className-Override am Nordlig DialogContent
- [x] Nur Level-3/4 Tokens — keine Token-Verwendung berührt

Geänderte Datei: `frontend/src/components/day-card/SessionDetailDialog.tsx`
- `DialogContent` bekommt `className="max-h-[calc(100dvh-32px)] overflow-y-auto"` + Touch-Properties
- Bisheriger innerer Scroll-div (`max-h + overflow-y-auto + flex 1 1 auto + min-height: 0`) wird zu schlichtem `<div className="space-y-4">`

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-combobox-scroll.png

(Wiederverwendet aus #774 — Layout-mässig keine Veränderung. Verbessertes Verhalten ist nicht im Standbild sichtbar.)

**Berechnung:**
- `100dvh - 32px` = ~668px auf 700px iPhone (16px Rand oben/unten)
- Vorher (#776/#778): `100dvh - 180px` = ~520px für nur den Body
- → Mehr Platz für Inhalt; kein verschachtelter Scroll

## 3. Touch Targets

- [x] Touch-Targets unverändert (Buttons im Header/Footer + Form-Felder)
- [x] Touch-Scroll: `touch-action: pan-y` + `overscroll-behavior: contain` + `WebkitOverflowScrolling: touch` direkt auf DialogContent

## 4. Weissraum & Spacing

- [x] `space-y-4` bleibt im inneren div
- [x] DialogContent-Padding (Nordlig DS Tokens) bleibt
- [x] Kein doppeltes Scroll mehr → einfacheres Layout

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Architektur-Vereinfachung: ein Scroll-Container statt zwei. Behebt potenzielle Konflikte zwischen Inner-Scroll und Radix-Popover-Body-Scroll-Lock. Wenn der Dialog-Body sehr lang wird, scrollen Header und Footer mit — bei dem aktuellen Edit-Form akzeptabel (kompakter Header, kompakter Footer). Falls später visuell stört: Header/Footer als sticky setzen via CSS-Override.

Quality Gates: ESLint, Prettier, TSC, Vitest 199 — alle grün.
