# Goal Readiness — Konzept

> ⚠️ **ARCHIVIERT — 2026-04-27**
>
> Dieses Dokument ist nicht mehr die Source of Truth.
> Inhalte fließen ins **PRD §5.1 (Goal Readiness)** ein → [`../PRD.md`](../PRD.md).
> Hier verbleibend als historische Referenz für die sportwissenschaftliche Herleitung.

> **Original-Status:** Entwurf v1
> **Letzte Aktualisierung:** 2026-04-19
> **Verwandt:** [FITNESS_LEVEL_SYSTEM_V2.md](FITNESS_LEVEL_SYSTEM_V2.md) · [../design/BRAND_STYLE_GUIDE.md](../design/BRAND_STYLE_GUIDE.md)
> **Issue:** [#716](https://github.com/NCS23/training-analyzer/issues/716)

---

## 1. Grundidee

**Goal Readiness** beantwortet die Frage: *„Bin ich bereit für dieses Rennen in X Tagen in Zeit Y?"*

Im Unterschied dazu beantwortet das **Fitness Level System V2** die Frage: *„Wie fit bin ich generell, unabhängig von einem Rennen?"*

**Zwei Dimensionen, komplementär:**

| Konzept | Frage | Zeitraum | Kontext |
|---|---|---|---|
| **Fitness Level (V2)** | Wer bin ich? | Dauerhaft, wächst mit Training | Ziel-unabhängig |
| **Goal Readiness** | Wo stehe ich gerade? | Temporär, an ein Rennen gekoppelt | Ziel-spezifisch |

**Metapher:** Fitness als Sein, Readiness als Tun.

---

## 2. Sportwissenschaftliche Basis

Die Frage „bin ich bereit?" hängt physiologisch von **vier Dimensionen** ab:

1. **Aerobes Fundament** (Chronic Training Load, CTL)
2. **Spezifische Ausdauer** (Long Runs)
3. **Pace-Spezifität** (Training in/nahe Ziel-Rennpace)
4. **Aktuelle Leistungsfähigkeit** (vDOT aus Best Efforts)

Zusätzlich — nur in der Tapering-Phase relevant:
5. **Form / Training Stress Balance** (CTL minus ATL)

Diese Dimensionen sind in der Trainingsliteratur etabliert (Daniels, Pfitzinger, Coggan, Banister-Modell).

**Was Konsistenz** (Anzahl Trainingstage) **nicht ist:** eine eigenständige physiologische Säule. Konsistenz ist **indirekter Prädiktor via CTL** — wer konsistent trainiert, baut CTL auf. Konsistenz wird daher als Warning-Modifier behandelt, nicht als gleichwertige Säule.

---

## 3. Die vier Säulen

### 3.1 Volumen (Chronic Training Load)

**Metrik:** CTL — 42-Tage exponentiell gewichteter Mittelwert der täglichen TSS (Training Stress Score).

- `rTSS = (Dauer_Sekunden × IF²) / 3600 × 100` mit `IF = Schwellen-Pace / aktueller Pace`

> **Korrigiert 2026-08-25 (minsaga #786).** Hier stand
> `rTSS = (Dauer_Sekunden × IF²) / 3600` mit
> `IF = aktueller Pace / Schwellen-Pace`. Zwei Fehler:
>
> 1. **Der Bruch war invertiert.** Pace steht in Sekunden je
>    Kilometer — kleiner heisst schneller. Mit der alten Formel
>    ergäbe ein schnellerer Lauf ein KLEINERES IF und damit weniger
>    Belastung.
> 2. **Der Faktor 100 fehlte.** Nach der Konvention ist eine Stunde
>    an der Schwelle 100 Punkte, nicht 1.
>
> Zusammen hätten alle CTL-Werte um 1 gelegen und jede Volumen-Säule
> bei 0. Der Code rechnet seit jeher richtig
> (`TrainingLoadAnalyzer.swift`); korrigiert wird das Dokument,
> bevor jemand die Formel als Referenz nimmt.
>
> Der Code kappt zusätzlich auf IF 0,4 bis 1,3 — gegen GPS-Ausreisser.
- Setzt voraus: Schwellen-Pace bekannt (aus Threshold-Test, siehe §7)
- Erste ~6 Wochen: CTL noch nicht „eingeschwungen"

**Zielzeit-abhängige Benchmarks** (Daumenregel):

| Distanz & Ziel | CTL in den letzten 4 Wochen |
|---|---|
| 5K Sub-25 | 35–50 |
| 10K Sub-55 | 50–70 |
| HM Sub-2:00 | 40–55 |
| HM Sub-1:45 | 55–70 |
| HM Sub-1:30 | 70–90 |
| M Sub-4:30 | 50–65 |
| M Sub-4:00 | 60–80 |
| M Sub-3:30 | 80–100 |
| M Sub-3:00 | 100–130 |

**Readiness-Mapping:** Linear skaliert. 100 % = Obergrenze der Ziel-Range. < 40 % des Targets ergibt Score 0.

### 3.2 Langlauf (bzw. Aerobic Base für 5K/10K)

**Für Halbmarathon und Marathon:**
- **Schwellwert:** ≥ 18 km (HM) bzw. ≥ 28 km (M) — **oder** ≥ 105 min (HM) bzw. ≥ 150 min (M)
  Dauer-Regel (Ergänzung Aug 2026): Die reine km-Schwelle bestraft langsamere
  Läufer — ein 16-km-Lauf über 1:45 h ist ein voller Long Run (Pfitzinger
  definiert Long Runs über die Dauer).
- **Metriken:** Anzahl Long Runs in letzten 12 Wochen + längste Distanz
- **Targets:**
  - HM: 6–10 Long Runs; längster ≥ 22 km
  - Marathon: 6–10 Long Runs; längster 32–35 km (mindestens 1 × ≥ 32 km)

**Für 5K und 10K (umbenannt: „Aerobic Base"):**
- Längster Einzellauf ≥ 60 min (5K) bzw. ≥ 75 min (10K)
- Targets:
  - 5K: mindestens 1 Lauf ≥ 60 min alle 2 Wochen
  - 10K: mindestens 1 Lauf ≥ 75–90 min alle 2 Wochen

**Score:** kombinierbar aus Anzahl (70 %) + längster Distanz (30 %).

### 3.3 Pace-Spezifität

**Metrik:** Kilometer im Ziel-Pace-Band über die letzten 8–10 Wochen.

**Ziel-Pace-Band:**
- Halbmarathon: HM-Ziel-Pace ± 10 Sek/km (≈ Laktatschwelle)
- Marathon: Marathon-Ziel-Pace (MP) ± 10 Sek/km
- 10K / 5K: entsprechende Ziel-Pace ± 15 Sek/km

**Was zählt:**
- Kontinuierliche Tempo-Einheiten (z. B. 20 km im MP)
- Marathon-Specific Workouts (z. B. 3 × 8 km @ MP mit Pausen)
- **Nicht** zählen: Intervalle deutlich schneller als Rennpace (VO2max-Bereich)

**Targets:**

| Distanz | Gesamt-Kilometer in Ziel-Pace (letzte 8 Wochen) | Anzahl spezifische Workouts |
|---|---|---|
| 5K | 20–30 km | 6–10 |
| 10K | 30–40 km | 6–8 |
| HM | 40–60 km | 4–6 |
| M | 60–100 km | 4–8 |

### 3.4 Performance (vDOT)

**Automatische Schätzung** aus Trainingsdaten — keine Race-Zeit-Eingabe erforderlich.

**Primär-Ansatz:** Best Recent Efforts + Daniels-Extrapolation
- Die App sucht in den letzten 30–45 Tagen nach besten Effort-Segmenten:
  - 1 km, 5 km, 10 km, 21,1 km schnellstes Tempo
- Jeder Effort → vDOT-Wert via Daniels-Tabelle → Marathon-Prognose
- Mehrere Prognosen werden gewichtet:
  - Längere Efforts (≥ 10 km) höheres Gewicht
  - Neuere Efforts höheres Gewicht (exponentieller Decay über 30 Tage)
- **Training-vs-Race-Korrektur:** Trainings-Efforts typisch 3–5 % langsamer als Race-Efforts → Korrekturfaktor anwenden

**Sekundär-Sanity-Check:** Critical Pace aus Log-Plot (Pace vs. Duration). Bei starker Divergenz zu vDOT → Konfidenzbereich schmaler zeigen.

**Optionaler Anker:** Race-Entry (siehe §8). Echte Rennzeit bekommt starken Gewichtungs-Bonus, verblasst nach 30 Tagen auf normale Gewichtung.

**Resultat:**

```
Prognose Marathon: 3:38 (Range 3:32 – 3:45)
vDOT: 48 ± 2
Datenbasis: 12 Trainings-Efforts in den letzten 35 Tagen
```

**Readiness-Score:** Prognose vs. Zielzeit.
- Prognose ≥ 5 min schneller als Ziel → 100 %
- Prognose = Ziel → 80 %
- Prognose 10 min langsamer → 50 %
- Etc.

---

## 4. Gewichtung pro Distanz

Die vier Säulen sind **nicht gleich wichtig** — kürzere Distanzen sind performance-sensitiver, Marathon ist volumen-intensiver.

| Säule | 5K | 10K | HM | M |
|---|---|---|---|---|
| Volumen | 15 % | 20 % | 20 % | 30 % |
| Aerobic Base / Langlauf | 10 % | 15 % | 15 % | 25 % |
| Pace | 30 % | 30 % | 30 % | 20 % |
| Performance | 45 % | 35 % | 35 % | 25 % |

---

## 5. Score-Berechnung

**Modell:** Gewichtete Summe + Warning-Flags.

```
Score = Σ (Säulenwert_i × Gewicht_i)

Warning-Levels pro Säule:
  < 30 %     → "Kritisch" (rot)
  30 % – 50 %→ "Ausbaufähig" (amber)
  ≥ 50 %     → OK
```

Der Score ist **motivierend-aggregiert** (kompensierbar), aber die Warnings zeigen **ehrlich** wo die Lücke ist.

**Beispiel Marathon-User:**

```
Readiness 76 %

Volumen           85 ✓
Langlauf          80 ✓
Pace              40 ⚠  „Zu wenig in Marathon-Pace — baue MP-Einheiten auf"
Performance       80 ✓
```

**Qualitative Einordnung** (Minsaga-Sprache — ergänzt die Zahl):

| Score | Einordnung | Coach-Sprache |
|---|---|---|
| 90–100 | Renn-bereit | „Du hast alles getan. Vertrau darauf." |
| 80–89 | Auf Kurs | „Solider Stand. Die letzten Wochen entscheiden." |
| 70–79 | Im Aufbau | „Fundament steht. Jetzt die Spezifität schärfen." |
| 60–69 | Früh in der Saga | „Noch Raum zum Wachsen." |
| < 60 | Ehrliche Bestandsaufnahme | „Ziel überprüfen oder Zeitplan strecken?" |

---

## 6. Konsistenz als Warning-Modifier

Konsistenz ist **keine Säule**, sondern hat zwei Rollen:

### 6.1 Warning-Modifier in der Volumen-Säule

**Messung:** Plan-Compliance in den letzten 42 Tagen — % der geplanten Einheiten absolviert.

(Bei Minsaga existiert ein Plan, sobald ein Ziel existiert; daher kein Fallback nötig.)

**Logik:**

| Szenario | Coach-Reaktion |
|---|---|
| CTL hoch + Konsistenz < 50 % | „Hohe Fitness auf dünner Basis — Verletzungsrisiko. Konsistenter trainieren." |
| CTL moderat + Konsistenz hoch | „Solide, stabile Basis." (positiver Kontext in Volumen-Säule) |
| CTL niedrig + Konsistenz niedrig | „Volumen und Rhythmus beide im Aufbau." |

### 6.2 Rhythmus-Karte

Eigene kleine Karte im Heute-Dashboard (neben Biometrics):

```
Rhythmus
28 Trainingstage in 42
Solide, 4–5 Einheiten pro Woche
```

Ziel: Verhaltens-Feedback unabhängig vom Readiness-Score.

**Warnbereich:**
- < 43 % (= < 18 aktive Tage) → „Unregelmäßig — Verletzungsrisiko"
- > 86 % (= > 36 aktive Tage) → „Sehr hohes Volumen, beobachte Erholung"

---

## 7. Form (TSB) — Tapering-Phase

**Metrik:** TSB = CTL − ATL (Acute Training Load, 7-Tage exponentieller Mittelwert).

**Interpretation:**
- TSB +5 bis +15: optimal getapert
- TSB 0 bis +5: akzeptabel
- TSB −5 bis −20: zu wenig Taper, müde Beine
- TSB < −20: overreached — **Warnsignal**
- TSB > +15: zu langes/intensives Taper, möglicher Formverlust

**Sichtbarkeit:** Form-Anzeige erscheint **plan-gesteuert** — ab Beginn der Tapering-Phase prominent. Länge der Tapering-Phase je nach Distanz:
- Marathon: 3 Wochen
- HM: 2 Wochen
- 10K: 1 Woche
- 5K: 4–7 Tage

Während der Build-Phase spielt TSB keine Rolle für Readiness (natürliche Akkumulation erwünscht).

---

## 8. Datenquellen

### 8.1 Automatisch aus Trainings-Daten
- GPX/FIT-Dateien → Pace, Distanz, HR, Elevation, Timestamps
- Daraus: CTL, ATL, TSB, Long-Run-Historie, Pace-Verteilung, Best Efforts

### 8.2 Threshold-Test (Onboarding + periodisch)

**Standard:** 20-Min-Threshold-Test (Pfitzinger-Style).
- Durchgeführt in Woche 2–3 des Trainings
- Durchschnittspace der 20 min = Threshold Pace ≈ LT2
- Basis für CTL-Berechnung

**Re-Test:** alle 6–8 Wochen, integriert in den Trainingsplan (z. B. am Ende einer Recovery-Woche).

**Fallback bei ausgelassenem Test:** HF-basierte LTHR-Schätzung aus Tempoläufen im letzten Monat.

**Optional (ambitioniert):** Kritische-Pace-Test-Paket über 4–6 Wochen (3-Min, 12-Min, 30-Min all-out) für präzisere CP-Bestimmung.

### 8.3 Race-Entry-Feature

User kann historische und aktuelle Rennen erfassen:
- Rennname, Distanz, Zeit, Datum, Bedingungen
- Zeit fließt in vDOT-Schätzung ein (starker Gewichtungs-Bonus)
- Bonus verblasst nach 30 Tagen → Auto-Schätzung aus Training übernimmt
- Rennen sind **Teil der Saga** — erscheinen in Historie/Timeline (Meilensteine)

---

## 9. Goal-Lifecycle

### 9.1 Goal-Setup

User setzt **Ziel + Datum** (Rennen + Kalenderdatum). **Zielzeit ist optional:**

**Modus A: Mit Zielzeit** (User weiß was er will)
- Targets sofort berechnet
- Kalibrierung Woche 4

**Modus B: Ohne Zielzeit** (User will erst schauen)
- Rennen + Datum reicht
- 4 Wochen Daten sammeln
- Kalibrierungs-Moment: „Basierend auf deinem Training sieht Sub-1:48 realistisch aus. Mutiger Griff: Sub-1:45. Was nimmst du?"
- Entscheidung mit Daten

### 9.2 Baseline (Woche 1–3)

- Motivierender Placeholder in Readiness-Bereich: *„Readiness kommt — die nächsten Wochen lernen wir dich kennen."*
- Onboarding-Fragebogen für initiale Grobschätzung (aktueller Wochenumfang, letzter langer Lauf, ggf. letzte Rennzeit)
- Optional: Import historischer FIT-Dateien für sofortige Readiness

### 9.3 Kalibrierung (Woche 4)

Nach Threshold-Test + 4 Wochen Daten:

> *„Wir haben deine Schwelle getestet und 4 Wochen beobachtet — hier ist dein scharfes Bild. Ab hier wird's präzise."*

Sichtbarer, erklärter Shift der Säulen-Targets. Bei Modus B: Zielzeit wird jetzt festgelegt.

### 9.4 Build (Woche 5 bis Tapering-Start)

- Readiness zeigt aktuellen Stand, Säulen-Warnings bei Schwächen
- Coach gibt **Suggestion-Mode**-Vorschläge zur Plan-Anpassung (User akzeptiert/ablehnt)
- Readiness-Trend sichtbar (kompakt in Goal-Card, tief in Fortschritt-Sektion)

### 9.5 Tapering

- Plan-gesteuerter Trigger: Form-Anzeige wird prominent
- Volumen reduziert, Pace erhalten
- TSB-Progression zeigt Entlastung

### 9.6 Race Day

**Ruhiger, warmer Moment ohne Zahlen.**

- Nordlicht-Gradient als Hintergrund
- Große Fraunces-Headline (z. B. „Heute ist dein Tag.")
- Countdown bis Start
- Ein einziger Coach-Satz: „Du hast alles getan. Jetzt lauf deine Saga."
- **Keine Readiness-Metriken** — der User braucht jetzt Vertrauen, keine Daten

### 9.7 Post-Race (2 Wochen)

**Kompakte Würdigung** im Dashboard:
- Rennname, Zeit, Ziel vs. Ergebnis
- Ein Satz Coach-Einordnung
- Tap führt zur tiefen Analyse in der Fortschritt-Sektion (Splits, HF-Verlauf, Pacing-Consistency, Vergleich mit Ziel)

Nach 2 Wochen oder bei neuem Ziel ersetzt durch Empty State (*„Jede Saga braucht ein Ziel."*) oder neue Goal-Card.

**Rennen bleibt in Race-Entry-Historie** — ist Teil der Saga.

---

## 10. Edge Cases

### 10.1 Pause / Verletzung

**Auto-Erkennung:** ≥ 7 Tage ohne Training → Prompt: *„War alles ok? Krank? Verletzt?"*
User kann bestätigen, Zeitraum wird als Pause markiert (kein Strafen der Konsistenz-Metrik, physiologische Realität aber ehrlich).

**Coach reagiert warm:** *„Zwei Wochen Pause. Der Körper hat Zeit gebraucht. Jetzt vorsichtig wieder einsteigen."*

**Langzeit-Pause (≥ 4 Wochen):** App stößt Ziel-Gespräch an: *„Nach 6 Wochen Pause — Marathon in 8 Wochen wäre riskant. Ziel verschieben?"*

### 10.2 Overreaching

- CTL-Anstieg > 5 Punkte/Woche über 4 Wochen → Warning *„Dein Volumen wächst schnell. Beobachte Erholung, HRV-Trend, Schlaf."*
- Kombiniert mit HRV-Drop oder Ruhepuls-Erhöhung → deutlichere Warnung

### 10.3 Goal-Upgrade

User setzt Ziel hoch (Sub-4:00 → Sub-3:45).

**Warning vor Commit:**
> *„Sub-3:45 erfordert höhere CTL, schnellere MP-Einheiten und mehr Long Runs. Deine aktuelle Readiness dafür wäre 58 % (aktuell 88 % für Sub-4:00). Trotzdem commiten?"*

User trifft informierte Entscheidung.

### 10.4 Over-Ready

User ist über dem Ziel vorbereitet (CTL 110 bei Target 90, Prognose 3:35 für Ziel 3:45).

- Score-Cap bei 100 %
- Coach-Hinweis: *„Deine aktuelle Form prognostiziert 3:35 — du könntest ein schnelleres Ziel angehen. Zielzeit anpassen?"*

### 10.5 Trainings-Phasen mit niedrigem Score

In der Base-Phase (Woche 1–6) ist Pace-Säule naturgemäß niedrig — MP-Training steht noch nicht auf dem Plan.

**Coach kontextualisiert:** *„Du bist in Phase 1 — Volumen baut sich auf. Pace-Spezifität kommt ab Woche 7. 42 % ist hier normal und erwartet."*

Kein „Expected Range" auf dem Progress-Ring — der Coach erklärt.

### 10.6 Mehrere Ziele / Tune-up-Rennen

**Ein primäres Ziel** pro Plan. Tune-up-Rennen (z. B. HM 6 Wochen vor Marathon) sind **Teil des Plans**, kein separater Readiness-Score.

Coach gibt ggf. Pacing-Empfehlung: *„Laufe diesen HM bei 90 % Effort, nicht PR versuchen — das Ziel ist Berlin."*

---

## 11. AI Coach — Integration

### 11.1 Dreistufige Architektur

1. **Rule-based** — regelbasierter Insight-Generator für tägliche Kurz-Einordnung (morgens). Kostengünstig, zuverlässig.
2. **Lokale iOS-KI** (Apple Intelligence / Foundation Models) — für erweiterte Einschätzungen, Post-Training-Feedback. On-device, datenschutzfreundlich.
3. **Cloud-KI** (Claude / OpenAI) — Fallback für komplexe Einschätzungen, die lokal nicht reichen.

### 11.2 Trigger-Events

Der Coach-Insight auf dem Dashboard aktualisiert sich bei:
- **Täglich morgens** — regelbasierte Kurz-Einordnung
- **Nach Training absolviert** — LLM-generiertes Feedback
- **Neues Ziel gesetzt** — Onboarding-Message
- **Readiness-Säule signifikant geändert** — Einordnung
- **Pause erkannt** — warme Nachricht
- **Alle X Tage ohne Ereignis** — Check-in

### 11.3 Ton

Style Guide §10: Persönlich, warmherzig, motivierend. Duzend, korrekte Umlaute. Nüchtern bei Daten, warm bei Kontext.

**Nicht:** Motivations-Floskeln, Bevormundung, Gamification-Sprache.
**Sondern:** Literarische Beobachtung. „Lass die Beine sich erinnern — die Geschwindigkeit kommt zurück."

---

## 12. Trainingsplan

### 12.1 Generierung (Hybrid)

AI kombiniert aus **wissenschaftlich fundierten Bausteinen**:
- Long-Run-Progression
- Threshold-Workouts (T-Pace nach Daniels)
- Marathon-Specific Workouts
- VO2max-Intervalle
- Recovery-Runs
- Stride-Einheiten

**Eingaben:** Ziel, Datum, Wochen verfügbar, aktuelle Fitness, Trainingstage/Woche.

**Keine Blackbox:** Jede Einheit hat eine begründete Funktion („diese Einheit wegen Pace-Spezifität").

### 12.2 Plan-Anpassung (Suggestion-Mode)

Wenn eine Säule schwächelt, schlägt der Coach konkrete Änderungen vor:

> *„Pace-Spezifität ist dein dünner Punkt. Vorschlag für nächste Woche: Donnerstag 10 km locker → 3 × 3 km @ MP."*

User swipe-akzeptiert oder -ablehnt. **Coach berät, User entscheidet.**

### 12.3 Tune-up-Rennen im Plan

Rennen vor dem Hauptziel werden als **Plan-Events** eingeplant, nicht als separate Ziele. Coach passt Pacing-Empfehlung entsprechend an.

---

## 13. Beziehung zu Fitness Level V2

### 13.1 Komplementär, nicht konkurrierend

| Ebene | Fitness Level V2 | Goal Readiness |
|---|---|---|
| Dashboard-Position | Ausdauer + Kraft Cards (kompakt) | Goal-Card (prominent) |
| Datenbasis | Ziel-unabhängige physiologische Fitness | Ziel-spezifisches Training der letzten Wochen |
| Zeitraum | Dauerhaft aufbauend (Level permanent) | Temporär (an Rennen gekoppelt) |
| Metapher | Wer bin ich | Wo stehe ich gerade |

### 13.2 Gemeinsame Datenquelle, unterschiedliche Sichten

Beide Systeme nutzen:
- CTL / Trainingsvolumen
- vDOT / Performance-Schätzung
- Long-Run-Historie

Aber verarbeiten diese unterschiedlich:
- **Level V2:** normalisiert `sqrt(CTL/90) × 100` → fixe populationsreferenzierte Level-Grenzen
- **Goal Readiness:** relativ zu ziel-abhängigen Targets, zeit-gebunden an ein Rennen

### 13.3 Narrative Kombination im Dashboard

```
Ausdauer: Level 4 · In voller Stärke · 82         ← dauerhaftes Sein
Kraft:    Level 2 · Im Aufbau · 54

Marathon Berlin · 38 Tage
Readiness 78 %                                     ← temporäres Tun
  Volumen 85 · Langlauf 80 · Pace 40 · Performance 80
```

---

## 14. Offene Punkte für Implementierung

- [ ] Konkrete Gewichts-Kurven für Säulen-Score-Berechnung (linear vs. gewichtet in Richtung Zielbereich)
- [ ] vDOT-Tabelle und Riegel-Formel in Python implementieren
- [ ] Pace-Zonen-Erkennung (HR-basiert, wenn kein Pace-Ziel explizit)
- [ ] Threshold-Test-Workflow im Plan-Editor
- [ ] Race-Entry-Feature (CRUD-Flow)
- [ ] Post-Race-Analyse-Komponenten (Splits, HF-Verlauf, Pacing-Consistency)
- [ ] Overreaching-Detection-Algorithmus (CTL-Wachstumsrate-Schwellen)
- [ ] Tapering-Detection aus Plan (Phase-Erkennung)
- [ ] AI-Coach-Insight-Templates und -Trigger-Logik
- [ ] Plan-Baustein-Bibliothek (Daniels-basierte Workouts)
- [ ] Integration mit Apple Intelligence / Foundation Models (iOS-App-Phase)

---

## 15. Referenzen

- [BRAND_STYLE_GUIDE.md](BRAND_STYLE_GUIDE.md) — Marken-Sprache, Farben, Typografie
- [FITNESS_LEVEL_SYSTEM_V2.md](FITNESS_LEVEL_SYSTEM_V2.md) — Level-System (Ausdauer/Kraft)
- [DOMAIN_MODEL.md](DOMAIN_MODEL.md) — Entities-Überblick
- [TRAINING_CONTEXT.md](TRAINING_CONTEXT.md) — Trainingskontext

**Trainingswissenschaftliche Basis:**
- Daniels, J. (2013). *Daniels' Running Formula* — VDOT-System, T-Pace, MP-Training
- Pfitzinger, P. & Douglas, S. (2019). *Advanced Marathoning* — Trainingsplan-Strukturen, Tapering
- Coggan, A. & Allen, H. (2010). *Training and Racing with a Power Meter* — CTL/ATL/TSB (Banister-Modell)
- Jones, A. et al. *Critical Power Concept* — moderne Threshold-Bestimmung
- Midgley, A. et al. *Training to Enhance Distance Running* — Long-Run-Physiologie
