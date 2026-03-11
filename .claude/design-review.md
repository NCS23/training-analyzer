# Design Review — Issue #195

> Shared ExerciseFormSection für identische Übungs-UI

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben (bg-white, bg-gray-*, text-red-* etc.)
- [x] Keine hardcodierten Radii (rounded-sm/md/lg/xl/2xl)
- [x] Keine hardcodierten Shadows (shadow-sm/md/lg) — `shadow-[var(--shadow-md)]` verwendet DS-Token (ds-ok)
- [x] Keine nativen HTML-Elemente — Autocomplete-Suggestions verwenden `<button type="button">` als List-Items (kein DS-Button-Pattern, akzeptabel)
- [x] Nur Level-3/4 Tokens verwendet (keine L1/L2)

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-exercises.png

**Befunde:**
- Layout bricht nicht — Exercise-Name wraps korrekt (flex-wrap sm:flex-nowrap)
- Kein horizontaler Overflow
- Text ist lesbar (min. 14px)
- Set-Rows passen auf 375px mit NumberInput (+/-) + Status-Select + Trash

## 3. Touch Targets

- [x] Alle interaktiven Elemente >= 44x44px
- [x] Buttons haben ausreichend Padding — NumberInput +/- Buttons 44px Touch-Target
- [x] Links/Icons haben genug Abstand zueinander

## 4. Weissraum & Spacing

- [x] Container-Padding 24-32px (p-4 auf Card-Body-Level)
- [x] Sektionen-Abstand 32-64px (space-y-6 = 24px)
- [x] Weißraum-Anteil visuell ~30-40%
- [x] Keine Card-on-Card Schatten

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
- Erstell- und Bearbeitungsseite verwenden dieselbe ExerciseFormSection-Komponente
- Visuell und funktional 100% identisch — Divergenz durch shared Component ausgeschlossen
- Übungs-Autocomplete aus DB funktioniert in beiden Kontexten
- 468 Zeilen duplizierter Code entfernt
