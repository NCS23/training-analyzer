# Figma Make Briefing — Training Analyzer Redesign

> ⚠️ **ARCHIVIERT — 2026-04-27**
>
> Dieses Briefing war für eine externe Figma-Make-Session gedacht.
> Source of Truth ist jetzt das **PRD** + **`design/BRAND_STYLE_GUIDE.md`** + die Figma-Datei selbst.
> Hier verbleibend als historische Referenz.

## Projektkontext

Du gestaltest das Redesign einer **Trainings-Analyse-App für ambitionierte Läufer**. Der Nutzer ist ein Halbmarathon-Läufer mit dem Ziel Sub-2h. Die App analysiert Trainingsdaten (GPS, Herzfrequenz, Pace), erstellt Trainingspläne und bietet KI-gestützte Coaching-Tipps.

**Sprache der App: Deutsch** — Alle Labels, Menüpunkte und Texte auf Deutsch.

---

## Design-Philosophie: Nordlig Design System

Das Design folgt **skandinavischen Gestaltungsprinzipien** — übersetzt in digitale Interfaces.

### 5 Säulen

1. **Funktionalismus** — Form follows Function. Kein visueller Ballast. Jedes Element hat einen Zweck.
2. **Lagom** (schwedisch: "genau das richtige Maß") — Balance ohne Überfluss. Nicht zu viel, nicht zu wenig.
3. **Hygge** (dänisch: "Behaglichkeit") — Wärme und Einladung. Die App soll sich anfühlen wie ein gemütlicher Ort, nicht wie ein Dashboard.
4. **Demokratisk Design** — Für alle. Barrierefreiheit ist kein Feature, sondern Grundlage. WCAG 2.1 AA minimum.
5. **Tidløshet** (Zeitlosigkeit) — Kein Trend-Chasing. Das Design soll in 5 Jahren noch gut aussehen.

### Design-Heuristik (5 Fragen an jedes Element)

- Ist es **notwendig**? (Funktionalismus)
- Ist es **ausgewogen**? (Lagom)
- Ist es **einladend**? (Hygge)
- Ist es **für alle**? (Demokratisk)
- Wird es **bestehen**? (Tidløshet)

---

## Design-Richtung: Emotionaler & Persönlicher

Das aktuelle Design ist funktional, aber zu **dashboardig** und **kalt**. Das Redesign soll:

- **Emotionaler** sein — Der Nutzer soll sich motiviert und verstanden fühlen
- **Persönlicher** sein — Die App kennt den Nutzer, seine Ziele, seinen Fortschritt
- **Erzählerischer** sein — Daten als Geschichte präsentieren, nicht als Tabelle
- **Wärmer** sein — Hygge stärker betonen, weniger "Analytics-Tool", mehr "persönlicher Coach"

### Konkrete Designanweisungen

- **Begrüßung mit Name** — "Guten Morgen, Nils" statt generischer Headlines
- **Fortschritt als Narrativ** — "Du bist auf Kurs für dein Sub-2h Ziel" statt nackter Zahlen
- **Emotionale Datenpräsentation** — Trends mit ermutigenden Texten begleiten
- **Großzügiger Weißraum** — 30-40% der Fläche frei lassen, Inhalte atmen lassen
- **Weiche Formen** — Abgerundete Ecken (8-12px Cards, 6-8px Buttons), sanfte Schatten
- **Illustrative Akzente** — Subtile Icons oder Illustrationen die Emotionen transportieren
- **Kein Daten-Overload** — Dashboard zeigt nur das Wichtigste, Details auf Unterseiten

---

## Farbpalette

### Primärfarben (Sky-Blau — Klarheit, Weite, Himmel)
| Token | Hex | Verwendung |
|-------|-----|------------|
| Primary | `#0369a1` | Buttons, Links, aktive Elemente |
| Primary Hover | `#075985` | Hover-States |
| Primary Active | `#0c4a6e` | Pressed-States |
| Primary Subtle BG | `#f0f9ff` | Aktive Nav-Items, leichte Hervorhebung |

### Sekundärfarben (Indigo — Tiefe, Akzent)
| Token | Hex | Verwendung |
|-------|-----|------------|
| Secondary | `#6366f1` | Sekundäre Akzente, Charts |
| Secondary Light | `#e0e7ff` | Subtle Backgrounds |

### Status-Farben
| Status | Farbe | Hex | Verwendung |
|--------|-------|-----|------------|
| Erfolg | Emerald | `#047857` | Positive Trends, Ziel erreicht |
| Warnung | Amber | `#b45309` | Aufpassen, leichte Abweichung |
| Fehler | Red | `#991b1b` | Fehler, kritische Warnung |
| Info | Blue | `#1e40af` | Hinweise, neutrale Info |

### Neutrale Farben (Slate — warmes Grau)
| Token | Hex | Verwendung |
|-------|-----|------------|
| Text Base | `#0f172a` | Haupttext (nie reines Schwarz) |
| Text Muted | `#475569` | Sekundärtext, Labels |
| Text Disabled | `#94a3b8` | Deaktivierte Elemente |
| Background Paper | `#f8fafc` | Seitenhintergrund (warmes Weiß) |
| Background Elevated | `#ffffff` | Cards, Panels |
| Background Surface | `#f1f5f9` | Hover, Tabellenstreifen |
| Background Base | `#e2e8f0` | App-Chrome, Sidebar-BG |
| Border Default | `#cbd5e1` | Standard-Rahmen |
| Border Muted | `#e2e8f0` | Dezente Trennlinien |

### Farbverteilung
- **70%** Neutrale Töne (Slate-Palette)
- **20%** Sekundärtöne (Surfaces, Borders)
- **10%** Akzentfarben (Primary, Status)

---

## Typografie

| Verwendung | Font | Gewicht | Größe |
|------------|------|---------|-------|
| H1 | Inter | Semibold (600) | 36px / LH 45px |
| H2 | Inter | Semibold (600) | 30px / LH 36px |
| H3 | Inter | Medium (500) | 24px / LH 30px |
| H4 | Inter | Medium (500) | 20px / LH 30px |
| Body | Inter | Regular (400) | 16px / LH 24px |
| Body Small | Inter | Regular (400) | 14px / LH 20px |
| Caption | Inter | Regular (400) | 12px / LH 18px |
| Label | Inter | Medium (500) | 14px / LH 20px |
| Nav Item | Inter | Regular/Medium | 13.5px |

**Regeln:**
- Max 3 Gewichte pro Screen
- Body-Text nie unter 16px auf Desktop, 14px auf Mobile
- Überschriften näher am Content darunter als am Element darüber

---

## Spacing & Layout

- **Basis: 8px Grid**
- Container-Padding: 16px (Mobile), 24-32px (Desktop)
- Content max-width: **1024px** (max-w-5xl)
- Card-Padding: 16-20px
- Section-Abstand: 24-32px
- Zusammengehörige Elemente: 8-16px
- Getrennte Sektionen: 32-48px
- **Weißraum: 30-40% der Gesamtfläche**

---

## Komponenten-Stil

- **Cards:** 12px Border-Radius, 1px Border (`#e2e8f0`), sanfter Schatten (`0 2px 8px rgba(0,0,0,0.06)`)
- **Buttons:** 8px Border-Radius, 44px Mindesthöhe (Touch-Target)
- **Inputs:** 8px Border-Radius, 44px Höhe, 1px Border
- **Badges/Pills:** `border-radius: 9999px`, kompakt
- **Icons:** Lucide Icon Set, 1.5-2px Stroke, abgerundete Enden
- **Shadows:** Weich und diffus, niedrige Opazität — nie harte Schatten
- **KEINE Cards in Cards mit Schatten** — verschachtelte Cards flach (ohne Schatten)

---

## Auftrag 1: Dashboard + App-Rahmen

### Was zu gestalten ist

#### A) App-Rahmen (Shell)

**Desktop (≥1024px):**
- **Linke Sidebar** (224px breit), fixiert
- Logo + App-Name oben
- Navigationsitems vertikal:
  - Dashboard (LayoutDashboard Icon)
  - Sessions (Dumbbell Icon)
  - Analyse (TrendingUp Icon)
  - KI-Chat (Bot Icon)
  - Plan (aufklappbar mit Unterpunkten: Woche, Ziele, Programme, Vorlagen, Übungen)
  - Profil (User Icon)
- Aktives Item: Primärfarbe, vertikaler Akzentstreifen rechts (3px)
- User-Info unten: Avatar-Kreis mit Initialen + Name + Logout
- Sidebar-BG: Elevated White (`#ffffff`), rechter Border

**Mobile (<1024px):**
- **Top Bar** (64px Höhe): Logo + App-Name, fixiert oben
- **Bottom Navigation** (fixiert unten): 5 Hauptitems als Icon + Label
  - Dashboard, Sessions, Analyse, Chat, Profil
  - Aktives Item: Primärfarbe
  - Safe-Area-Padding unten beachten (iOS)

**Transitions:**
- Sidebar verschwindet unter 1024px, Bottom Nav erscheint
- Content-Bereich passt sich an (kein Sidebar-Offset auf Mobile)

---

#### B) Dashboard-Screen

Das Dashboard ist die **emotionale Heimat** der App. Es soll motivieren, nicht überfordern.

**Header-Bereich:**
- Persönliche Begrüßung: "Guten Morgen, Nils" (zeitabhängig)
- Motivierender Untertitel: z.B. "Woche 12 deiner Sub-2h Vorbereitung" oder "3 Einheiten diese Woche — du bist auf Kurs"
- Aktuelles Datum

**Primäre Metriken (Hero-Bereich):**
Wenige, große Zahlen — emotional aufgeladen:
- **Wochenziel-Fortschritt** — z.B. Ring/Progress-Circle "4 von 5 Einheiten" mit ermutigender Farbe
- **Wochenkilometer** — z.B. "34,2 km" mit Trend-Pfeil ↑ und Vergleich zur Vorwoche
- **Formkurve** — Fitness/Fatigue Balance als einfache Visualisierung

**Nächste Einheit (prominent):**
- Card mit dem nächsten geplanten Training
- Typ (z.B. "Intervall-Training"), geplante Dauer, Intensität
- Ein einladender CTA: "Training starten" oder "Details ansehen"

**Letzte Aktivität:**
- Kompakte Darstellung der letzten 2-3 Trainings
- Datum, Typ, Distanz, Pace — als horizontale Mini-Cards oder Liste
- Trend/Stimmung: kleines Emoji oder Farb-Indikator

**Wochenübersicht:**
- Einfacher 7-Tage-Kalender (Mo-So) mit farbigen Dots für absolvierte Einheiten
- Geplante Einheiten als leere Kreise, absolvierte als gefüllte

**KI-Coaching-Tipp:**
- Eine kurze, persönliche Empfehlung vom KI-Coach
- z.B. "Dein Ruhepuls war diese Woche 2 Schläge höher. Achte auf ausreichend Schlaf."
- Karte mit Bot-Icon, warm gestaltet, nicht klinisch

---

### Designanforderungen

- **Mobile-First**: Zuerst 375px (iPhone SE) gestalten, dann 1024px+ Desktop
- **Zwei Frames liefern**: Mobile (375×812) und Desktop (1440×900)
- **Echte Daten verwenden**: Keine "Lorem Ipsum", sondern realistische Laufdaten
- **Emotionale Sprache**: Labels und Texte sollen warm und persönlich klingen
- **Weißraum**: Großzügig. Nicht alles vollpacken. Luft zum Atmen.
- **Farben nur aus der definierten Palette** — keine eigenen Farben erfinden
- **Touch-Targets**: Mindestens 44×44px für alle interaktiven Elemente

---

### Realistische Beispieldaten

```
Nutzer: Nils-Christian, 32 Jahre
Ziel: Halbmarathon Sub-2h (aktuell: 2:04:12)
Aktuelle Woche: KW 15, Woche 12 der Vorbereitung

Wochenziel: 5 Einheiten, 45 km
Bisher diese Woche: 3 Einheiten, 28,7 km

Letzte Sessions:
- So 06.04: Langer Lauf, 18,2 km, 5:42 min/km, Ø HF 148
- Fr 04.04: Intervalle, 10,4 km, 8×400m, Ø HF 168
- Mi 02.04: Lockerer Dauerlauf, 8,1 km, 6:15 min/km, Ø HF 138

Nächstes Training: Di 08.04, Tempodauerlauf, ~12 km, Ziel-Pace 5:30

Formkurve: Fitness steigt, Ermüdung moderat
Ruhepuls-Trend: 52 → 54 bpm (leicht erhöht)
```
