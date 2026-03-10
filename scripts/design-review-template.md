# Design Review — Issue #ISSUE_NUMBER

> Dieser Report wird automatisch vom pre-push Hook validiert.
> Alle Sektionen müssen ausgefüllt sein. Screenshots müssen existieren.

## 1. Nordlig DS Compliance

<!-- AUTOMATED: Diese Sektion wird vom Hook automatisch geprüft -->
<!-- Manuell hier dokumentieren was geprüft wurde -->

- [ ] Keine hardcodierten Farben (bg-white, bg-gray-*, text-red-* etc.)
- [ ] Keine hardcodierten Radii (rounded-sm/md/lg/xl/2xl)
- [ ] Keine hardcodierten Shadows (shadow-sm/md/lg)
- [ ] Keine nativen HTML-Elemente (button, input, select, textarea)
- [ ] Nur Level-3/4 Tokens verwendet (keine L1/L2)

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
<!-- Pfad zum Screenshot einfügen, z.B.: -->
<!-- screenshot: .claude/screenshots/mobile-375.png -->
screenshot: SCREENSHOT_PATH_HERE

**Befunde:**
- Layout bricht nicht
- Kein horizontaler Overflow
- Text ist lesbar (min. 14px)

## 3. Touch Targets

- [ ] Alle interaktiven Elemente >= 44x44px
- [ ] Buttons haben ausreichend Padding
- [ ] Links/Icons haben genug Abstand zueinander

## 4. Weissraum & Spacing

- [ ] Container-Padding 24-32px
- [ ] Sektionen-Abstand 32-64px
- [ ] Weißraum-Anteil visuell ~30-40%
- [ ] Keine Card-on-Card Schatten

## 5. Gesamtbewertung

**Verdict:** PASS / FAIL

**Anmerkungen:**
<!-- Freitext für Befunde, Kompromisse, bekannte Einschränkungen -->
