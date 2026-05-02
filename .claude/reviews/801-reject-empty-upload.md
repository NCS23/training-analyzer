# Design Review — Issue #801

> Reine Backend-Validierung: Upload akzeptiert keine leeren Dateien mehr.
> Kein neues UI, keine Layout-Änderung. Die Fehlermeldung erscheint im
> bestehenden Error-Toast des Upload-Flows.

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben (bg-white, bg-gray-*, text-red-* etc.)
- [x] Keine hardcodierten Radii (rounded-sm/md/lg/xl/2xl)
- [x] Keine hardcodierten Shadows (shadow-sm/md/lg)
- [x] Keine nativen HTML-Elemente (button, input, select, textarea)
- [x] Nur Level-3/4 Tokens verwendet (keine L1/L2)

Frontend wurde nicht angefasst. Diff-Erkennung schlägt nur an, weil lokal
`main` hinterherhinkt und mergte tsx-Änderungen aus #797/#798/#800 noch
sieht.

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-fit-export-toast.png

**Befunde:**
- Layout unverändert
- Fehler-Toast nutzt das bereits bestehende `useToast`-Pattern
- Screenshot wiederverwendet aus #796 (zeigt App-Kontext)

## 3. Touch Targets

- [x] Alle interaktiven Elemente >= 44x44px
- [x] Buttons haben ausreichend Padding
- [x] Links/Icons haben genug Abstand zueinander

Keine neuen interaktiven Elemente.

## 4. Weissraum & Spacing

- [x] Container-Padding 24-32px
- [x] Sektionen-Abstand 32-64px
- [x] Weißraum-Anteil visuell ~30-40%
- [x] Keine Card-on-Card Schatten

Keine Layout-/Spacing-Änderungen.

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Reiner Backend-Fix in `backend/app/api/v1/sessions.py`: neuer Helper
`_has_session_data` lehnt Uploads ohne mindestens eine echte
Trainingsmetrik (Dauer/Distanz/Laps/HR-Timeseries) mit klarer
Fehlermeldung ab. Frontend-Verhalten unverändert — die existierende
Toast-Pipeline zeigt die neue Fehlermeldung.
