# Design Review — Issue #799

> Backend-Verhaltensänderung (Workout-Name in FIT-Datei) plus eine
> Frontend-Signaturanpassung (`notes`-Argument entfernt). Kein neuer
> visueller Surface, kein Layout, kein Spacing, keine neuen Komponenten.

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben (bg-white, bg-gray-*, text-red-* etc.)
- [x] Keine hardcodierten Radii (rounded-sm/md/lg/xl/2xl)
- [x] Keine hardcodierten Shadows (shadow-sm/md/lg)
- [x] Keine nativen HTML-Elemente (button, input, select, textarea)
- [x] Nur Level-3/4 Tokens verwendet (keine L1/L2)

Frontend-Diff entfernt nur einen Funktionsparameter — keine Tokens, Farben
oder Komponenten betroffen.

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-fit-export-toast.png

**Befunde:**
- Layout unverändert — kein UI-Surface betroffen
- Wochenplan-Dialog rendert identisch
- Screenshot wiederverwendet aus #796 (zeigt den Wochenplan-Kontext)

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
Reine Verhaltensänderung im Backend: der Workout-Name in der exportierten
FIT-Datei kommt jetzt aus `SESSION_TYPE_LABELS` (z. B. "Langer Lauf")
statt aus den Notizen. Frontend wurde nur an die neue API-Signatur
angepasst — `notes`-Argument entfernt. Keine sichtbaren UI-Änderungen.
