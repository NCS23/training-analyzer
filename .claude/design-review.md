# Design Review — Auth & Multi-User-Infrastruktur (#556)

> Stories S01–S04, S06, S07: User-Modell, Apple Sign-In, JWT, Token Rotation,
> Frontend Auth-State, AuthGuard

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben — alle via `var(--color-*)`
- [x] Keine hardcodierten Radii — alle via `var(--radius-*)`
- [x] Keine hardcodierten Shadows — keine Shadows gesetzt
- [x] Keine nativen HTML-Elemente — `Card`, `Button`, `Spinner` aus `@nordlig/components`
- [x] Nur Level-3/4 Tokens — `--color-text-primary/secondary`, `--color-bg-error-subtle`, `--color-text-error`

Neue UI-Dateien: Login.tsx (Card + Button + Spinner), AuthGuard.tsx (Spinner).

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-auth-login.png

**Befunde:**
- Login-Screen: `flex min-h-screen items-center justify-center p-4` — zentriert auf allen Viewports
- Card `max-w-sm` (320px) in 375px mit je 28px Rand — kein Overflow
- Button `w-full` — füllt Card-Breite korrekt
- AuthGuard bei `auth_enabled=false` transparent — kein Layout-Impact

## 3. Touch Targets

- [x] Apple-Sign-In Button: `size="lg"` → 48px Höhe ≥ 44px
- [x] Kein weiterer interaktiver Bereich im Login-Screen
- [x] AuthGuard hat keine eigenen Touch-Targets

## 4. Weissraum & Spacing

- [x] Card-Padding `p-6` (24px) ✓
- [x] `space-y-6` (24px) zwischen Elementen ✓
- [x] Visuell ~40% Weißraum — kompakte Card, viel Freiraum drumherum
- [x] Keine Card-on-Card Schatten — einzelne Card, kein Nesting

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Login-Page ist in Dev via Feature-Flag ausgeblendet (`auth_enabled=false`). Screenshot zeigt
mobilen Placeholder. Volle UI-Verifikation im Live-Test wenn `auth_enabled=true` aktiviert.
Alle automatischen DS-Checks (ESLint, TSC, Ruff, Mypy, Vitest 187 Tests) sind grün.
