# 📚 Documentation — Training Analyzer / minsaga

> **Stand: 2026-04-27** — Neu strukturiert. Single Source of Truth ist `PRD.md`.

---

## 🎯 Wo finde ich was?

### Wenn du …

| … wissen willst, **was** minsaga ist und **was** wir bauen | → [`PRD.md`](PRD.md) |
|---|---|
| … verstehen willst, **wie** wir bauen (Code-Standards, Layout-Regeln) | → [`engineering/`](engineering/) |
| … die **Marke / visuelle Sprache** brauchst | → [`design/BRAND_STYLE_GUIDE.md`](design/BRAND_STYLE_GUIDE.md) |
| … ins **Domain-Modell** schauen willst (Entities, Felder) | → [`reference/DOMAIN_MODEL.md`](reference/DOMAIN_MODEL.md) |
| … die App **aufsetzen oder deployen** willst | → [`operations/`](operations/) |
| … alte Konzepte zur **Nachvollziehbarkeit** brauchst | → [`archive/`](archive/) |

---

## 🗂 Struktur

```
docs/
├── PRD.md                   ← Single Source of Truth (Produkt + Features)
├── README.md                ← du bist hier
│
├── reference/               Tiefendokumentation, vom PRD verlinkt
│   ├── DOMAIN_MODEL.md
│   ├── TRAINING_CONTEXT.md
│   ├── CSV_FORMAT_EXAMPLES.md
│   ├── FIT_IMPORT_NOTES.md
│   └── trainingsplan-vorlage.yaml
│
├── design/                  Visuelle Sprache (kein Code)
│   └── BRAND_STYLE_GUIDE.md
│
├── engineering/             Wie wir bauen (Standards, Regeln)
│   ├── PROJEKT_REGELN.md       ← Frontend / Backend / Testing
│   ├── CLEAN_CODE.md           ← Clean Code & SOLID
│   ├── DESIGN_REVIEW.md        ← UX-Review-Checkliste
│   └── FIGMA_RULES.md          ← Figma-Workflow-Regeln
│
├── operations/              Setup, Deploy, Workflow
│   ├── DEVELOPMENT.md
│   ├── QUICKSTART.md
│   ├── CONTRIBUTION_GUIDE.md
│   └── CHANGELOG.md
│
└── archive/                 Historische Konzepte (superseded)
    ├── REDESIGN_KONZEPT.md          → fließt in PRD §3, §4
    ├── DASHBOARD_LAYOUT_PROPOSAL.md → fließt in PRD §4.1
    ├── GOAL_READINESS_CONCEPT.md    → fließt in PRD §5.1
    ├── AI_ANALYSIS_INTEGRATION.md   → fließt in PRD §5.3
    ├── FITNESS_LEVEL_SYSTEM_V2.md   → SUPERSEDED (siehe PRD §7)
    ├── FIGMA_MAKE_BRIEFING.md       → SUPERSEDED durch PRD + Brand Style Guide
    ├── MINSAGA_TOKENS.md            → Tokens leben in Figma + NDS
    └── NORDLIG_DESIGN_SYSTEM.md     → NDS hat eigenes Repo
```

---

## 🌳 Externe Sources of Truth

Nicht alles wohnt in diesem Repo:

| Was | Wo |
|---|---|
| **Komponenten** (Buttons, Cards, Nav-Bars, States) | [Figma File `vfjxFkAugXZCZPRVyADQRY`](https://www.figma.com/design/vfjxFkAugXZCZPRVyADQRY/) + Storybook im NDS |
| **Design Tokens** (Farben, Radii, Spacing) | Figma Variables (live) + [`@nordlig/components`](https://github.com/NCS23/nordlig-design-system) |
| **Nordlig Design System (Code + Storybook)** | [NCS23/nordlig-design-system](https://github.com/NCS23/nordlig-design-system) |
| **Issues, Stories, Epics** | [GitHub Project Board](https://github.com/orgs/NCS23/projects/1) |

Im PRD und in den `design/`/`engineering/`-Docs wird **verlinkt**, nicht dupliziert.

---

## 🔄 Workflow

1. **Pre-Code Pflichtlektüre** (siehe Root-`CLAUDE.md`):
   - `docs/PRD.md` → Was ist das Produkt
   - `docs/engineering/PROJEKT_REGELN.md` → Wie wird gebaut
   - `docs/engineering/CLEAN_CODE.md` → Clean Code & SOLID
   - `docs/engineering/DESIGN_REVIEW.md` → UX-Review

2. **Bei UI-Arbeit zusätzlich:** Figma File + Storybook prüfen.

3. **Bei Domain-Fragen:** `docs/reference/DOMAIN_MODEL.md`.

4. **Konzeptarbeit (neue Features, Refactor):** Direkt im PRD aufnehmen,
   nicht parallele Konzept-Docs anlegen.

---

## 📋 Aktueller Status

| Bereich | Status |
|---|---|
| PRD-Skelett | ✅ angelegt (v0) |
| Interview-Sessions S1–S3 | ⏳ ausstehend |
| Code-Audit für Bestand-Mapping (PRD §6) | ⏳ ausstehend |
| Figma-Audit & Reorganisation | ⏳ in Arbeit |
| Tab-Namen final | ⏳ Vorschläge stehen, im Interview validieren |

---

## ⚠️ Was hier NICHT mehr stehen sollte

Nicht im `docs/`-Verzeichnis ablegen:

- ❌ Komponenten-Specs (gehören nach Figma + Storybook)
- ❌ Token-Tabellen (gehören nach Figma Variables + NDS)
- ❌ Wireframes als ASCII-Mockups (zu wartungsintensiv — Figma-Link reicht)
- ❌ Parallele Konzept-Drafts neben dem PRD (führt zu Drift, deshalb sind wir gerade hier)

Wenn ein neues Konzept entsteht: **erst ein Abschnitt im PRD**, dann ggf. eine Reference-/Design-Doku, wenn die Tiefe nicht reinpasst.
