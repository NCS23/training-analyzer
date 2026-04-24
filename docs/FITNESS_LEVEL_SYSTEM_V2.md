# Fitness Level System v2 — Konzept & Designentscheidungen

**Epic:** [#694](https://github.com/NCS23/training-analyzer/issues/694)
**Erarbeitet:** April 2026
**Mockup:** `.claude/worktrees/peaceful-ride/mockups/fitness-level-mockup.html`

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

## Verwandte Dokumente

- [TRAINING_CONTEXT.md](TRAINING_CONTEXT.md) — HM Sub-2h Kontext
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md) — Datenmodell
- Epic [#694](https://github.com/NCS23/training-analyzer/issues/694) — Implementierungsplan
