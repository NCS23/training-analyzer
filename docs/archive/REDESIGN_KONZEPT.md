# Training Analyzer — Redesign Konzept v2

> ⚠️ **ARCHIVIERT — 2026-04-27**
>
> Dieses Dokument war die ursprüngliche Diskussionsbasis für das Redesign.
> Inhalte fließen jetzt ins **PRD** ein → [`../PRD.md`](../PRD.md):
> - Navigationsstruktur (§3 — Tabs werden im Interview neu festgelegt)
> - Tab-Specs Heute / Training / Analyse / Plan / Sammlung (§4)
> - Querschnittskonzepte wie Ziel-Integration in Plan (§5)
>
> Hier verbleibend als historische Referenz für ursprüngliche Überlegungen.

> **Original-Status:** Entwurf — Diskussionsbasis für Epics & Stories
> **Erstellt:** 2026-04-06
> **Kontext:** Grundlegendes Redesign der App-Architektur, Navigation und Features

---

## Motivation

Die App ist aktuell ein **Daten-Verwaltungstool**: Sessions hochladen, Listen anzeigen, Charts rendern. Das Redesign macht sie zum **persönlichen Trainingsbegleiter**, der den Nutzer täglich abholt, proaktiv Erkenntnisse liefert und vom Nutzer her denkt — nicht von der Datenbank.

### Kernprobleme (Ist-Zustand)

1. **Dashboard ist unpersönlich** — zeigt Gesamtstatistiken (Anzahl Sessions, Gesamtdistanz) die keinen täglichen Wert haben
2. **Analyse ist generisch** — Charts (Pace-Trend, Volumen) ohne Einordnung oder Handlungsempfehlung
3. **Plan-Bereich überladen** — 7 Tabs (Woche, Ziele, Pacing, Programme, Vorlagen, Übungen, Routen) in einem Mega-Hub
4. **Ziele und Plan doppeln sich** — Ziel existiert separat, obwohl es immer zum Plan gehört
5. **Routen vermischen Geographie und Training** — Segmente, Pacing-Strategie, HR-Ziele auf Routen gespeichert (gehört in Vorlagen)
6. **Kein Soll/Ist-Vergleich** — geplante Session und tatsächliche Session sind nicht sichtbar verknüpft
7. **Kein Fitness-Score** — keine einfache Antwort auf "Wie fit bin ich?"
8. **KI-Chat als isolierter Menüpunkt** — statt kontextbezogen überall verfügbar

---

## Teil 1: Navigationsstruktur

### 1.1 Bottom Nav / Sidebar (5 Haupt-Tabs)

| # | Tab | Label | Icon-Vorschlag | Zweck | Nutzungshäufigkeit |
|---|-----|-------|----------------|-------|-------------------|
| 1 | **Heute** | "Heute" | Sonne/Kalender-Tag | Täglicher Begleiter — was steht an, wie geht's mir | Täglich |
| 2 | **Training** | "Training" | Laufschuh/Aktivität | Wochenplan + Sessions — planen und ausführen | Täglich |
| 3 | **Fortschritt** | "Fortschritt" | Trend-Pfeil/Chart | Fitness-Score + Insights + tiefe Analyse | Wöchentlich |
| 4 | **Plan** | "Plan" | Kalender/Ziel | Trainingsplan mit integriertem Ziel + Pacing | Gelegentlich |
| 5 | **Bibliothek** | "Bibliothek" | Buch/Sammlung | Routen, Vorlagen, Übungen | Gelegentlich |

### 1.2 Zusätzliche Navigation

**Profil & Einstellungen:**
- Zugang über Avatar/Icon oben rechts im Header
- Kein eigener Tab in Bottom Nav oder Sidebar
- Enthält: Athleten-Profil (HR-Zonen, Schwellenwerte), App-Einstellungen, Integrationen

**KI-Chat:**
- Floating Action Button (FAB) rechts unten
- Auf ALLEN Seiten sichtbar (Desktop UND Mobile — gleiches Pattern)
- Öffnet Chat als Overlay/Sheet
- Kontextbezogen: Weiß auf welcher Seite der Nutzer ist

### 1.3 URL-Struktur (React Router)

```
/heute                          → Heute (Dashboard)
/training                       → Wochenansicht (Default)
/training/sessions              → Alle Sessions (Liste mit Filter)
/training/sessions/new          → Session hochladen
/training/sessions/:id          → Session-Detail
/fortschritt                    → Fitness-Score + Insights (Default)
/fortschritt/trends             → Deep Dive Trends
/plan                           → Aktiver Plan (Default)
/plan/:planId                   → Plan-Detail
/plan/:planId/pacing            → Pacing-Rechner für diesen Plan
/bibliothek                     → Bibliothek-Übersicht (Default)
/bibliothek/routen              → Routen-Liste
/bibliothek/routen/new          → Route erstellen
/bibliothek/routen/:id          → Route-Detail
/bibliothek/vorlagen            → Vorlagen-Liste
/bibliothek/vorlagen/new        → Vorlage erstellen
/bibliothek/vorlagen/:id        → Vorlage bearbeiten
/bibliothek/uebungen            → Übungen-Liste
/bibliothek/uebungen/:id        → Übung-Detail
/profil                         → Athleten-Profil & Einstellungen
```

### 1.4 Desktop Sidebar Layout

```
┌──────────────────┬──────────────────────────────────────┐
│                  │  Breadcrumbs                [🤖] [👤]│
│  Heute           │                                      │
│  Training        │                                      │
│  Fortschritt     │         Seiteninhalt                 │
│  Plan            │                                      │
│  Bibliothek      │                                      │
│                  │                              [💬 KI] │
│──────────────────│                                      │
│  [👤] Profil     │                                      │
└──────────────────┴──────────────────────────────────────┘
```

### 1.5 Mobile Layout

```
┌─────────────────────────────────────────────┐
│  [Logo]                          [🤖] [👤]  │
├─────────────────────────────────────────────┤
│                                             │
│              Seiteninhalt                   │
│                                             │
│                                     [💬 KI] │
├─────────────────────────────────────────────┤
│ Heute │ Training │ Fortschr. │ Plan │ Bibl. │
└─────────────────────────────────────────────┘
```

---

## Teil 2: Heute (neues Dashboard)

### 2.1 Konzept

Persönlicher täglicher Begleiter. Zeigt dem Nutzer was er **heute** wissen muss. Keine abstrakten Gesamt-Statistiken. Alles ist kontextbezogen und eingeordnet.

### 2.2 Sektionen (von oben nach unten)

#### Sektion A: Begrüßung + Fitness-Score

**Begrüßung:**
- Tageszeit-abhängig: "Guten Morgen" / "Guten Tag" / "Guten Abend"
- Vorname des Nutzers (aus Profil)

**Fitness-Score:**
- Große Zahl (0-100)
- Trend-Indikator: ↑ steigend / → stabil / ↓ fallend (über letzte 2 Wochen)
- Ein Satz Kontext: "Deine Fitness steigt seit 3 Wochen stetig" / "Leichter Rückgang nach Regenerationswoche — normal"
- Form-Indikator daneben: Frisch / Normal / Ermüdet (Farbcode: grün / gelb / orange)

**Datenquelle:** Fitness-Score-Engine (siehe Teil 7)

#### Sektion B: Was steht heute an?

**Wenn Training geplant:**
- Card mit heutigem Training aus dem Wochenplan
- Trainingstyp + Icon (z.B. "Tempolauf" mit Lauf-Icon)
- Kurzbeschreibung: "8 km mit 4×1000m @ 4:15/km"
- Zugeordnete Route (falls vorhanden): "Alsterrunde" mit Minimap
- CTA-Button: "Training starten" → navigiert zu Upload-Seite mit vorausgefülltem Datum

**Wenn Ruhetag (laut Plan):**
- "Heute ist Regenerationstag. Gönn dir eine Pause."

**Wenn kein Plan aktiv:**
- "Kein Training geplant. Möchtest du eine Session hochladen?"

**Datenquelle:** Wochenplan-API (heutiger Tag), Route-API (falls verknüpft)

#### Sektion C: Letztes Training

**Card mit letzter absolvierter Session:**
- Datum + Typ ("Gestern: Tempolauf")
- 2-3 Kernmetriken je nach Typ:
  - Laufen: Distanz, Pace, HR
  - Kraft: Übungen, Tonnage, RPE
- **Einordnung** (nicht nur Zahlen):
  - "8s/km schneller als dein Durchschnitt für Tempoläufe"
  - "Puls 5 Schläge höher als sonst bei diesem Tempo — mögliche Ermüdung"
  - "Tonnage +12% vs. letzte Woche"
- Link: "Details ansehen" → Session-Detail

**Datenquelle:** Letzte Session + historischer Vergleich (Durchschnittswerte für gleichen Trainingstyp)

#### Sektion D: Wochenfortschritt

**Kompakte Wochenübersicht:**
- Fortschrittsbalken: "3 von 5 Sessions"
- Volumen: "34 von 50 km" (wenn Plan vorhanden)
- Oder ohne Plan: "Diese Woche: 3 Sessions, 34 km, 3:20h"
- 7-Tage-Leiste (Mo-So) mit Punkte/Icons pro Tag (erledigt / geplant / leer)

**Datenquelle:** Wochenplan-API + Sessions dieser Woche

#### Sektion E: Insights (1-2 Karten)

**Proaktiv generierte Hinweise:**
- Nur die 1-2 relevantesten, nicht alle gleichzeitig
- Rotieren täglich / bei neuen Daten
- Beispiele:
  - Warnung: "Du trainierst seit 3 Tagen über Plan-Intensität — Verletzungsrisiko steigt"
  - Trend: "Dein 5km-Pace hat sich um 15s/km verbessert seit Februar"
  - Plan: "Nächste Woche beginnt die Aufbauphase — Umfang steigt um 15%"
  - Balance: "80% deiner Läufe sind im GA1-Bereich — gute Verteilung!"
  - Erinnerung: "Letzte Kraft-Session war vor 8 Tagen — Zeit für Stabilisation?"

**Datenquelle:** Insight-Engine (regelbasiert + optional KI-generiert)

### 2.3 Was wegfällt (vs. altes Dashboard)

| Alt | Warum weg |
|-----|-----------|
| Gesamtanzahl Sessions (aller Zeiten) | Kein täglicher Wert |
| Gesamtdistanz (aller Zeiten) | Kein täglicher Wert |
| Durchschnitts-HR (aller Zeiten) | Zu abstrakt, ohne Kontext |
| Isoliertes Ziel-Widget | Ziel ist jetzt Teil des Plans, Fortschritt im "Fortschritt"-Tab |
| Letzte 5 Sessions als reine Liste | Ersetzt durch "Letztes Training" mit Einordnung |

---

## Teil 3: Training (Woche + Sessions)

### 3.1 Konzept

Alles rund um die **Trainingsausführung** an einem Ort. Geplante und tatsächliche Sessions nebeneinander. Der Nutzer sieht immer: Was soll ich tun, was habe ich getan, wie war die Abweichung.

### 3.2 Wochenansicht (Default: `/training`)

**Header:**
- Woche-Navigation: ← KW 14 (31.03. – 06.04.2026) →
- Aktuelle Phase aus Plan (falls aktiv): "Aufbauphase — Woche 3 von 6"

**Wochenzusammenfassung:**
- Sessions: 3/5 erledigt
- Volumen: 34/50 km
- Zeit: 2:45 / 4:00 Stunden
- Intensitätsverteilung (Mini-Balken: locker / mittel / hart)

**Tages-Cards (Mo-So):**
Jeder Tag zeigt nebeneinander:

```
┌─────────────────────────────────────────┐
│ Dienstag, 1. April                      │
├───────────────────┬─────────────────────┤
│ GEPLANT           │ AUSGEFÜHRT          │
│ Tempolauf 8km     │ ✅ 8.2 km          │
│ 4×1000m @ 4:15    │ Pace: 4:48 (∅)     │
│ Route: Alsterrunde│ HR: 162 bpm        │
│                   │ → 6s/km schneller   │
├───────────────────┴─────────────────────┤
│ [Session-Detail ansehen]                │
└─────────────────────────────────────────┘
```

**Status pro Tag:**
- ✅ Erledigt (Session verknüpft)
- 🟡 Geplant (noch offen)
- ⏭️ Übersprungen
- ➕ Zusätzlich (ungeplante Session)
- — Ruhetag

**Aktionen auf Wochenansicht:**
- "Training hochladen" Button (prominent)
- Drag & Drop: Sessions zwischen Tagen verschieben
- Klick auf geplante Session: Detail-Dialog mit Vorgaben + "Route zuordnen"
- Klick auf ausgeführte Session: Navigiert zu Session-Detail

### 3.3 Sessions-Liste (`/training/sessions`)

- Erreichbar über Link/Tab in der Training-Seite ("Alle Sessions")
- Paginated, filterbar (Suchtext, Trainingstyp, Zeitraum, Workout-Typ)
- Wie bisher, unverändert in Funktionalität

### 3.4 Session hochladen (`/training/sessions/new`)

- Workflow wie bisher (Typ wählen → Formular → Upload → Speichern)
- **Neu:** Automatische Zuordnung zur geplanten Session
  - Wenn für heute eine Session geplant ist und der Trainingstyp übereinstimmt → vorschlagen
  - Nutzer kann bestätigen oder ablehnen
- Nach dem Speichern → Redirect zu Session-Detail

### 3.5 Session-Detail (`/training/sessions/:id`)

**Bestehende Funktionalität bleibt:**
- Metriken-Grid (Distanz, Pace, HR, Höhenmeter etc.)
- HR-Zonen
- Karte + Route (wenn GPS vorhanden)
- Splits/Laps
- KI-Analyse

**Neu:**
- **Soll/Ist-Vergleich** (wenn mit geplanter Session verknüpft):
  - "Geplant: 8km @ 4:15/km — Tatsächlich: 8.2km @ 4:09/km"
  - Abweichung pro Metrik hervorheben
- **Kontextuelle Einordnung:**
  - "3. Tempolauf in dieser Phase — Tendenz: schneller werdend"
  - Vergleich mit Durchschnitt für diesen Trainingstyp

**Aktionen (Kebab-Menü):**
- Als Route speichern (GPS → Bibliothek)
- Als Vorlage speichern (→ Bibliothek)
- Export (FIT/GPX)
- Löschen

### 3.6 Route einer geplanten Session zuordnen

**Flow:**
1. Im Wochenplan: Klick auf geplante Session → Detail-Dialog
2. Feld "Route": Dropdown/Suche aus Routen-Bibliothek
3. Oder: "Neue Route erstellen" → Navigiert zu `/bibliothek/routen/new`
4. Oder: "Rundkurs generieren" → Startpunkt + Distanz → OSRM-Vorschläge
5. Gewählte Route wird auf der geplanten Session gespeichert
6. Auf "Heute"-Dashboard: Zeigt Route mit Minimap bei heutigem Training

**Datenmodell-Änderung:**
- `PlannedSession` bekommt optionales Feld `route_id` (FK zu `training_routes`)

---

## Teil 4: Fortschritt (Fitness-Score + Insights + Analyse)

### 4.1 Konzept

Beantwortet die Fragen: "Wo stehe ich?", "Werde ich besser?", "Was muss ich ändern?" Keine abstrakten Charts ohne Einordnung — jede Visualisierung beantwortet eine konkrete Frage.

### 4.2 Übersicht (Default: `/fortschritt`)

#### Sektion A: Fitness-Score

**Große Darstellung:**
- Score (0-100) zentriert, groß
- Trend-Verlauf: Linienchart über letzte 8-12 Wochen
- Aufschlüsselung darunter: Ausdauer-Score (0-100) | Kraft-Score (0-100)
- Veränderung vs. Vorwoche: "+3 Punkte"
- Einflussfaktoren: "Gestiegen durch regelmäßiges Training und gute Intensitätsverteilung"

#### Sektion B: Form-Indikator

- Aktuelle Form: Frisch / Normal / Ermüdet
- Grafik: Belastung letzte 7 Tage vs. 42-Tage-Gewohnheit
- Empfehlung: "Du bist gut erholt — morgen ist ein guter Tag für ein hartes Training"
- Belastungsverhältnis (ACWR-basiert, aber in einfacher Sprache): "Deine Belastung ist im grünen Bereich"

#### Sektion C: Insights

**Liste proaktiver Erkenntnisse** (mehr als auf dem Dashboard):
- Belastungssteuerung
- Plan-Treue (Soll vs. Ist über Wochen)
- Trainingsbalance (Verteilung locker/mittel/hart)
- Stärken & Schwächen
- Vergleiche (Strecke X früher vs. heute)
- Warnungen (Monotonie, Überbelastung, zu wenig Regeneration)

### 4.3 Trends (Deep Dive: `/fortschritt/trends`)

**Filterbare Charts:**
- Zeitraum: 4 Wochen / 8 Wochen / 3 Monate / 6 Monate / 1 Jahr
- Trainingstyp-Filter

**Charts:**
1. **Pace-Entwicklung** — Linienchart, Durchschnittspace pro Woche (filterbar nach Trainingstyp)
2. **Volumen** — Balken, Wochen-km und Stunden
3. **Intensitätsverteilung** — Gestapelte Balken pro Woche (Zone 1-5 oder locker/mittel/hart)
4. **HR-Effizienz** — Pace bei gleichem HR-Bereich über Zeit (sinkender Puls = fitter)
5. **Kraft-Progression** — Tonnage-Trend, Top-5-Übungen
6. **Plan-Treue** — Balken: geplante vs. tatsächliche Sessions/km pro Woche

---

## Teil 5: Plan (Trainingsplan + Pacing)

### 5.1 Konzept

Strategische Trainingsplanung. Wird gelegentlich eingerichtet und dann über "Training" (Wochenplan) ausgeführt. **Ziel ist integraler Teil des Plans** — kein separates Feature.

### 5.2 Ziel als Teil des Plans (kein separater Ziele-Tab)

**Aktuell (wird abgelöst):**
- Separater "Ziele"-Tab unter Plan
- `RaceGoal` als eigene Entity mit `is_active` Toggle
- Bidirektionale Referenz: Goal ↔ Plan

**Neu:**
- Plan enthält Ziel-Felder direkt:
  - `race_name` (Wettkampf-Name, z.B. "Hamburg Marathon 2026")
  - `race_date` (Wettkampfdatum)
  - `race_distance_km` (Distanz)
  - `target_time_seconds` (Zielzeit)
  - Daraus berechnet: `target_pace`, `days_until_race`
- Ein Plan ist "aktiv" → sein Ziel wird auf dem Dashboard gezeigt
- Kein separates Ziele-CRUD nötig

**Migration:**
- Bestehende RaceGoals in den zugehörigen Plan überführen
- RaceGoals ohne Plan: Als Plan mit nur einem Ziel (ohne Phasen) migrieren
- `race_goals` Tabelle kann danach deprecated/entfernt werden
- Alle Referenzen auf `goal_id` (Pacing, Sessions, Dashboard) auf Plan-Ziel umstellen

### 5.3 Plan-Übersicht (`/plan`)

**Wenn aktiver Plan existiert:**
- Plan-Name + Ziel: "Hamburg Marathon — 06.09.2026 — Ziel: 1:49:59"
- Countdown: "153 Tage bis zum Wettkampf"
- Phasen-Timeline: Visueller Balken mit Phasen, aktuelle Phase hervorgehoben
- Phasen-Liste: Name, Typ, Wochen, Start/Ende
- Wochenübersicht: Welche Wochen generiert, aktueller Stand
- Aktionen: Plan bearbeiten, Wochen generieren, Pacing berechnen

**Wenn kein Plan:**
- Leerer Zustand: "Erstelle deinen Trainingsplan"
- CTA: Plan erstellen (manuell oder YAML-Import)

### 5.4 Plan erstellen/bearbeiten (`/plan/:planId`)

- Name, Beschreibung
- Ziel-Felder (Wettkampf, Datum, Distanz, Zielzeit) — integriert, nicht separat
- Phasen hinzufügen/bearbeiten/verschieben
- YAML-Import bleibt
- Wochen generieren (wie bisher)

### 5.5 Pacing-Rechner (`/plan/:planId/pacing`)

- Nimmt Zieldaten direkt vom Plan (nicht mehr von separatem Goal)
- Strategie wählen (gleichmäßig, negativ, konservativ)
- Optional: Route zuordnen → Höhenprofil fließt in Pace-Berechnung ein
- Splits-Tabelle + Chart
- Export: GPX/FIT für die Uhr, Druckversion

---

## Teil 6: Bibliothek (Routen, Vorlagen, Übungen)

### 6.1 Konzept

Wiederverwendbare Trainingsbausteine. Anlegen, verwalten, in Sessions und Pläne einsetzen. Drei klare Kategorien mit gleichem UX-Pattern: Liste → Detail → Erstellen/Bearbeiten.

### 6.2 Bibliothek-Navigation (`/bibliothek`)

Sub-Tab-Leiste (wie Plan-Hub):
```
Routen | Vorlagen | Übungen
```
- Default-Tab: Routen (oder zuletzt besuchter Tab)
- Jeder Tab zeigt direkt die jeweilige Liste mit Such-/Filterfunktion + "Neu erstellen" Button

### 6.3 Routen (vereinfacht)

#### Datenmodell (neu)

Eine Route ist **reine Geographie**. Keine Trainingsstruktur.

```
TrainingRoute:
  id: int (PK)
  name: str (max 200)
  description: str (optional)
  distance_km: float
  elevation_gain_m: float (optional)
  elevation_loss_m: float (optional)
  location_name: str (optional)
  surface_json: JSON (optional, z.B. {"asphalt": 60, "trail": 40})
  waypoints_json: JSON (GPS-Punkte mit lat/lng/alt/km_marker)
  is_round_trip: bool (default false)
  tags_json: JSON (string array)
  is_favorite: bool (default false)
  created_at: datetime
  updated_at: datetime
```

**Entfernte Felder (vs. aktuell):**
- ~~`route_segments_json`~~ — Trainingsstruktur gehört in Vorlagen/Wochenplan
- ~~`pacing_strategy`~~ — Ist eine Berechnung (Plan × Route), kein Routen-Attribut
- ~~`linked_session_template_id`~~ — Verknüpfung geht andersrum (Session → Route)

#### Erstellen

**Drei Wege eine Route zu erstellen:**

1. **Manuell auf Karte zeichnen** (`/bibliothek/routen/new`)
   - Wegpunkte setzen auf interaktiver Karte
   - OSRM Snapping berechnet Route zwischen Punkten
   - Höhenprofil wird automatisch extrahiert
   - Name, Beschreibung, Tags, Oberfläche angeben
   - Speichern

2. **Rundkurs generieren**
   - Startpunkt auf Karte wählen
   - Zieldistanz eingeben
   - OSRM generiert 1-3 Rundkurs-Alternativen
   - Alternative auswählen → Route wird erstellt

3. **Aus absolvierter Session extrahieren**
   - In Session-Detail: Kebab → "Als Route speichern"
   - GPS-Track wird extrahiert (Douglas-Peucker Vereinfachung)
   - Route wird automatisch erstellt → Nutzer kann Name/Tags ergänzen

#### Route-Editor (vereinfacht)

**Was bleibt:**
- Interaktive Karte mit Wegpunkten (hinzufügen, verschieben, löschen)
- OSRM Route-Snapping
- Metriken: Distanz, Höhenmeter, Wegpunkte
- Höhenprofil-Darstellung
- Name, Beschreibung, Tags, Oberfläche

**Was wegfällt:**
- ~~Segment-Editor~~ (SegmentTable, SegmentBar, useSegmentEditor)
- ~~Pacing-Panel~~ (PacingPanel)
- ~~Segment-Typen~~ (warmup, steady, cooldown etc. auf Routen)
- ~~Auto-Segmentierung~~
- ~~"Route aus Template erstellen"~~ (Template → Route Generierung)

#### Route nutzen

- **Geplante Session:** "Route zuordnen" im Wochenplan → Route aus Bibliothek wählen
- **Pacing-Rechner:** Route als Input → Höhenprofil fließt in Pace-Berechnung ein
- **Export:** GPX / FIT Export bleibt

### 6.4 Vorlagen

Wie bisher, keine Änderungen. Session-Blueprints für Lauf und Kraft.

### 6.5 Übungen

Wie bisher, keine Änderungen. Kraft-Übungskatalog.

---

## Teil 7: Fitness-Score Modell

### 7.1 Konzept

Ein einfacher, verständlicher Score der dem Nutzer sagt wie fit er ist — ohne Vorwissen über TSS, CTL oder TRIMP vorauszusetzen. Inspiriert von Apple Fitness (Einfachheit) und MyGym Genius (Fitnessalter).

### 7.2 Wissenschaftliche Grundlage

Das Modell basiert auf drei etablierten trainingswissenschaftlichen Konzepten:

**A) Banister Fitness-Fatigue-Modell (Impulse-Response)**
- Jede Trainingseinheit erzeugt zwei Effekte: Fitness (langfristig) und Ermüdung (kurzfristig)
- Performance = Fitness minus Ermüdung
- Fitness baut sich langsam auf und ab (Zeitkonstante ~42 Tage)
- Ermüdung baut sich schnell auf und ab (Zeitkonstante ~7 Tage)
- Implementiert als EWMA (Exponentially Weighted Moving Average) — gewichtet neuere Sessions stärker
- Quellen: Banister et al. (1975), TrainingPeaks PMC-Modell

**B) TRIMP (Training Impulse) nach Edwards**
- Quantifiziert die Belastung einer einzelnen Session
- Berechnung: Summierte Zeit in jeder HR-Zone × Gewichtungsfaktor
- Zone 1 (50-60% HRR): Faktor 1 | Zone 2 (60-70%): Faktor 2 | Zone 3 (70-80%): Faktor 3 | Zone 4 (80-90%): Faktor 4 | Zone 5 (90-100%): Faktor 5
- Nutzt Ruhepuls + Maximalpuls aus dem Athleten-Profil (Karvonen-Zonen)
- Für Kraft-Sessions ohne HR: RPE × Dauer (in Minuten) als TRIMP-Äquivalent

**C) Polarisiertes Training (80/20-Regel)**
- Evidenzbasierte Intensitätsverteilung: ~80% Zone 1-2, ~20% Zone 4-5, minimal Zone 3
- Studien belegen Überlegenheit für VO2max und Rennleistung (Seiler 2010, Munoz et al. 2014, Stöggl & Sperlich 2015)
- Abweichung von 80/20 → Warnung/Insight

**D) ACWR (Acute:Chronic Workload Ratio)**
- Verhältnis akute Belastung (7 Tage EWMA) zu chronischer Belastung (28-42 Tage EWMA)
- Ratio 0.8-1.3: optimaler Bereich (niedrigstes Verletzungsrisiko)
- Ratio >1.5: deutlich erhöhtes Verletzungsrisiko
- Evidenz umstritten, aber als Indikator im Kontext anderer Metriken nützlich

### 7.3 Fitness-Score (0-100)

**Kernmetrik: CTL (Chronic Training Load)**

Der Fitness-Score basiert primär auf der CTL — dem exponentiell gewichteten Durchschnitt der täglichen Trainingsbelastung (TRIMP) über ~42 Tage.

**Berechnung Schritt für Schritt:**

1. **TRIMP pro Session berechnen:**
   - Lauf-Sessions: Edwards' TRIMP = Σ (Minuten in Zone_i × Gewicht_i) für i=1..5
   - Kraft-Sessions: TRIMP-Äquivalent = RPE × Dauer_Minuten × 0.5
   - Sessions ohne HR und ohne RPE: Dauer_Minuten × 2 (konservativer Standardfaktor)

2. **Täglichen TRIMP aggregieren:**
   - Mehrere Sessions am Tag: Summe
   - Ruhetag: TRIMP = 0

3. **CTL (Fitness) berechnen** — EWMA mit Zeitkonstante τ=42 Tage:
   ```
   CTL_heute = CTL_gestern × (1 - 1/42) + TRIMP_heute × (1/42)
   ```

4. **ATL (Ermüdung) berechnen** — EWMA mit Zeitkonstante τ=7 Tage:
   ```
   ATL_heute = ATL_gestern × (1 - 1/7) + TRIMP_heute × (1/7)
   ```

5. **TSB (Form) berechnen:**
   ```
   TSB = CTL - ATL
   ```
   - Positiv → Frisch (erholt)
   - Null → Normal
   - Negativ → Ermüdet (Belastung über Gewohnheit)

6. **Score normalisieren auf 0-100:**
   - CTL wird relativ zum eigenen historischen Maximum normalisiert
   - Neuer Nutzer: Erste 4 Wochen Aufbauphase, Score startet niedrig und entwickelt sich
   - Formel: `Score = min(100, CTL / persönliches_CTL_max × 100)`
   - `persönliches_CTL_max` wächst mit dem Nutzer (höchster je erreichter CTL-Wert, ggf. mit Decay)

**Aufschlüsselung:**
- **Ausdauer-Score (0-100):** CTL nur aus Lauf-Sessions
- **Kraft-Score (0-100):** CTL nur aus Kraft-Sessions
- **Gesamt-Score:** Gewichteter Durchschnitt (Gewicht proportional zur Anzahl Sessions je Typ)

**Trend:**
- ↑ steigend: CTL heute > CTL vor 14 Tagen + 2%
- → stabil: Differenz ≤ 2%
- ↓ fallend: CTL heute < CTL vor 14 Tagen - 2%

### 7.4 Form-Indikator (Frische/Ermüdung)

**Basiert auf TSB (Training Stress Balance) = CTL - ATL**

**Drei Stufen:**
- 🟢 **Frisch** — TSB > +10: Gut erholt, guter Tag für hartes Training
- 🟡 **Normal** — TSB zwischen -10 und +10: Normaler Trainingszustand
- 🟠 **Ermüdet** — TSB < -10: Hohe akute Belastung, Regeneration empfohlen

**Zusätzlich: ACWR-basierte Verletzungswarnung**
- ACWR = ATL / CTL
- ACWR > 1.5 → Warnung: "Deine Belastung ist deutlich über deinem Gewohnheitsniveau — erhöhtes Verletzungsrisiko"
- ACWR < 0.5 → Hinweis: "Du trainierst deutlich weniger als gewohnt — Fitness könnte abnehmen"

**Empfehlungen (regelbasiert):**
- Frisch + ACWR 0.8-1.3 → "Guter Tag für ein intensives Training"
- Normal + ACWR 0.8-1.3 → "Normales Training empfohlen"
- Ermüdet ODER ACWR > 1.3 → "Regeneration empfohlen — lockerer Lauf oder Ruhetag"
- ACWR > 1.5 → "Achtung: Verletzungsrisiko erhöht — reduziere die Belastung"

### 7.5 Trainingsqualität (Insights)

**Intensitätsverteilung (80/20-Analyse):**
- Berechnet aus HR-Zonen der letzten 4 Wochen
- Zone 1-2 Anteil vs. Zone 4-5 Anteil
- Ideal: 75-85% locker, 15-25% intensiv
- Insight bei Abweichung: "Nur 60% deiner Läufe waren locker — zu viel Intensität bremst den Fortschritt"

**Monotonie:**
- Monotonie = Durchschnitt(Tages-TRIMP über 7 Tage) / Standardabweichung(Tages-TRIMP über 7 Tage)
- Monotonie > 2.0 → Warnung: "Dein Training ist sehr gleichförmig — mehr Variation reduziert Übertrainingsrisiko"

**Strain (Belastungsmaß):**
- Strain = Wochen-TRIMP × Monotonie
- Hoher Strain → Warnung: "Hohe Gesamtbelastung bei wenig Variation — Übertrainingsrisiko"

### 7.6 Darstellung pro Seite

| Seite | Was wird gezeigt |
|-------|-----------------|
| **Heute** | Score (groß) + Trend-Pfeil + Form-Ampel (Frisch/Normal/Ermüdet) + ein Satz Kontext + ggf. ACWR-Warnung |
| **Fortschritt** | Score-Verlauf (Chart über Wochen), Ausdauer/Kraft aufgeschlüsselt, Form-Verlauf, ACWR-Verlauf, Intensitätsverteilung (80/20), Einflussfaktoren |
| **Plan** | Fitness-Trend im Kontext der Plan-Phasen (optional) |

---

## Teil 8: KI-Chat

### 8.1 Änderung

- **Alt:** Eigener Menüpunkt `/chat` in Sidebar/Bottom Nav
- **Neu:** Floating Action Button (FAB) auf allen Seiten

### 8.2 Spezifikation

- Position: Rechts unten, über Bottom Nav (Mobile) / über Content (Desktop)
- Größe: 56×56px (Touch-Target konform)
- Tap/Click: Öffnet Chat als Bottom Sheet (Mobile) oder Side Panel (Desktop)
- Kontextbezogen: Chat kennt die aktuelle Seite und kann relevante Daten vorschlagen
- Unread-Badge: Kleine Zahl wenn ungelesene Antworten
- Bestehende Chat-Funktionalität bleibt (Konversationen, Quick Actions, Tool-Nutzung)

---

## Teil 9: Profil & Einstellungen

### 9.1 Zugang

- Avatar/Icon oben rechts im Header (auf allen Seiten)
- Navigiert zu `/profil`
- Kein Tab in Bottom Nav oder Sidebar

### 9.2 Inhalte (unverändert)

- Athleten-Profil: Name, Ruhepuls, Maximalpuls, Schwellenwert
- HR-Zonen Konfiguration + Live-Vorschau
- Höhenfaktoren
- Integrationen (zukünftig)
- App-Einstellungen

---

## Teil 10: Zusammenfassung der Änderungen

### Wird neu gebaut

| Feature | Beschreibung |
|---------|-------------|
| "Heute" Dashboard | Persönlicher täglicher Begleiter (Sektion A-E) |
| Fitness-Score Engine | Backend-Berechnung: Score + Form + Insights |
| Form-Indikator | Frisch/Normal/Ermüdet basierend auf Belastungsverhältnis |
| Insight-Engine | Regelbasierte proaktive Hinweise |
| Soll/Ist-Verknüpfung | Geplante Session ↔ Tatsächliche Session sichtbar |
| Route-Session-Zuordnung | Geplante Session bekommt `route_id` Feld |
| Navigation (5 Tabs) | Heute, Training, Fortschritt, Plan, Bibliothek |
| KI-Chat FAB | Floating Button statt Menüpunkt |
| Bibliothek-Hub | Einstiegsseite für Routen/Vorlagen/Übungen |
| "Fortschritt" Seite | Fitness-Score Detail + Insights + Trends |

### Wird vereinfacht

| Feature | Was ändert sich |
|---------|----------------|
| Routen | Segmente, Pacing, Template-Link entfernt — nur noch Geographie |
| Route-Editor | Kein Segment-Editor, kein Pacing-Panel |

### Wird zusammengelegt

| Alt | Neu |
|-----|-----|
| Ziele (separater Tab) | Teil des Plans |
| Sessions-Liste + Wochenplan | "Training" Tab |
| Dashboard + Analyse | "Heute" (täglich) + "Fortschritt" (Deep Dive) |
| Routen + Vorlagen + Übungen | "Bibliothek" Tab |

### Wird verschoben

| Feature | Von | Nach |
|---------|-----|------|
| KI-Chat | Eigener Menüpunkt | Floating Action Button |
| Profil | Bottom Nav Tab | Header-Icon |
| Pacing | Eigener Plan-Tab | Unter Plan (`/plan/:id/pacing`) |

### Wird entfernt

| Feature | Grund |
|---------|-------|
| Separater Ziele-Tab + CRUD | Ziel ist jetzt Teil des Plans |
| Route-Segmente (SegmentTable, SegmentBar) | Trainingsstruktur gehört nicht auf Routen |
| Route-Pacing-Panel | Pacing ist Berechnung, kein Routen-Attribut |
| Route-Template-Verknüpfung | Überflüssig — Session verweist auf Route |
| "Route aus Template generieren" | Template-Segmente auf Route übertragen war das falsche Pattern |
| Abstrakte Dashboard-Stats | Gesamtdistanz/Sessions aller Zeiten → kein täglicher Nutzen |

### Datenmodell-Änderungen

| Tabelle | Änderung |
|---------|----------|
| `training_routes` | Felder entfernen: `route_segments_json`, `pacing_strategy`, `linked_session_template_id` |
| `training_plans` | Felder hinzufügen: `race_name`, `race_date`, `race_distance_km`, `target_time_seconds` |
| `planned_sessions` | Feld hinzufügen: `route_id` (FK zu `training_routes`) |
| `race_goals` | Deprecated → Daten in Plans migrieren, dann Tabelle entfernen |
| Neue Tabelle(n) | `fitness_scores` (täglicher Score-Snapshot) oder als berechneter Wert |

---

## Teil 11: Geklärte Entscheidungen

| Frage | Entscheidung | Begründung |
|-------|-------------|------------|
| **Fitness-Score Modell** | Banister-Modell (CTL/ATL/TSB) mit Edwards' TRIMP | Trainingswissenschaftlich fundiert, etablierter Standard |
| **Insight-Engine** | Hybrid: Regeln für Warnungen + KI für tiefere Insights | Regeln sind schnell + determinisitsch, KI ergänzt bei Bedarf. Beides trainingswissenschaftlich fundiert. |
| **Migration Goals → Plan** | Übergangszeit: Alte Goals bleiben temporär sichtbar mit Hinweis "Bitte Plan erstellen" | Keine Datenverluste, sanfte Migration |
| **Soll/Ist Matching** | Auto-Vorschlag + Bestätigung: App schlägt Match vor (Datum + Typ), Nutzer bestätigt | Bester Kompromiss: wenig Aufwand für Nutzer, aber Kontrolle |
| **Bibliothek-Navigation** | Sub-Tabs (Routen \| Vorlagen \| Übungen) | Konsistent mit Plan-Hub, direkter Zugang ohne Zwischenseite |
| **Implementierungsreihenfolge** | Dashboard + Score zuerst (größter Nutzer-Impact) | Nutzer spürt den Unterschied sofort, Score liefert Basis für Insights |

## Teil 12: Implementierungsreihenfolge

### Phase 1: Fitness-Score Engine + "Heute" Dashboard
**Größter Nutzer-Impact. Fundament für Insights und Fortschritt.**
1. Backend: TRIMP-Berechnung pro Session
2. Backend: CTL/ATL/TSB Engine (EWMA)
3. Backend: Form-Indikator + ACWR
4. Backend: Trainingsqualität-Metriken (80/20, Monotonie)
5. Backend: Insight-Engine (regelbasiert, trainingswissenschaftlich fundiert)
6. Frontend: Neue "Heute"-Seite (alle 5 Sektionen)
7. API: Endpunkte für Score, Form, Insights

### Phase 2: Navigation + Informationsarchitektur
**Neue 5-Tab-Struktur als Rahmen für alles.**
1. Neue Navigation (5 Tabs: Heute, Training, Fortschritt, Plan, Bibliothek)
2. Profil in Header verschieben
3. KI-Chat als Floating Action Button
4. URL-Struktur umbauen (React Router)
5. Bestehende Seiten in neue Struktur einordnen

### Phase 3: Training-Tab (Woche + Sessions zusammenführen)
**Soll/Ist-Verknüpfung — der zweitwichtigste Flow.**
1. Wochenansicht mit Soll/Ist nebeneinander
2. Automatisches Session-Matching (Vorschlag + Bestätigung)
3. Route einer geplanten Session zuordnen (`route_id` auf PlannedSession)
4. Session-Detail: Soll/Ist-Vergleich anzeigen

### Phase 4: Fortschritt-Seite
**Deep Dive für den Fitness-Score + Insights.**
1. Score-Verlauf (Chart)
2. Aufschlüsselung Ausdauer/Kraft
3. Form-Verlauf + ACWR
4. Intensitätsverteilung (80/20-Analyse)
5. Trend-Charts (Pace, Volumen, HR-Effizienz, Kraft)
6. Plan-Treue (Soll vs. Ist über Wochen)

### Phase 5: Plan + Ziele zusammenlegen
**Datenmodell-Bereinigung.**
1. Ziel-Felder in TrainingPlan integrieren
2. Alembic-Migration
3. Übergangs-UI für bestehende Goals ohne Plan
4. Pacing-Rechner auf Plan-Ziel umstellen
5. Dashboard-Referenzen auf Plan-Ziel umstellen
6. Separaten Ziele-Tab entfernen

### Phase 6: Routen vereinfachen + Bibliothek
**Technische Schulden aufräumen.**
1. Route-Segmente, Pacing, Template-Link aus Datenmodell entfernen
2. Route-Editor vereinfachen (kein Segment-Editor, kein Pacing-Panel)
3. Bibliothek-Hub mit Sub-Tabs
4. Routen, Vorlagen, Übungen in Bibliothek einordnen
5. "Route aus Template generieren" entfernen
6. Frontend-Code aufräumen (Segment-Komponenten entfernen)

### Phase 7: KI-Integration + Insights-Ausbau
**KI-generierte Insights als Ergänzung zu regelbasierten.**
1. KI-Insights: Claude analysiert Trainingsdaten und generiert persönliche Empfehlungen
2. Kontextbezogener Chat (weiß auf welcher Seite der Nutzer ist)
3. Proaktive Hinweise basierend auf Datenveränderungen
