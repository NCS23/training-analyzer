# Figma-Regeln — minsaga / Nordlig DS

Verbindlich für alle Figma-Operationen via MCP. Kein Schreiben in Figma ohne diese Regeln gelesen zu haben.

---

## 1. Atomares Design — PFLICHT

**Immer an der Quelle ändern, nie am Symptom.**

| Node-Typ | Wann ändern |
|---|---|
| `COMPONENT` / `COMPONENT_SET` | Hier werden Änderungen gemacht |
| `INSTANCE` | Nur für kontextspezifische Overrides (z.B. Text-Content) |
| `FRAME` / Seiten-Layouts | Niemals direkt — nur über Komponenten-Änderungen |

**Vor jeder Änderung:**
1. Node-Typ prüfen: `COMPONENT` oder `INSTANCE`?
2. Wenn `INSTANCE` → die Quell-Komponente suchen und dort ändern
3. Instanzen auf Frames (MobileSite, etc.) erben automatisch — nie manuell patchen

---

## 2. Varianten-Auswahl

**Die richtige Variante wählen — niemals Größen oder Eigenschaften manuell überschreiben.**

- ❌ Avatar sm resizen auf 44px → ✅ Avatar lg verwenden (44px ist lg)
- ❌ `variant.resize(44, 44)` → ✅ `instance.setProperties({ Size: 'lg' })`
- ❌ Hardcodierte Werte setzen → ✅ Token-gebundene Eigenschaften nutzen

**Größenvarianten haben Bedeutung:**
- `sm` / `md` → nicht-interaktive Kontexte (Avatar neben Text, Kommentarliste)
- `lg` → interaktive Standalone-Elemente (min. 44×44px Touch-Target)
- `xl` → prominente Darstellungen (Profil-Seite, Hero)

---

## 3. Token-Architektur (4 Ebenen)

**NIEMALS Ebenen überspringen oder L1/L2 direkt in Komponenten binden.**

```
L1 · Base          → Rohe Werte (stone/200, slate/300, 8px, ...)
L2 · Global        → Globale Aliasse (neutral-1/200, spacing/sm, ...)
L3 · Semantic      → Bedeutung (border/neutral, text/secondary, ...)
L4 · Components    → Komponenten-spezifisch (avatar/border, bottomNav/bg, ...)
```

- Komponenten-Nodes binden auf **L4** (oder L3 wenn kein L4 existiert)
- L4 aliast auf L3, L3 auf L2, L2 auf L1 — niemals Sprünge
- Neue Tokens immer vollständig durch alle Ebenen anlegen

**Minsaga Farb-Regel:**
- `neutral-1` (slate) → Text, strukturelle Borders (Nav, Card, Divider)
- `neutral-2` (stone) → Backgrounds, Surfaces, Komponentenrahmen (Avatar-Ring)

---

## 4. Schriftarten

**Nur diese zwei Familien — keine anderen.**

| Rolle | Font | Gewichte |
|---|---|---|
| Display / Headings | Fraunces | Bold, Semibold |
| UI / Body / Labels | DM Sans | Regular, Medium, SemiBold |

- ❌ Inter → ✅ DM Sans
- ❌ ExtraBold (4. Gewicht) → ✅ max. 3 Gewichte: Regular, Medium, SemiBold
- Immer zuerst `await figma.loadFontAsync(...)` vor Text-Änderungen

---

## 5. Touch-Targets

- **Minimum 44×44px** für alle interaktiven Elemente
- Visuell kleiner ist OK — dann muss der **Wrapper** (Button, Touchable) 44×44px sein
- Direkt interaktive Komponenten (standalone klickbar) → `lg`-Variante oder größer

---

## 6. Schatten-Richtung

- **Header** → Schatten nach unten (y=+2)
- **BottomNav** → Schatten nach oben (y=-2)
- Für entgegengesetzte Richtungen separate Token-Kette anlegen (kein Negieren via Aliasing möglich)

---

## 7. Arbeitsablauf vor jeder Figma-Änderung

```
1. Node-Typ bestimmen (COMPONENT / INSTANCE / FRAME)
2. Bei INSTANCE → Quell-Komponente finden (findOne mit type === 'COMPONENT')
3. Passende Variante wählen (nicht manuell resizen/patchen)
4. Token-Ebene prüfen: L4 für Komponenten, L3 für semantische Bedeutung
5. Font laden bevor Text-Nodes geändert werden
6. Nach Änderung: kurz verifizieren (Größen, Farben, Token-Bindungen)
```

---

## 8. Seiten-Struktur (NordligDesignSystem Figma-Datei)

| Seite | Inhalt |
|---|---|
| `minsaga` | Minsaga-Komponenten (Avatar, BottomNav, AppHeader, MobileSite, ...) |
| `Atoms` | Nordlig DS Basis-Komponenten |
| `Molecules` | Nordlig DS zusammengesetzte Komponenten |
| `Organisms` | Nordlig DS komplexe Komponenten |
| `Token Reference` | Token-Übersicht |

**Immer `await figma.setCurrentPageAsync(page)` bevor auf einer Seite gesucht wird.**

---

## Referenzen

- [BRAND_STYLE_GUIDE.md](BRAND_STYLE_GUIDE.md) — Farben, Typografie, Neutral-Regeln
- [DESIGN_REVIEW.md](DESIGN_REVIEW.md) — UX-Review-Checkliste
- Nordlig DS Storybook: http://storybook.89.167.78.223.sslip.io
- Figma-Datei: `vfjxFkAugXZCZPRVyADQRY` (NordligDesignSystem)
