# Dashboard Layout — Proposal ohne Level-Cards

> ⚠️ **ARCHIVIERT — 2026-04-27**
>
> Dieses Dokument ist nicht mehr die Source of Truth.
> Inhalte fließen ins **PRD §4.1 (Heute)** ein → [`../PRD.md`](../PRD.md).
> Hier verbleibend als historische Referenz für Begründungen (z.B. Wegfall des Level-Systems).

> **Original-Status:** Vorschlag · 2026-04-26
> Ergänzt / ersetzt: [FITNESS_LEVEL_SYSTEM_V2.md](FITNESS_LEVEL_SYSTEM_V2.md) — siehe „Hintergrund".

---

## Hintergrund

Die ursprüngliche Idee eines Level-Systems (Epic [#694](https://github.com/NCS23/training-analyzer/issues/694))
sollte drei Probleme des alten CTL-Scores lösen: Schrumpfen nach Pause, 100 unerreichbar,
nicht objektiv. Die Lösung war ein populationsreferenziertes Level-System mit Score 0–100
innerhalb des Levels.

Bei näherer Prüfung haben sich drei wesentliche Schwächen gezeigt:

1. **Kraft-Levels sind methodisch nicht haltbar** — RPE-basiertes TRIMP belohnt Untrainiertheit
   (siehe FITNESS_LEVEL_SYSTEM_V2 §6 „Offene Fragen"). Tonnage- und reine Konsistenz-Alternativen
   lösen das Grundproblem nicht.
2. **Levels widersprechen der Coach-Positionierung** — minsaga positioniert sich gegen Strava-artige
   Gamification und für kontextualisiertes Coaching. „Du bist Level 4" ist eine abstrakte
   Klassifizierung ohne Handlungsempfehlung — genau das, was Garmin macht und was Minsaga
   *nicht* sein will.
3. **Level-Cards konkurrieren mit Goal Readiness** — beide beantworten dieselbe Frage („wo
   stehe ich?"), Goal Readiness aber spezifischer und handlungsorientierter.

Die Goal Readiness (Epic [#718](https://github.com/NCS23/training-analyzer/issues/718)) ist
das stärkere Konzept und sollte das primäre Mess-Instrument bleiben. Levels werden gestrichen,
Level-Namen bleiben als Coach-Vokabular bestehen.

---

## Neues Dashboard

### Hierarchie

```
┌─ Header ──────────────────────────────────────┐
│ Guten Morgen, Nils.                           │
└───────────────────────────────────────────────┘

┌─ AICoachInsight ──────────────────────────────┐
│ 🤖  Insight · KI-GENERIERT                    │
│     38 Tage bis Berlin. Dein Tempolauf am     │
│     Freitag entscheidet — heute sammelst du   │
│     Kilometer, ohne zu fordern.               │
└───────────────────────────────────────────────┘

┌─ Ziel-Card (raised, spacious) ── Hauptfokus ──┐
│ Kopenhagen HM · Sub 2:00h · 42 Tage          │
│                                               │
│   [Ring 78 %]                                 │
│                                               │
│ ┌─ Fitness (CTL) ────────── 79 % ──────────┐│
│ ├─ Langläufe ─────────────── 83 % ──────────┤│
│ ├─ Tempoläufe ────────────── 62 % ⚠ ────────┤│
│ └─ Konsistenz ─────────────── 88 % ──────────┘│
└───────────────────────────────────────────────┘

┌─ PlannedSessionCard (raised) — HEUTE ─────────┐
│ HEUTE GEPLANT                                 │
│ Ruhelauf                                      │
│ Plauderton, Puls unter 140. Lockere Beine.    │
│                                               │
│ DISTANZ   PACE      ZONE                      │
│ 6 km      5:40/km   < 140 bpm                 │
│                                               │
│ [Lauf starten ›]                              │
└───────────────────────────────────────────────┘

┌─ WeekOverviewCard (raised) ───────────────────┐
│ WOCHE 9 VON 14                  46 km geplant │
│                                               │
│ Mo  Di  Mi  Do  Fr  Sa  So                    │
│ 14  15  16  17  18  19  20                    │
│  ·   ·   ·   ·   ·       ·                    │
│                                               │
│ Detail-Sektion klappt nur auf, wenn ein       │
│ anderer Tag als HEUTE ausgewählt wird —       │
│ vermeidet Doppelung mit PlannedSessionCard.   │
└───────────────────────────────────────────────┘

[Trend / Verlauf — auf Detail-Seite, nicht im Dashboard]
```

### Was wegfällt

| Entfernt | Begründung |
|---|---|
| `Ausdauer Card` (Level + Score) | Goal Readiness beantwortet die Frage präziser und handlungsorientierter |
| `Kraft Card` (Level + Score) | Methodisch nicht haltbar (RPE-Problem). Das Krafttraining wird nicht mehr bewertet — die Existenz im Wochenplan reicht. |
| Level-Up Vollbild-Feier (Story [#697](https://github.com/NCS23/training-analyzer/issues/697)) | Wird ersetzt durch **Goal-Achievement-Feier** beim Erreichen des gesetzten Rennziels — emotional stärker, weil mit echter persönlicher Geschichte verknüpft |

### Was bestehen bleibt / hinzukommt

- **AICoachInsight (existiert)** — Komponente in Figma (id `2675:4232`), Bot-Icon mit Fuchsia-Akzent + Header *„Insight · KI-GENERIERT"* + Body-Text. Stärkster Coach-Touchpoint. Greift Form (TSB), gestriges Training, Tage bis Rennen und Trend als Kontext auf. Eigene L4-Tokens unter `components/aicoachinsight/*`. Ersetzt die ursprünglich angedachte „AI Coach Subline" — eine eigene Card hat mehr Präsenz.
- **Goal Readiness Card** mit 4 Komponenten (Fitness, Langläufe, Tempoläufe, Konsistenz) — primärer Eyecatcher.
- **PlannedSessionCard (existiert)** — Heute-Card mit allen Session-States (`planned | active | completed | missed | optional | rest-day | upload`). Trägt die konkreten Aktionen: Lauf starten, FIT-Datei hochladen, Auswerten, Verschieben, Einplanen.
- **WeekOverviewCard (existiert)** — Wochenkontext mit Mo–So-Statusleiste. Detail-Sektion klappt nur auf, wenn ein **anderer** Tag als heute ausgewählt wird — sonst doppelt sie sich mit der PlannedSessionCard. Varianten: `state=default | rest-day | no-training | strength | completed`.
- **Level-Namen als Coach-Vokabular** — der AI Coach kann sagen *„Du bist im Rhythmus für Sub-2h"* oder *„Auf Kurs zur Halbmarathon-Form"*. Die Namen bleiben warm, narrativ, motivierend — ohne formale Klassifizierung.

### Warum PlannedSessionCard *und* WeekOverviewCard?

Beide existieren bereits, beide haben einen klar abgegrenzten Zweck:

| Komponente | Zoom | Zweck |
|---|---|---|
| `PlannedSessionCard` | Eine Session | *„Was tue ich jetzt?"* — Action-CTAs (Start / Upload / Verschieben / Auswerten). 7 States. |
| `WeekOverviewCard` | Ganze Woche | *„Wo stehe ich in der Woche?"* — Status pro Tag, Vorschau anderer Tage. |

Die WeekOverviewCard bringt eine **kompakte** Detail-Sektion mit, die für die Vorschau
*anderer* Tage gedacht ist. Damit auf dem Dashboard keine Doppelung entsteht, gilt eine
einfache Regel:

> **Wenn der ausgewählte Tag in der WeekOverviewCard = heute ist, wird die Detail-Sektion
> ausgeblendet** — die PlannedSessionCard zeigt das schon prominenter.

Sobald der User in der WeekOverviewCard einen anderen Tag tippt, klappt deren Detail-Sektion
auf und zeigt die Vorschau für Donnerstag/Freitag/etc. So bleiben beide Cards im Einsatz,
ohne sich zu duplizieren.

Form (TSB) als reine Metrik braucht keine eigene Card — sie ist Kontext für die
AI Coach Insight, nicht eigenständige Information.

---

## Empty State (kein Ziel gesetzt)

Bleibt unverändert (im Style Guide bereits dokumentiert):

```
[minsaga Logo]
Jede Saga braucht ein Ziel.
Ein Rennen. Eine Zeit. Eine Distanz.
Setz den Horizont — wir zeigen dir den Weg dorthin.
[Ziel festlegen]
```

Wenn kein Ziel gesetzt ist, fällt die Goal-Card weg — stattdessen erscheint dieser Empty
State. AICoachInsight, PlannedSessionCard und WeekOverviewCard können trotzdem angezeigt
werden mit allgemeinen Empfehlungen.

---

## Mapping zu existierenden Komponenten

| Dashboard-Element | Komponente | Status / Variante |
|---|---|---|
| AI Coach Insight | `AICoachInsight` | existiert (Figma `2675:4232`) — Bot-Icon + „Insight · KI-GENERIERT" + Body |
| Ziel-Card | `GoalCard` | existiert, `elevation=raised, padding=spacious` (Hero) |
| Heute (Action) | `PlannedSessionCard` | existiert, 7 States (`planned/active/completed/missed/optional/rest-day/upload`) |
| Wochenkontext | `WeekOverviewCard` | existiert, 5 States — Detail-Sektion ausblenden wenn ausgewählter Tag = heute |

`LevelScoreCard` (existiert in Figma) wird **nicht** mehr im Dashboard genutzt — bleibt
optional als historisches Artefakt oder für eine spätere Detail-/Verlaufsansicht verfügbar.

---

## Trend / Verlauf

Der CTL-Trend (und ggf. weitere historische Werte) wandert auf eine **Detail- bzw.
Fortschrittsseite** (Tab „Fortschritt"). Dort hat er Platz und Kontext — auf dem
Dashboard nimmt er Aufmerksamkeit weg, ohne tagesaktuell relevant zu sein.

---

## Migration

### Frontend

1. Dashboard-Layout umbauen: Ausdauer- und Kraft-Card entfernen, Heute- und Diese-Woche-Card ergänzen
2. `LevelScoreCard` aus dem Dashboard-Code entfernen (Komponente bleibt vorhanden, falls später wieder gebraucht)
3. Goal-Achievement-Feier statt Level-Up-Feier implementieren (Story #697 anpassen oder neu schreiben)

### Backend

1. Score-Engine v2 (Story [#695](https://github.com/NCS23/training-analyzer/issues/695)) **stoppen** falls nicht
   begonnen — Ressourcen in Goal Readiness (Epic #718) umlenken
2. CTL-Berechnung bleibt unverändert (wird von Goal Readiness und Trend weiter gebraucht)
3. Hysterese / Level-Logik nicht implementieren

### Docs

- `FITNESS_LEVEL_SYSTEM_V2.md` → als „Superseded" markieren, Begründung dokumentieren
- `BRAND_STYLE_GUIDE.md` Section 11 → umschreiben auf neues Konzept (Goal Readiness primär,
  Level-Namen als Coach-Vokabular bleiben)

---

## Was wir gewinnen / verlieren

**Gewinn:**
- Dashboard wird ruhiger (Lagom-Prinzip)
- Keine geratenen Level-Schwellwerte mehr, die später kalibriert werden müssten
- Keine demotivierenden Level-Downs nach Verletzungspause
- Konsistente Coach-Persona ohne konkurrierende Gamification-Schicht
- Goal Readiness wird stärker, weil sie nicht mehr neben Levels um Aufmerksamkeit konkurriert
- Klare emotionale Hierarchie: das Ziel ist der Held der Geschichte, nicht ein abstraktes Level

**Verlust:**
- Level-Up als regelmäßiger Mikro-Feier-Moment fällt weg → kompensiert durch Goal-Achievement
  als seltenerer, aber emotional stärkerer Höhepunkt
- Die abstrakte „wie fit bin ich?"-Antwort fällt weg → ersetzt durch zielrelative Aussagen
  („Du bist auf Kurs für Sub-2h")
- Bestehende Mockups / Vorarbeiten für Level-System (HTML-Mockup, Stories #695–#697)
  werden teilweise obsolet
