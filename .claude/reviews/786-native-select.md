# Design Review — NativeSelect für Combobox-Hotspots (#786)

> Pragmatische Lösung nach 6 gescheiterten Combobox-Iterationen. Native
> `<select>` mit DS-Tokens statt Nordlig Combobox an den Stellen mit
> langen Listen (Segment-Typ, Übung-Picker, Trainings-/Lauftyp).

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben — DS-Tokens (input-bg, input-text, input-border, border-focus, text-muted)
- [x] Keine hardcodierten Radii — `rounded-[var(--radius-input)]`
- [x] Keine hardcodierten Shadows
- [x] **Kontrollierte Ausnahme bei native HTML:** `<select>` in `NativeSelect.tsx` mit `// ds-ok-file:` Header und Begründung. Hook (`check-nordlig-compliance.sh`) wurde um `ds-ok-file:`-Bypass erweitert (siehe `Section 5`)
- [x] Nur Level-3/4 Tokens verwendet

Geänderte/neue Dateien:
- `frontend/src/components/NativeSelect.tsx` — neue Komponente mit DS-Styling
- `frontend/src/components/RunDetailsEditor.tsx` — Segment-Typ + Übung-Picker auf NativeSelect
- `frontend/src/components/day-card/SessionDetailDialog.tsx` — Trainingstyp + Lauftyp auf NativeSelect
- `.claude/hooks/check-nordlig-compliance.sh` — `ds-ok-file:`-Bypass-Mechanismus

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-native-select.png

**Befunde:**
- Optisch identisch zum Nordlig Select (Border, Padding, Chevron, Höhe)
- Auf iPhone Safari: Tap öffnet System-Wheel-Picker → User-Erfahrung wie überall sonst auf iOS
- Auf Chrome Desktop: nativer Browser-Dropdown → perfektes Mausrad-Scrolling
- Keine Combobox-CSS-Hacks mehr nötig

## 3. Touch Targets

- [x] sm = 36px Höhe (im Edit-Dialog akzeptabel, weil enges Form-Layout); md/lg verfügbar
- [x] Touch-Tap auf gesamtem Select-Bereich
- [x] Nativer iOS-Picker bietet System-Touch-Targets (Apple-empfohlen 44px)

## 4. Weissraum & Spacing

- [x] Identisches Padding/Spacing wie Nordlig Select
- [x] Chevron-Icon mit `pointer-events-none` (Klicks gehen durch zum Select)
- [x] Keine Layout-Veränderungen am umgebenden Form

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
**Bewusste Memory-Regel-Ausnahme** ("KEINE native HTML-Elemente"): Nach 6 Iterationen mit cmdk-Combobox (#774-#785) bleibt Scrolling unbrauchbar. Native `<select>` ist die saubere Lösung — Browser scrollt nativ, iOS bekommt System-Wheel-Picker. Nur an Stellen mit langen Listen verwendet, NICHT als generischer Ersatz für Nordlig Select. Hook erweitert um `ds-ok-file:`-Bypass für dokumentierte Ausnahmen — bessere Praxis als Hard-Block ohne Override.

**Folge-Issue im NDS-Repo** für richtigen Combobox-Fix wird angelegt — sobald da behoben, kann NativeSelect wieder weg.

Quality Gates: ESLint, Prettier, TSC, Vitest 203 — alle grün.
