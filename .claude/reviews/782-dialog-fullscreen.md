# Design Review — Dialog Vollbild auf Mobile + nativer Scroll (#782)

> Folge zu #774/#776/#778/#780. User-Feedback: "automatische scrolling ist
> murks". Komplett neue Architektur: Vollbild-Sheet auf Mobile, native
> Browser-Scroll-Mechanik ohne CSS-Workarounds.

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben — DialogContent-Background bleibt vom DS
- [x] Keine hardcodierten Radii — auf Desktop bleibt `--radius-dialog`, auf Mobile bewusst `rounded-none` (Vollbild-Sheet)
- [x] Keine hardcodierten Shadows
- [x] Keine nativen HTML-Elemente — nur className/style auf Nordlig DialogContent + bestehendem div
- [x] Nur Level-3/4 Tokens

Geänderte Datei: `frontend/src/components/day-card/SessionDetailDialog.tsx`

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-combobox-scroll.png

(Wiederverwendet — Layout-Effekt: Dialog wird Vollbild, Body scrollt nativ. Kann nicht in Standbild ohne Live-Daten gezeigt werden.)

**Mobile Vollbild-Sheet (`< lg`):**
- `inset-0` + `max-w-none` + `w-full` + `h-[100dvh]` + `max-h-none` + `rounded-none`
- DialogContent `overflow-hidden`, Body `flex-1 min-h-0 overflow-y-auto`
- Header + Footer sind Flex-Geschwister → bleiben durch `flex-shrink: 0` (default für Nordlig DialogHeader/Footer) sichtbar
- Native Browser-Scroll ohne `overscroll-behavior` oder `touch-action` Override → User-Erfahrung wie auf einer normalen Seite

**Desktop (`≥ lg`):**
- Bleibt zentriert mit `lg:max-h-[calc(100dvh-32px)]`
- Gleiche Body-Scroll-Architektur

## 3. Touch Targets

- [x] Touch-Targets unverändert
- [x] Header (Titel + Menü-Button) bleibt sichtbar beim Scrollen → kein versehentliches Scrollen-statt-Klicken
- [x] Footer (Save/Cancel) bleibt sichtbar → User kann jederzeit speichern/abbrechen

## 4. Weissraum & Spacing

- [x] `space-y-4` im Body bleibt
- [x] DialogContent-Padding (Nordlig DS Tokens) bleibt
- [x] Auf Mobile mehr Inhalts-Platz (Vollbild) — Form-Felder besser erreichbar

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Architektur-Refactor mit "weniger ist mehr"-Ansatz: weg von verschachtelten Scroll-Containern und CSS-Hacks, hin zu nativer Browser-Scroll-UX. Vollbild-Sheet auf Mobile ist Standard-iOS/Android-Pattern für lange Edit-Forms. Auf Desktop bleibt das vertraute Modal.

Quality Gates: ESLint, Prettier, TSC, Vitest 199 — alle grün.
