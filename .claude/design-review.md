# Design Review — Issue #606

> RouteEditor: Read-only/Edit-Modus mit Kebab-Menü

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben (bg-white, bg-gray-*, text-red-* etc.)
- [x] Keine hardcodierten Radii (rounded-sm/md/lg/xl/2xl)
- [x] Keine hardcodierten Shadows (shadow-sm/md/lg)
- [x] Keine nativen HTML-Elemente (button, input, select, textarea)
- [x] Nur Level-3/4 Tokens verwendet (keine L1/L2)

Alle bestehenden DS-Komponenten (Button, DropdownMenu, Input, ActionBar, Spinner) werden weiterhin genutzt. Keine neuen Primitives eingeführt.

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-route-editor-readonly.png

**Befunde:**
- Neue Route: Edit-Modus (Name-Input + ActionBar) korrekt
- Bestehende Route: Read-only-Ansicht mit Kebab-Menü oben rechts
- Kebab-Menü: Bearbeiten, Als GPX exportieren, Als FIT exportieren, Löschen
- ActionBar enthält nur Abbrechen + Speichern

## 3. Touch Targets

- [x] Alle interaktiven Elemente >= 44x44px
- [x] Kebab-Menü-Button hat ausreichend Padding (ghost sm)
- [x] DropdownMenuItem-Elemente haben min. 44px Höhe

## 4. Weissraum & Spacing

- [x] Container-Padding 24-32px (p-4 pt-6 md:p-6 md:pt-8)
- [x] Sektionen-Abstand via space-y-4
- [x] Keine Card-on-Card Schatten

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Refactoring des RouteEditors nach dem SessionDetail-Pattern. Keine neuen UI-Primitives, nur Umstrukturierung der Anzeigemodi. Read-only-Ansicht standardmäßig, Edit-Modus auf Anfrage via Kebab-Menü.
