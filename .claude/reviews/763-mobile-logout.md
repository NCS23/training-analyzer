# Design Review — Mobile-Logout-Button (#763)

> Logout-Button in der `MobileTopBar` ergänzt — auf Mobile fehlte bisher
> jede Logout-Möglichkeit, weil die Sidebar `lg:hidden` ist.

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben — `var(--color-text-muted/base)`, `var(--color-bg-surface)`
- [x] Keine hardcodierten Radii — `rounded-[var(--radius-sm)]` (vom DS Button)
- [x] Keine hardcodierten Shadows
- [x] Keine nativen HTML-Elemente — `<Button variant="ghost" size="sm">` aus `@nordlig/components`
- [x] Nur Level-3/4 Tokens verwendet

Geänderte Datei: `frontend/src/layouts/AppLayout.tsx` (`MobileTopBar` Komponente)

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-topbar-logout.png

**Befunde:**
- TopBar-Höhe `h-[64px]` bleibt unverändert — kein Layout-Shift
- Logo + Titel links, Logout-Button rechts, durch `justify-between` getrennt
- Auf 375px Breite reichlich Platz, kein Overflow
- Icon-Button mit `h-5 w-5` LogOut-Icon — gut erkennbar bei mobiler Daumenbedienung

## 3. Touch Targets

- [x] Logout-Button: Nordlig DS `<Button size="sm">` rendert ≥ 44px Höhe
- [x] `!px-3` Override hält den Button schmal aber tappbar (>= 44×44)
- [x] Klare räumliche Trennung von Logo (durch `justify-between`)

## 4. Weissraum & Spacing

- [x] Container-Padding `px-5` (20px) — passt zur bestehenden TopBar
- [x] Kein Card-on-Card Schatten
- [x] Konsistent mit der Desktop-Sidebar (selber LogOut-Icon, gleicher `useAuth().logout` Flow)

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Minimaler, fokussierter Fix für ein konkretes UX-Loch. Nordlig Button
statt nativem `<button>` (anders als die Desktop-Sidebar, die noch ein
natives Element verwendet — könnte bei Gelegenheit angeglichen werden,
aber bewusst nicht in dieser Branch). Quality Gates: ESLint, Prettier,
TSC, Vitest 191 — alle grün.
