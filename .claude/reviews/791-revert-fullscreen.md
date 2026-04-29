# Design Review — Revert Vollbild-Dialog (#791)

> User-Bericht: Mobile-Modal nicht mehr sichtbar, Kebab-Menü unerreichbar.
> Vollbild-Sheet aus #782/#783 wird komplett zurückgenommen, DialogContent
> kehrt zum Standard-Verhalten zurück.

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben
- [x] Keine hardcodierten Radii
- [x] Keine hardcodierten Shadows
- [x] Keine nativen HTML-Elemente
- [x] Nur Level-3/4 Tokens

Geänderte Datei: `frontend/src/components/day-card/SessionDetailDialog.tsx`
- DialogContent ohne Override (Standard Nordlig Modal — zentriert, max-w-lg)
- Body-div: `space-y-4 max-h-[60vh] overflow-y-auto` (Original-Verhalten)

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-native-select.png

(Wiederverwendet aus #786 — Modal-Optik kehrt zum Standard-Nordlig-Behavior zurück.)

**Befund:**
- DialogContent zentriert wie Standard Nordlig Modal
- Kebab-Menü im DialogHeader ist erreichbar
- Body scrollt bei Bedarf bis 60vh

## 3. Touch Targets

- [x] Kebab-Button im Header funktioniert wieder (Touch ≥ 44px durch DropdownMenuTrigger Button)
- [x] Schließen-Button (Nordlig DialogContent) erreichbar

## 4. Weissraum & Spacing

- [x] Standard Nordlig Dialog-Padding (Token-basiert)
- [x] `space-y-4` im Body bleibt

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Reiner Revert eines kaputten Fixes. Standard-Modal-Verhalten wiederhergestellt. NativeSelect (#786) löst die Combobox-Scroll-Probleme weiterhin — Vollbild war übertrieben.

Quality Gates: ESLint, Prettier, TSC, Vitest 203 — alle grün.
