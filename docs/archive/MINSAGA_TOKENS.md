# Minsaga Token-System

> ⚠️ **ARCHIVIERT — 2026-04-27**
>
> Tokens leben in **Figma Variables** (File `vfjxFkAugXZCZPRVyADQRY`) und im **NDS-Repo / Storybook**
> ([NCS23/nordlig-design-system](https://github.com/NCS23/nordlig-design-system)).
> Diese Markdown-Spiegelung ist redundant und wird nicht mehr gepflegt.
> Hier verbleibend, bis Verweise im Code/Doc bereinigt sind — danach löschbar.

> **Original-Status:** Produktiv | 2026-04-22
> **Referenz:** [nordlig-design-system/docs/TOKEN_GUIDELINES.md](https://github.com/NCS23/nordlig-design-system/blob/main/docs/TOKEN_GUIDELINES.md)
> **Gilt für:** Training-Analyzer (Minsaga-App)

---

## 0. Collection-Architektur (aktuell)

Seit 2026-04-22 ist die Figma-Token-Struktur auf **5 Domänen-Collections** konsolidiert:

| Collection | Modi | Tokens | Zweck |
|---|---|---|---|
| `Color` | light, dark | 1233 | Alle Farb-Tokens (L1-L4) |
| `Typography` | default | 417 | Fonts, Sizes, Line-Heights, Letter-Spacings, Weights |
| `Spacing` | default | 466 | Padding, Gap, Margin, Layout-Spacing |
| `Sizing` | default | 442 | Heights, Widths, Icon-Sizes, Border-Widths |
| `Radius` | default | 121 | Corner-Radii |

**Die Unterscheidung "generisch vs. Minsaga-spezifisch" passiert über die Schichten (L1 vs L2/L3/L4)**, nicht über Collection-Suffixe. Die früheren `· Core` / `· Minsaga`-Trennung wurde aufgelöst, weil sie in der Praxis mehr Verwirrung als Klarheit geschaffen hat (Farben ARE Identität, es gibt keinen "echten generischen Core").

---

## 1. Zweck des Dokuments

Dieses Dokument beschreibt die **Minsaga-spezifischen Token-Ergänzungen** auf Basis des Nordlig Design Systems. Alle Architektur-Regeln, Naming-Konventionen und Schichten-Prinzipien gelten wie im NDS dokumentiert — dieses Dokument erklärt nur die produktspezifischen Abweichungen und Ergänzungen.

---

## 2. Multi-Product-Strategie

Das NDS ist als **strukturelles Framework** konzipiert. Jedes Produkt erbt die Architektur (4-Layer-Modell, Naming, Rollen) und füllt die **produkt-identitätsstiftenden Werte** selbst aus.

### Aktueller Zustand (2026-04-22)

Minsaga ist das **einzige aktive Produkt**. Die Figma-Datei enthält das **Minsaga-Token-System** in 5 Domänen-Collections (siehe oben).

**Verteilung innerhalb einer Collection:**
- **L1** = Primitives (z.B. `L1 · Base/sky/500`, `L1 · Base/fraunces`)
- **L2** = Global (z.B. `L2 · Global/brand-1/500`, `L2 · Global/size/md`)
- **L3** = Semantic Roles (z.B. `L3 · Semantic/bg/primary`, `L3 · Semantic/body/size`)
- **L4** = Components (z.B. `L4 · Components/button/primary/bg`)

### Wenn ein zweites Produkt kommt

Zwei Wege, abhängig davon wie nah das neue Produkt an Minsaga ist:

1. **Sehr ähnlich** (gleiche Design-DNA, andere Farben) → Modes in bestehender Collection erweitern (z.B. `Color` bekommt zusätzliche Modes `ProductX-Light`, `ProductX-Dark`). Skaliert bis ~3-5 Produkte.
2. **Signifikant anders** (andere Fonts, andere Feel-Philosophie) → Figma-File duplizieren, zum eigenen Produkt-DS forken. Eigenständige Token-Sammlung.

### Komponenten-Propagation

- **Komponenten wie Button, Card, Badge, Input etc.** leben im NDS-Repo (`@nordlig/components`) und sind Code-Source-of-Truth. Minsaga importiert das NPM-Package.
- **Minsaga-spezifische Komponenten** (`GoalCard`, `BiometricsCard`, `LevelScoreCard`, `WeekOverviewCard`, `PlannedSessionCard`, `Logo`) leben im Minsaga-Repo (`training-analyzer/frontend`) und nutzen die NDS-Primitives.

---

## 3. Minsaga-Identitäts-Tokens

Die folgenden Tokens machen die **visuelle Identität von Minsaga** aus. Sie würden sich in einem anderen Produkt unterscheiden.

### 3.1 Brand Colors (L2)

| Token | L1-Alias | Rolle im Nordlicht-Gradient |
|---|---|---|
| `L2 · Global/brand-1` | sky | Links / primary |
| `L2 · Global/brand-2` | indigo | Rechts |
| `L2 · Global/brand-3` | cyan | Mitte / accent |

### 3.2 Accent Colors (L2)

| Token | L1-Alias | Funktion |
|---|---|---|
| `L2 · Global/accent-1` | emerald | Success |
| `L2 · Global/accent-2` | amber | Warning |
| `L2 · Global/accent-3` | rose | Error |
| `L2 · Global/accent-4` | fuchsia | **AI / Coach** (Minsaga-Alleinstellung) |
| `L2 · Global/accent-5` | slate | Info |

### 3.3 Neutral Colors (L2)

| Token | L1-Alias | Rolle |
|---|---|---|
| `L2 · Global/neutral-1` | slate | Strukturelle Trennung (Text, Borders) |
| `L2 · Global/neutral-2` | stone | Surface / Hintergrund (warme Untertöne) |

### 3.4 Nordlicht-Gradient (L3)

Der Markenkern-Gradient `sky → cyan → indigo`:

```
L3 · Semantic/gradient/brand/from  →  L2 brand-1/500
L3 · Semantic/gradient/brand/via   →  L2 brand-3/500
L3 · Semantic/gradient/brand/to    →  L2 brand-2/500
```

Plus Hover/Active/Soft-States (siehe Figma).

**Verwendung:** Nur auf primären CTAs, Progress-Ringen, aktiven Tab-Indikatoren, Level-Up-Feier. Nie als Hintergrundtapete.

### 3.5 AI-Coach-Farbe (geplant — noch nicht finalisiert)

Für AI-Coach-Elemente eigene Rolle geplant:

```
L3 · Semantic/bg/ai      →  L2 accent-4/50 (fuchsia-subtle)
L3 · Semantic/text/ai    →  L2 accent-4/700
L3 · Semantic/border/ai  →  L2 accent-4/200
```

### 3.6 Typography

Minsaga nutzt zwei Fonts, die per L3-Rolle gebunden sind:

| Rolle | `family` | `weight` |
|---|---|---|
| `display` | Fraunces | SemiBold |
| `heading` | Fraunces | SemiBold (h1-h4), Medium (h5-h6) |
| `title` | Fraunces | SemiBold |
| `subheading` | DM Sans | Medium |
| `body` | DM Sans | Regular |
| `label` | DM Sans | Medium |
| `caption` | DM Sans | Regular |
| `overline` | DM Sans | Medium + uppercase |
| `stat` | DM Sans | SemiBold |

Siehe NDS-Doku für die generischen Size/Line-Height/Letter-Spacing-Werte. Minsaga überschreibt nur das `family`-Property.

### 3.7 Card-Radius (Minsaga-Signatur)

Der auffällig große Card-Radius ist Minsaga-typisch:

```
L4 · Components/card/radius/outer  →  32px (Minsaga-spezifisch)
L4 · Components/card/radius/inner  →  8px  (Standardwert)
```

Andere Produkte könnten `card/radius/outer` auf 12-16px zurücksetzen.

### 3.8 Stat-Rolle (Minsaga-spezifisch)

Minsaga ist metrik-lastig (Puls, Distanz, Pace, Scores). Die `stat`-Rolle für numerische Displays:

```
L3 · Semantic/stat/xs/size   → 15
L3 · Semantic/stat/sm/size   → 20
L3 · Semantic/stat/md/size   → 26
L3 · Semantic/stat/lg/size   → 40
L3 · Semantic/stat/xl/size   → 56
```

Alle stat-Rollen: `family = DM Sans`, `weight = SemiBold`, `line-height` tight (1.1-1.2×), `letter-spacing` negativ für visuelle Dichte.

---

## 4. Minsaga-eigene Komponenten (L4)

Die folgenden Komponenten existieren nur in Minsaga, haben eigene L4-Tokens:

| Komponente | Zweck |
|---|---|
| `GoalCard` | Rennen-Ziel + Readiness-Ring |
| `LevelScoreCard` | Ausdauer/Kraft-Level mit Score |
| `BiometricsCard` | Ruhepuls, Schlaf, Energie Übersicht |
| `WeekOverviewCard` | Wochenplan mit Tagesdetail |
| `PlannedSessionCard` | Heutige Trainingseinheit mit CTA |
| `ReadinessCard` | Ziel-Vorbereitung-Zustand |
| `WeekDayButton` | Einzelner Tag im Wochenraster |
| `BiometricTile` | Einzelne Biometrie-Kachel |
| `StatBox` | Wiederverwendbarer Wert-Display (Label + Value + Unit) |
| `Logo` | minsaga-Wortmarke mit 3 Größen |

---

## 5. Abweichungen vom NDS-Default

| Bereich | NDS-Default | Minsaga-Override |
|---|---|---|
| Display-Font | system-ui / Inter | **Fraunces SemiBold** |
| Body-Font | system-ui / Inter | **DM Sans** |
| Card-Radius | 8-16px | **32px** |
| Primärer Accent-Tone | — | Nordlicht-Gradient (sky→cyan→indigo) |
| AI-Coach-Farbe | — | Fuchsia (accent-4) |

---

## 6. Referenzen

- [BRAND_STYLE_GUIDE.md](BRAND_STYLE_GUIDE.md) — Marken-Identität, Ton, Sprache
- [nordlig-design-system · TOKEN_GUIDELINES.md](https://github.com/NCS23/nordlig-design-system/blob/main/docs/TOKEN_GUIDELINES.md) — Architektur, Regeln
- [nordlig-design-system · TOKEN_HIERARCHY_REVIEW.md](https://github.com/NCS23/nordlig-design-system/blob/main/TOKEN_HIERARCHY_REVIEW.md) — aktuelle Hierarchie-Übersicht
- [FITNESS_LEVEL_SYSTEM_V2.md](FITNESS_LEVEL_SYSTEM_V2.md) — Level-Konzept (nutzt `stat`-Rolle)

---

## 7. Offene Punkte

- [ ] AI-Coach L3-Rollen anlegen (`bg/ai`, `text/ai`, `border/ai`)
- [ ] `teal/*` und `red/*` aus Color · Core entfernen (laut BRAND_STYLE_GUIDE)
- [ ] 137 pre-existing raw L4-Tokens in `Sizing · Core` (Button/Badge-Paddings) auf L3-Scale aliasen
- [ ] Typography-Rollen vollständig spezifizieren (`family/weight/line-height/letter-spacing` pro Rolle)
- [ ] Chart-Token-System für Recharts (`chart/series/1..7`, `chart/zone/1..5`)
