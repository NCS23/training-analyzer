# UX & Design Review — Training Analyzer

Dieses Dokument ist die verbindliche Checkliste fuer den UX & Design Review.
Jedes Feature wird VOR dem Commit gegen diese Kriterien geprueft.

Die Grundlage sind die **5 Saeulen** und **7 Gestaltungskriterien** des
Nordlig Design Systems (DESIGN_PRINCIPLES.md im DS-Repo).

---

## Nordlig-Heuristik — 5 Fragen

Bei JEDER Designentscheidung diese 5 Fragen beantworten:

1. **Ist es noetig?** — Kann ich es entfernen ohne Funktion zu verlieren?
2. **Ist es ausgewogen?** — Stimmen Proportionen, Spacing, Farbverteilung?
3. **Ist es einladend?** — Warm, zugaenglich, genug Luft zum Atmen?
4. **Ist es fuer alle?** — Touch, Tastatur, Screenreader, jedes Geraet?
5. **Wird es bestehen?** — Zeitlos oder Trend? Sieht es in 5 Jahren noch gut aus?

---

## Mobile-First Checkliste

**Jedes Feature MUSS auf iPhone SE (375×667px) geprueft werden.**

- [ ] Layout funktioniert auf 375px Breite ohne horizontales Scrollen
- [ ] Text ist lesbar ohne Zoomen (min. 16px Body)
- [ ] Touch-Targets sind mindestens 44×44px
- [ ] Formulare: Labels ueber Feldern, korrekte Input-Types
- [ ] Navigation erreichbar (Bottom Bar oder Hamburger)
- [ ] Keine Hover-Only Interaktionen
- [ ] Modals/Sheets sind auf Mobile bedienbar (volle Breite, swipe-to-close)
- [ ] Tabellen scrollen horizontal mit Sticky-Spalte bei Bedarf
- [ ] Karten (Maps) haben Touch-Gesten (Pinch-Zoom, Pan)
- [ ] Charts skalieren lesbar (ggf. vereinfachte Mobile-Variante)

---

## 7 Gestaltungskriterien

### A. Weissraum (Funktionalismus + Lagom)

- [ ] Genuegend Luft zwischen Elementen — nichts wirkt gedraengt
- [ ] Mindestens 30% Weissraumanteil auf jeder Seite
- [ ] Header-Hoehe >= 56px (Mobile: >= 48px)
- [ ] Cards und Sections haben ausreichend Padding
- [ ] Kein visuelles "Gedraenge" — bei Zweifel: mehr Platz

### B. Farbe (Hygge + Demokratisk)

- [ ] 70-20-10 Regel: 70% neutral, 20% Primaer, 10% Akzent
- [ ] Warme Toene wo moeglich (Nordlig-Prinzip)
- [ ] Kontrast >= 4.5:1 fuer Text (WCAG AA)
- [ ] Kontrast >= 3:1 fuer grosse Texte und Icons
- [ ] Farbe ist NIEMALS einziger Informationstraeger (+ Icon/Text/Form)
- [ ] Training-Farben konsistent: Quality=Lila, Recovery=Gruen, Longrun=Blau, Kraft=Orange
- [ ] HR-Zonen konsistent: Zone1=Gruen, Zone2=Gelb, Zone3=Rot

### C. Typografie (Lagom + Tidloeshet)

- [ ] Maximal 3 Schriftgewichte pro Seite
- [ ] Klare Hierarchie: Heading > Subheading > Body > Small
- [ ] Body-Text >= 16px (Mobile: kein kleinerer Text fuer Kerninfo)
- [ ] Zeilenhoehe 1.4-1.6 fuer Fliesstext
- [ ] Zahlen/Metriken gut lesbar (evt. tabellarische Ziffern)

### D. Form (Funktionalismus + Hygge)

- [ ] Weiche Radii (4-16px) — keine scharfen Ecken, keine Pillenform
- [ ] Subtile Schatten (diffus, 1-2 Ebenen) — nicht hart oder uebertrieben
- [ ] 1px Borders wo noetig (nicht 2px+)
- [ ] Konsistente Radii innerhalb einer Seite
- [ ] Icons einheitlich (Lucide React, gleiche Groesse pro Kontext)

### E. Bewegung (Lagom)

- [ ] Animationen sind subtil und funktional
- [ ] Micro-Interactions: 150ms (Color, Opacity)
- [ ] Standard UI: 200ms (Accordion, Hover)
- [ ] Overlays: 300ms (Modal, Sheet, Toast)
- [ ] `prefers-reduced-motion` wird respektiert
- [ ] Keine Animationen die vom Inhalt ablenken

### F. Informationsdichte (Lagom + Demokratisk)

- [ ] Progressive Disclosure: Nicht alles auf einmal zeigen
- [ ] Dashboard: Max 4-6 Metriken auf einen Blick
- [ ] Session Detail: Sektionen klar getrennt, scrollbar
- [ ] Tabellen: Max 5-7 Spalten sichtbar (Rest horizontal scrollbar)
- [ ] Kein "Feature-Dumping" — jede Information hat ihren Platz

### G. Ehrlichkeit (Funktionalismus + Demokratisk)

- [ ] Klare Zustaende: Loading, Empty, Error, Success
- [ ] Loading: Skeleton statt Spinner wo moeglich
- [ ] Empty State: Hilfreicher Text + Handlungsaufforderung
- [ ] Fehlermeldungen: Menschlich, konkret, mit Loesung
- [ ] Bestaetigungen: Kurz, positiv, mit naechstem Schritt
- [ ] Kein UI das Funktionalitaet vortaeuscht die nicht existiert

---

## Accessibility (Demokratisk)

- [ ] **Tastatur:** Alle interaktiven Elemente per Tab erreichbar
- [ ] **Focus-Ring:** Sichtbar, 2px, ring-offset-1, `focus-visible`
- [ ] **ARIA:** Labels auf Icons-only Buttons, Landmarks, Live-Regions
- [ ] **Screenreader:** Sinnvolle Lesereihenfolge, keine rein visuellen Infos
- [ ] **Kontrast:** WCAG AA Minimum (4.5:1 Text, 3:1 UI-Elemente)
- [ ] **Touch:** Minimum 44×44px, ausreichend Abstand zwischen Targets
- [ ] **Reduced Motion:** Animationen reduzieren bei Praeferenz

---

## Training-spezifische Pruefpunkte

### Session Detail View
- [ ] Metriken-Grid: Auf Mobile 2×2 statt 4×1
- [ ] HR-Zonen Chart: Lesbar auf 375px Breite
- [ ] Lap-Tabelle: Horizontal scrollbar, Lap-Nr sticky
- [ ] Karte: Volle Breite auf Mobile, Touch-bedienbar
- [ ] Soll/Ist-Vergleich: Abweichungen farblich markiert

### Session List
- [ ] Cards statt Tabelle auf Mobile
- [ ] ActivityType-Badge sichtbar (Icon + Farbe)
- [ ] Wichtigste Metrik sofort erkennbar (Dauer, Distanz/Tonnage)
- [ ] Pull-to-Refresh auf Mobile (optional)

### Dashboard
- [ ] StatCards: 2×2 Grid auf Mobile, 4×1 auf Desktop
- [ ] Letzte Sessions: Card-Layout, nicht Tabelle
- [ ] Insights/Warnungen: Prominent, nicht versteckt
- [ ] Naechste Einheit: Oben, gut sichtbar

### Upload/Erfassung
- [ ] Grosse Drop-Zone (min. 120px Hoehe)
- [ ] Klarer Fortschritt: Upload → Parsing → Review → Speichern
- [ ] Kraft-Erfassung: Uebung fuer Uebung, gut auf Mobile bedienbar
- [ ] Fehler bei invaliden Dateien: Menschliche Fehlermeldung

---

## Review-Bewertung

| Bewertung | Bedeutung | Aktion |
|-----------|-----------|--------|
| **Kritisch** | Feature nicht nutzbar oder unzugaenglich | MUSS vor Commit gefixt werden |
| **Schwerwiegend** | Deutliche UX-Probleme, Design-Verletzung | MUSS vor Commit gefixt werden |
| **Leicht** | Suboptimal aber funktional | SOLLTE gefixt werden, darf committed werden |
| **Hinweis** | Verbesserungsvorschlag | Optional, als Issue erfassen |

---

## Review-Dokumentation

Nach dem Review im Commit oder Issue dokumentieren:

```
UX Review: [Feature Name]
- Geprueft auf: iPhone SE (375px), Desktop (1280px)
- Kriterien: A✅ B✅ C✅ D✅ E✅ F✅ G✅
- Mobile-First: ✅
- Accessibility: ✅
- Findings: [keine / Liste]
```
