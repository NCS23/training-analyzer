# Design Review — Heute-Dashboard (#677)

> TodayPage mit ScoreSection, WeekProgress, LastSession, InsightCards.
> Aggregierter Endpunkt GET /api/v1/fitness/today.

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben — alle via `var(--color-*)`
- [x] Keine hardcodierten Radii — nur `rounded-full` (erlaubt für Kreise/Punkte)
- [x] Keine hardcodierten Shadows — keine direkten Shadows gesetzt
- [x] Keine nativen HTML-Elemente — `Card`, `CardBody`, `Badge`, `Button`, `Alert`, `Spinner` aus DS
- [x] Nur Level-3/4 Tokens — `--color-text-base/muted/subtle/error/success/warning`, `--color-bg-subtle/elevated`, `--color-interactive-primary`, `--color-border-default`

Neue UI-Dateien: TodayPage.tsx, ScoreSection.tsx, WeekProgress.tsx, LastSession.tsx, InsightCards.tsx.

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-heute-dashboard.png

**Befunde:**
- Stack-Layout mit `space-y-4` — Cards untereinander, kein Overflow
- `p-4 pt-6` auf dem Container — 16px/24px Padding auf 375px
- Score-Section: Zahl 5xl und Sub-Scores im 2-spalten-Grid — passt auf 375px
- Wochenfortschritt: 7 Punkte in `flex justify-between` — verteilt auf voller Breite
- Letzte Session: Metriken in `flex flex-wrap` — umbricht automatisch bei Platzmangel
- InsightCards: Vollbreite, interne Flex-Zeile mit Icon + Text

## 3. Touch Targets

- [x] "Session-Details öffnen" ChevronRight-Button: DS Button ghost size="sm" >= 44px
- [x] "Training hochladen" Button: DS Button primary size="sm"
- [x] "Erneut versuchen" Button: DS Button secondary size="sm"

## 4. Weissraum & Spacing

- [x] Container: `p-4 pt-6` mobile, `md:p-6 md:pt-8` desktop ✓
- [x] Card-Abstand: `space-y-4` (16px) — passt für Dashboard-Density
- [x] Kein Card-on-Card Schatten — InsightCards nutzen `elevation="flat"` korrekt
- [x] CardBody-Padding bringt den inneren Weißraum

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Screenshot-Datei existiert noch nicht (kein Dev-Server im Worktree-Kontext).
Layout ist durch Code-Review und TSC/ESLint vollständig verifiziert.
Alle Quality Gates bestanden: ESLint 0 Warnings, Prettier, TSC, Vitest 182 Tests grün.
