# Fitness Level System v2 — Konzept & Designentscheidungen

> ⚠️ **ARCHIVIERT (Superseded) — 2026-04-27**
>
> Das Level-System wird **nicht** umgesetzt. Goal Readiness ersetzt es konzeptionell.
> Source of Truth: **PRD §5.1 (Goal Readiness)** → [`../PRD.md`](../PRD.md).
> Hier verbleibend als historische Referenz für die Entscheidungsbegründung.

> **Original-Status: SUPERSEDED — 2026-04-26**
>
> Das Level-System wird **nicht** umgesetzt. Goal Readiness (Epic [#718](https://github.com/NCS23/training-analyzer/issues/718)) ist
> das primäre Mess-Instrument. Siehe [DASHBOARD_LAYOUT_PROPOSAL.md](DASHBOARD_LAYOUT_PROPOSAL.md)
> für das neue Konzept.
>
> **Kurzbegründung:**
> 1. **Kraft-Levels methodisch nicht haltbar** — RPE-basiertes TRIMP belohnt Untrainiertheit (siehe §6 unten).
> 2. **Levels widersprechen der Coach-Positionierung** — abstrakte Klassifizierung statt kontextualisiertem Coaching.
> 3. **Level-Cards konkurrieren mit Goal Readiness** — beide beantworten dieselbe Frage, Goal Readiness aber spezifischer.
>
> **Was bleibt:** Die Level-Namen (*„Im Rhythmus", „In voller Stärke"* etc.) bleiben als
> Coach-Vokabular für die AI Coach Subline erhalten — nicht als formale Klassifizierung.
>
> Dieses Dokument bleibt als historische Referenz / Designentscheidungs-Trace bestehen.

---

**Epic:** [#694](https://github.com/NCS23/training-analyzer/issues/694) · **Status:** zurückgestellt
**Erarbeitet:** April 2026
**Mockup:** `.claude/worktrees/peaceful-ride/mockups/fitness-level-mockup.html` (obsolet)

---

## Ausgangslage: Warum das alte System nicht funktioniert

Das bisherige System normalisiert CTL gegen das **persönliche Maximum**:

```
Score = CTL / persönliches_CTL_Maximum × 100
```

Das erzeugt drei fundamentale Probleme:

1. **Score schrumpft nach Pause** — CTL fällt, Maximum bleibt → nach einer Verletzung sieht man Score 40 obwohl man vorher bei 80 war. Demotivierend.
2. **100 praktisch unerreichbar** — das Maximum wächst immer mit, wer gut trainiert kommt nie an 100.
3. **Nicht objektiv** — zwei Athleten mit identischem CTL haben unterschiedliche Scores je nach ihrer History.

Das Fallback für neue Nutzer (`CTL / 80.0`) ist willkürlich und nicht kommuniziert.

---

## Kernfrage: Was soll der Score aussagen?

Nach Diskussion: zwei Dinge, klar getrennt:

1. **"Wie gut ist meine Fitness?"** → braucht externe, stabile Referenz
2. **"Wie entwickle ich mich?"** → braucht Zeitverlauf (Trend)

Goal Readiness ("bin ich bereit für mein Ziel?") ist eine **dritte, separate Metrik** — nicht im Score verrechnet.

---

## Warum ein Level-System?

Der Level-Ansatz löst alle drei Probleme gleichzeitig:

| Problem | Lösung |
|---------|--------|
| Score schrumpft nach Pause | Level-Grenzen sind fix, Score ist relativ zum Level |
| 100 unerreichbar | Score 0–100 = Position *innerhalb* des Levels — immer erreichbar |
| Nicht objektiv | Level-Grenzen sind populationsreferenziert, nicht personal |
| Neuling ohne Score | Level 1, Score 5 — sofort bedeutungsvoll |

Zusätzlich: **Gamification**. Level-Aufstieg ist ein klares Ereignis das gefeiert werden kann. Ein Score der von 67 auf 68 steigt ist emotional bedeutungslos. "Du hast Level 5 erreicht" nicht.

### Verworfene Alternativen

**Populationsreferenz ohne Level (z.B. `sqrt(CTL/90) × 100`):**
Besser als persönliches Maximum, aber ein ambitionierter Freizeitläufer landet bei Score ~78 und weiß nicht ob das gut oder schlecht ist. Ohne Kontext ist eine absolute Zahl schwer einzuordnen.

**Composite Score (CTL + Konsistenz + Progression):**
Motivational, aber verliert Transparenz. Zwei Athleten mit gleichem CTL haben unterschiedliche Scores — schwer zu erklären. Entscheidung: Konsistenz bleibt separater Indikator, nicht in Score eingerechnet.

**Kein Score, nur Level:**
Zu wenig Information. Der Score innerhalb des Levels zeigt wie nah der nächste Aufstieg ist — das ist der eigentliche Motivations-Hook.

---

## Level-Definitionen

### Ausdauer (CTL-basiert, Edwards TRIMP)

| Level | Name | CTL-Bereich | Bedeutung |
|-------|------|-------------|-----------|
| 1 | Erste Schritte | 0–12 | Sporadisch, Einstieg |
| 2 | Im Rhythmus | 12–28 | 3×/Woche, regelmäßig |
| 3 | Auf Kurs | 28–48 | Solide Basis |
| 4 | In voller Stärke | 48–68 | Sub-2h HM Niveau |
| 5 | Entfesselt | 68–88 | Ambitioniert, strukturiert |
| 6 | Grenzenlos | 88–120 | Sehr hohe Belastung |
| 7 | Legende | 120+ | Elite-Amateur |

**Warum diese Grenzen?** Basieren auf Steady-State CTL bei gegebener Trainingsfrequenz (Edwards TRIMP). Bei CTL-Tau=42 konvergiert EWMA zum täglichen Durchschnitt. 5×/Woche 60min Zone 2-3 → CTL ~45-55. Grenzen noch gegen echte App-Daten zu validieren (offen).

### Kraft (Kraft-CTL-basiert, RPE × Dauer)

| Level | Name |
|-------|------|
| 1 | Erste Wiederholung |
| 2 | Im Aufbau |
| 3 | Starke Basis |
| 4 | Volle Kraft |
| 5 | Unaufhaltsam |

Nur 5 Level, da Kraft sekundär in der App. Eigene CTL-Grenzen notwendig weil Kraft-TRIMP (RPE-basiert) nicht mit Lauf-TRIMP vergleichbar.

### Score-Berechnung

```
Score = round((CTL - level_min) / (level_max - level_min) × 100)
```

Linear innerhalb des Levels. Klar, transparent, erklärbar.

### Normalisierung (wie CTL auf Levels gemappt wird)

Sqrt-Kurve gegen Referenz CTL=90:

```
load_score = sqrt(CTL / 90) × 100
```

Sqrt gibt schnelle Progression früh (motivierend für Einsteiger), härtere Gains später (realistisch). CTL=90 = sehr ambitionierter Amateur, für die Zielgruppe der App erreichbar aber nicht trivial.

---

## Hysterese

Ohne Schutzzone: CTL knapp an der Grenze → Level flackert täglich. Lösung:

- **Level-Up**: CTL ≥ Schwelle für **7 aufeinanderfolgende Tage**
- **Level-Down**: CTL < Schwelle − 10% für **21 aufeinanderfolgende Tage**

Das macht ein Level zur stabilen Aussage, nicht zum Tages-Wert.

### Verhalten nach Trainingspause

Das **persönliche Höchstlevel** ist permanent und kann nie verloren gehen — es ist ein Achievement. Das **aktuelle Level** kann nach 21 Tagen sinken, wird aber positiv gerahmt: "Wiederaufbau-Modus" statt "Abstieg". Bei Rückkehr: "Willkommen zurück auf Level X".

---

## Dashboard-Hierarchie

```
Guten Morgen, Nils.
[AI Coach Subline — dynamisch]

[Ziel-Card — primär, Eyecatcher]
  Kopenhagen HM · Sub 2:00h · 42 Tage
  78% bereit (Ring)
  Fitness (CTL) ████ 79%
  Langläufe     ████ 83%
  Tempoläufe    ███  62%  ← orange (Schwäche)
  Konsistenz    ████ 88%

Fitness
[Ausdauer Card]  Level 4 · In voller Stärke · 82
[Kraft Card]     Level 2 · Im Aufbau · 54
```

### Warum Ziel-Card primär, nicht Score?

Die täglich relevante Frage ist nicht "wie fit bin ich abstrakt?" sondern "komme ich rechtzeitig ans Ziel?". Die Level-Cards sind wichtig, aber sekundär. Ein User 6 Wochen vor einem Rennen will wissen ob er bereit wird — nicht ob er Level 4 oder 5 ist.

### Empty State (kein Ziel gesetzt)

```
[minsaga Logo]
Jede Saga braucht ein Ziel.
Ein Rennen. Eine Zeit. Eine Distanz.
Setz den Horizont — wir zeigen dir den Weg dorthin.
[Ziel festlegen]
```

Greift die Saga-Sprache der App auf. Nicht technisch ("Du hast kein Ziel gesetzt"), sondern einladend und narrativ.

---

## Goal Readiness: Warum CTL allein nicht reicht

CTL misst nur Volumen und Intensität über Zeit — nicht ob du **für diese spezifische Pace und Distanz** vorbereitet bist. Jemand mit hohem CTL aus vielen kurzen Läufen ist nicht zwingend für einen HM bereit.

Deshalb: **4 Komponenten**, die zusammen Race-Readiness abbilden:

| Komponente | Misst | Wissenschaftliche Basis |
|-----------|-------|------------------------|
| Fitness (CTL) | Trainingsvolumen-Basis | Banister/Coggan |
| Langläufe | Spezifische Ausdauer für die Distanz | ≥18km Läufe in letzten 8 Wochen |
| Tempoläufe | Pace-spezifische Vorbereitung | Schwellen-/Temptraining nahe Zielpace |
| Konsistenz | Regelmäßigkeit (kein Overreaching) | Trainingstage / 30 in 42 Tagen |

**Gewichtung noch offen** — wird in #698 definiert und validiert.

---

## AI Coach Subline

Keine statische Zeile — dynamisch generiert, kontextabhängig. Brückt zwischen Begrüßung und Dashboard-Content.

**Kontext-Inputs:**
- Tage bis Rennen
- Gestrige Session (ja/nein, Typ)
- Aktuelle Form (TSB: frisch/normal/ermüdet)
- CTL-Trend
- Tageszeit

**Beispielzustände:**

| Situation | Subline |
|-----------|---------|
| 42 Tage, steigend | "Du bist auf dem richtigen Weg. Hier ist dein Stand." |
| Tag nach hartem Training | "Gestern hast du geliefert. Heute schaust du, wo du stehst." |
| Ruhetag, gute Form | "Dein Körper arbeitet auch heute. Schau was er erreicht hat." |
| Rennwoche (≤7 Tage) | "7 Tage noch. Alles was du brauchst, hast du bereits." |
| Nach Pause | "Willkommen zurück. Lass uns schauen, wo wir stehen." |
| Kein Ziel | "Hier ist dein aktueller Stand. Was willst du damit erreichen?" |

---

## Offene Fragen (für spätere Iterationen)

1. **Level-Grenzen validieren** — CTL-Richtwerte aus Literatur, aber unsere App nutzt Edwards TRIMP. Müssen gegen echte Nutzerdaten kalibriert werden sobald mehr Daten vorhanden.

2. **Ziel-CTL-Richtwerte** — Welcher CTL ist nötig für Sub-2h HM, Sub-1:45, etc.? Grobe Schätzung: ~55-70 für Sub-2h. Noch nicht präzise hergeleitet.

3. **Goal Readiness Gewichtung** — 4 Komponenten mit welcher Gewichtung? Erste Annahme: CTL 35%, Langläufe 30%, Tempoläufe 20%, Konsistenz 15%. Zu validieren.

4. **Kalibrierungsphase für neue Nutzer** — EWMA braucht ~21 Tage zum Konvergieren. Anzeige "Score wird kalibriert" in den ersten Wochen, oder Onboarding-Schätzung basierend auf Trainingshistorie-Angabe?

5. **Kraft-CTL Grenzen** — Welche RPE-TRIMP Werte entsprechen welchem Niveau? Wenig Referenzdaten verfügbar.

6. **RPE als Basis für Kraft-CTL ungeeignet** — RPE × Dauer bevorzugt unfitte Nutzer: Wer eine Session mit RPE 9 absolviert (weil er untrainiert ist) akkumuliert mehr TRIMP als jemand fitteres mit RPE 5 bei gleicher Dauer. Mögliche Alternativen:
   - **Tonnage** (Gewicht × Wiederholungen × Sätze) als objektive, RPE-unabhängige Basis
   - **RPE nur als Intensitäts-Modifikator** auf das geleistete Volumen — nicht als Hauptgröße
   - **Kein Kraft-CTL, nur Konsistenz** — nur messen ob regelmäßig trainiert wird, nicht wie hart
   → Muss vor Implementierung des Kraft-Level-Systems entschieden werden.

---

## Entscheidung gegen das Level-System (2026-04-26)

Nach kritischer Prüfung wurde entschieden, das Level-System **nicht** umzusetzen.
Die Begründung im Detail:

### 1. Kraft-Levels sind methodisch nicht haltbar

Punkt 6 der „Offenen Fragen" oben dokumentiert, dass RPE-basiertes Kraft-TRIMP
**Untrainiertheit belohnt**: Wer eine Session mit RPE 9 absolviert (weil untrainiert)
akkumuliert mehr TRIMP als jemand fitteres mit RPE 5 bei gleicher Dauer. Höheres
Level für weniger Fitness ist kaputtes Design.

Die diskutierten Alternativen lösen das Grundproblem nicht:
- **Tonnage** (kg × reps × sets) bevorzugt schweres Heben über Wiederholungs-Volumen —
  ungeeignet für läuferspezifisches Krafttraining (Stabilität/Funktion, nicht 1RM)
- **Reine Konsistenz**: brauchbar, aber dann kein Level-System mehr, sondern Streak-Tracking

Zudem: Kraft ist mehrdimensional (Maximalkraft, Hypertrophie, Kraftausdauer,
sportartspezifisch). Ein einzelnes Kraft-Level kann nichts Aussagekräftiges
zusammenfassen. Bei einem Läufer ist Kraft Begleittraining, nicht Hauptdisziplin —
sie braucht keinen parallelen Level-Stack zur Ausdauer.

### 2. Ausdauer-Levels widersprechen der Coach-Positionierung

Der Style Guide (`BRAND_STYLE_GUIDE.md`) positioniert minsaga explizit:

> *„Coach, nicht Werkzeug — Daten erscheinen immer mit Kontext. Nicht 'CTL: 82'
> sondern 'Du bist in voller Form.'"*

> *„minsaga füllt die Lücke: ein persönlicher KI-Begleiter der deinen Fortschritt
> versteht … hinter den Zahlen eine Geschichte steckt."*

Ein Level-System bringt Daten *ohne* Handlungskontext: „Level 4, Score 82" sagt
einem Läufer **nichts darüber, was er tun soll oder was es bedeutet**. Es ist
abstrakte Klassifizierung — exakt das, was Garmin macht und was Minsaga laut
eigener Positionierung *nicht* sein will.

Ein echter Coach sagt nicht *„Du bist Level 4"*. Er sagt *„Deine Grundlagenausdauer
ist gut, aber deine Tempoläufe für die Pace fehlen — die nächsten 4 Wochen
fokussieren wir darauf."* — genau das, was Goal Readiness mit ihren 4 Komponenten
plus AI Coach Subline schon leistet.

### 3. Level-Cards konkurrieren mit Goal Readiness

Im obigen Abschnitt „Warum Ziel-Card primär, nicht Score?" ist bereits dokumentiert:

> *„Die täglich relevante Frage ist nicht 'wie fit bin ich abstrakt?' sondern
> 'komme ich rechtzeitig ans Ziel?'. Die Level-Cards sind wichtig, aber sekundär."*

Wenn die Level-Cards **nicht** die täglich relevante Frage beantworten, sind sie
auf dem Dashboard fehl am Platz. Sie konkurrieren mit Goal Readiness um Aufmerksamkeit,
ohne neuen Erkenntniswert zu bieten.

### 4. Geratene Schwellwerte

Der Abschnitt „Warum diese Grenzen?" räumt ein, dass die CTL-Bereiche (12, 28, 48,
68, 88, 120) *„noch gegen echte App-Daten zu validieren"* sind — d.h. die
Schwellwerte sind aktuell geraten. Ein produktiv ausgerolltes System mit geratenen
Klassengrenzen wäre methodisch fragwürdig und würde nach erster Datenerhebung
ohnehin korrigiert werden müssen, was zu Level-Migrationen für Bestandsnutzer führen würde.

### Was wir stattdessen tun

- **Goal Readiness** bleibt das primäre Mess-Instrument (Epic [#718](https://github.com/NCS23/training-analyzer/issues/718))
- **CTL-Trend** bleibt verfügbar — verschiebt sich aber in eine Detail-/Verlaufsansicht
- **Level-Namen** (*„Erste Schritte"* … *„Legende"*) bleiben als Coach-Vokabular für
  AI-Subline-Formulierungen erhalten — z.B. *„Du bist auf Kurs für Sub-2h"*
- **Krafttraining** wird als Konsistenz-Indikator („2 von 3 Einheiten diese Woche")
  abgebildet — keine Score- oder Level-Berechnung
- **Goal-Achievement-Feier** ersetzt die Level-Up-Feier — emotional stärker, weil
  mit echter persönlicher Geschichte verknüpft

### Auswirkungen auf bestehende Stories

| Story | Aktion |
|---|---|
| [#694](https://github.com/NCS23/training-analyzer/issues/694) Epic Fitness Level System | **Schließen** als Wontfix mit Verweis auf neue Doku |
| [#695](https://github.com/NCS23/training-analyzer/issues/695) Score-Engine v2 | **Schließen** — wird nicht implementiert |
| [#696](https://github.com/NCS23/training-analyzer/issues/696) Level Cards Frontend | **Schließen** — Cards entfallen aus Dashboard |
| [#697](https://github.com/NCS23/training-analyzer/issues/697) Level-Up Celebration | **Umschreiben** auf Goal-Achievement Celebration |

---

## Verwandte Dokumente

- [DASHBOARD_LAYOUT_PROPOSAL.md](DASHBOARD_LAYOUT_PROPOSAL.md) — **Aktuelles Dashboard-Konzept (ersetzt dieses Doc)**
- [BRAND_STYLE_GUIDE.md](BRAND_STYLE_GUIDE.md) Section 11 — Aktualisierte Doku zum Fitness-Tracking
- [TRAINING_CONTEXT.md](TRAINING_CONTEXT.md) — HM Sub-2h Kontext
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md) — Datenmodell
- Epic [#694](https://github.com/NCS23/training-analyzer/issues/694) — Implementierungsplan (zurückgestellt)
- Epic [#718](https://github.com/NCS23/training-analyzer/issues/718) — Goal Readiness (aktuelles Konzept)
