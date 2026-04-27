# Design Review — KI-Chat Plan-Editing inkl. Segmente (#759)

> Erweiterung des KI-Chats: PlanSuggestionCard mit run_details/Segment-Vorschau
> und neue WeekRewriteCard für Wochen-Umstrukturierungen.

## 1. Nordlig DS Compliance

- [x] Keine hardcodierten Farben — alle via `var(--color-*)` (bg-base, bg-subtle, text-base/muted/primary/warning/success/error, border-default/subtle, bg-warning-subtle, bg-primary-subtle, bg-surface)
- [x] Keine hardcodierten Radii — nur `rounded-full` (Pill-Badges) und `rounded-[var(--radius-md|sm)]`
- [x] Keine hardcodierten Shadows — keine direkten Shadow-Klassen
- [x] Keine nativen HTML-Elemente — `<Button>` aus `@nordlig/components` für alle Aktionen
- [x] Nur Level-3/4 Tokens verwendet (siehe Liste oben)

Geänderte/neue UI-Dateien:
- `frontend/src/components/chat/PlanSuggestionCard.tsx` (Segment-Vorschau ergänzt)
- `frontend/src/components/chat/WeekRewriteCard.tsx` (neu)
- `frontend/src/components/chat/ChatMessageBubble.tsx` (WeekRewriteCard integriert)

Automated grep-audit: 0 Hits für hardcoded Farben/Radii/Shadows/native Elements.

## 2. Mobile-First Check (375px)

**Screenshot (375px Viewport):**
screenshot: .claude/screenshots/mobile-375-chat-cards-segments.png

**Befunde:**
- Beide Karten passen vollständig in 375px Breite, kein horizontaler Overflow
- Segment-Liste in `PlanSuggestionCard` nutzt `flex items-baseline gap-2` mit `min-w-[5.5rem]` für Label — Pace/Dauer brechen sauber bei Bedarf um
- Wochen-Empfehlungen in `WeekRewriteCard` als Bullet-Liste mit `list-disc list-inside` — nutzt volle Breite, keine Abschneidung
- Pill-Badges bleiben kompakt mit ausreichend `px-2 py-0.5`
- Text-Größen `text-xs`/`text-sm` (12-14px) — knapp aber lesbar im dichten Chat-Kontext

## 3. Touch Targets

- [x] "Übernehmen" Button: Nordlig DS `<Button variant="primary" size="sm">` — `size="sm"` rendert >= 44px Höhe per DS-Token
- [x] "Rückgängig" Button (PlanSuggestionCard): DS `<Button variant="ghost" size="sm">` — ebenfalls >= 44px
- [x] Buttons nebeneinander mit `gap-2` (8px) — kein versehentliches Tap-Risiko

## 4. Weissraum & Spacing

- [x] Container-Padding: `p-3` (12px) — angemessen für eingebettete Chat-Karten innerhalb einer Bubble
- [x] Sektionen-Abstand: `space-y-2` (8px) zwischen Header/Description/Preview/Reason/Actions
- [x] Kein Card-on-Card Schatten — Karten nutzen nur `border` ohne `shadow`, innere Segment-Box `bg-[var(--color-bg-subtle)]` mit `border-subtle`
- [x] Segment-Liste in eigener subtler Sub-Box — visuell abgegrenzt, aber ohne Schatten-Verdoppelung

## 5. Gesamtbewertung

**Verdict:** PASS

**Anmerkungen:**
Die neuen Karten reihen sich stilistisch nahtlos in das bestehende Chat-System ein
(siehe `PlanSuggestionCard` und `PlanCreatedCard`). Die Segment-Vorschau folgt dem
gleichen visuellen Muster wie der Wochenplan-Detail-Bereich (Label links,
Werte rechts, kompakte vertikale Liste). Quality Gates: ESLint 0, Prettier,
TSC, Vitest 189, Ruff, Mypy, Pytest 1315 — alle grün.
