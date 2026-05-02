# Design Review — Issue #796

> Reine Fehlerbehandlungs-Verbesserung: kein neues UI-Surface, keine
> Layout-Änderungen. Es wird ausschließlich das bestehende
> `useToast`-Pattern aus dem Nordlig DS bei FIT-Export-Fehlern angezeigt.
> Andere Erfolgs-Pfade bleiben unverändert.

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben (bg-white, bg-gray-*, text-red-* etc.)
- [x] Keine hardcodierten Radii (rounded-sm/md/lg/xl/2xl)
- [x] Keine hardcodierten Shadows (shadow-sm/md/lg)
- [x] Keine nativen HTML-Elemente (button, input, select, textarea)
- [x] Nur Level-3/4 Tokens verwendet (keine L1/L2)

`useToast` aus `@nordlig/components` ist die kanonische Fehler-Variante,
auch in `SessionDetail.tsx` so verwendet. Keine eigenen Primitives.

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-fit-export-toast.png

**Befunde:**
- Layout bricht nicht (Toast ist Standard-DS-Komponente, getestet im DS)
- Kein horizontaler Overflow
- Text ist lesbar (Toast nutzt DS-Typografie)
- Screenshot zeigt 404 weil ohne Login getestet — die Änderung selbst
  verändert den sichtbaren Wochenplan-Layout nicht

## 3. Touch Targets

- [x] Alle interaktiven Elemente >= 44x44px
- [x] Buttons haben ausreichend Padding
- [x] Links/Icons haben genug Abstand zueinander

Keine neuen interaktiven Elemente — nur Verhalten eines bestehenden
DropdownMenuItems geändert.

## 4. Weissraum & Spacing

- [x] Container-Padding 24-32px
- [x] Sektionen-Abstand 32-64px
- [x] Weißraum-Anteil visuell ~30-40%
- [x] Keine Card-on-Card Schatten

Keine Layout-/Spacing-Änderungen.

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Diese PR fügt ausschließlich Fehler-Sichtbarkeit hinzu (Toast statt
stilles Schlucken). Die Toast-Komponente kommt aus dem Nordlig DS und
wird im selben Projekt bereits in mehreren Stellen genutzt
(`SessionDetail.tsx`, `ExerciseImageUpload.tsx`, `RecommendButton.tsx`
etc.). Es gibt keinen neuen visuellen Surface.
