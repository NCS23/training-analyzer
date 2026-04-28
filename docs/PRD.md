# minsaga — Product Requirements Document

> **Status:** v0 (Skelett) · 2026-04-27
> **Single Source of Truth.** Wenn etwas Produkt- oder Konzept-Bezogenes nicht hier steht, ist es **nicht spezifiziert**.
> Visuelle Spezifikationen (Komponenten, Tokens, Brand) leben **nicht** hier — siehe Verlinkungen.

---

## Inhaltsverzeichnis

- [0. Status & Versionierung](#0-status--versionierung)
- [1. Vision & Positioning](#1-vision--positioning) 🎙️ *Interview S1*
- [2. Zielgruppe & Jobs](#2-zielgruppe--jobs) 🎙️ *Interview S2*
- [3. Information Architecture](#3-information-architecture)
- [4. Feature-Spezifikation pro Tab](#4-feature-spezifikation-pro-tab)
- [5. Querschnittskonzepte](#5-querschnittskonzepte)
- [6. Bestand & Migration: was existiert, was wird umgebaut](#6-bestand--migration-was-existiert-was-wird-umgebaut)
- [7. Was wir bewusst NICHT machen](#7-was-wir-bewusst-nicht-machen)
- [8. Offene Fragen / Entscheidungs-Backlog](#8-offene-fragen--entscheidungs-backlog)
- [9. Glossar & Vokabular](#9-glossar--vokabular) 🎙️ *Interview S3*
- [Anhang A: Versionshistorie](#anhang-a-versionshistorie)

---

## Verwandte Dokumente

| Bereich | Dokument | Zweck |
|---|---|---|
| **Brand & Voice** | [`design/BRAND_STYLE_GUIDE.md`](design/BRAND_STYLE_GUIDE.md) | Visuelle Sprache, Tonalität, Designprinzipien |
| **Domain-Modell** | [`reference/DOMAIN_MODEL.md`](reference/DOMAIN_MODEL.md) | Entities, Relations, Felder |
| **Trainingskontext** | [`reference/TRAINING_CONTEXT.md`](reference/TRAINING_CONTEXT.md) | HM Sub-2h Use Case |
| **Daten-Formate** | [`reference/CSV_FORMAT_EXAMPLES.md`](reference/CSV_FORMAT_EXAMPLES.md), [`reference/FIT_IMPORT_NOTES.md`](reference/FIT_IMPORT_NOTES.md) | Import-Formate |
| **Engineering** | [`engineering/`](engineering/) | Code-Standards, Layout-Regeln, Review-Checklisten |
| **Figma File** | [`vfjxFkAugXZCZPRVyADQRY`](https://www.figma.com/design/vfjxFkAugXZCZPRVyADQRY/) | Komponenten, Variants, Tokens (live) |
| **Nordlig DS** | [NCS23/nordlig-design-system](https://github.com/NCS23/nordlig-design-system) + Storybook | Design-System Komponenten + Code |
| **Archiv** | [`archive/`](archive/) | Historische Konzepte (superseded), bewusst stehen gelassen für Nachvollziehbarkeit |

---

## 0. Status & Versionierung

| Datum | Version | Was geändert | Begründung |
|---|---|---|---|
| 2026-04-27 | v0 | Skelett angelegt | Konsolidierung der bisher fragmentierten Konzept-Docs (`REDESIGN_KONZEPT.md`, `DASHBOARD_LAYOUT_PROPOSAL.md`, `GOAL_READINESS_CONCEPT.md`, `AI_ANALYSIS_INTEGRATION.md`) |

**Versionierungs-Konvention:**
- **v0**: Skelett, Inhalte werden im Interview befüllt
- **v1.0**: Erste vollständige Version nach Interview-Sessions S1–S3
- **v1.x**: Konkretisierungen, Bugfixes, geringfügige Ergänzungen
- **v2.0**: Substantielle Konzept-Änderung (z.B. neue Tab-Struktur)

---

## 1. Vision & Positioning

> 🎙️ **Interview Session 1** — Vision & Anti-Vision.
> Wird in einem strukturierten Dialog mit Nils befüllt.

### 1.1 Was ist minsaga?

> minsaga ist ein persönlicher Lauf-Begleiter, der dich auf dem Weg zu deinem selbstgesteckten Wettkampfziel führt — nicht über nackte Zahlen, sondern über die Geschichte, die du dabei schreibst.

**Drei Kern-Eigenschaften:**

1. **Eine Präsenz, drei Stimmen** — Coach beim Planen, Zeuge an Meilensteinen, Begleiter im Alltag. (Details siehe §1.3.1)
2. **Der Plan reagiert auf dich** — kein statischer 14-Wochen-Plan. minsaga schlägt nach jedem Lauf, jede Woche und auf deinen Anstoß Anpassungen vor — transparent, mit Begründung, immer zur Bestätigung. (Details siehe §5.8)
3. **Saga-Tonfall an Schwellen, sachlich im Alltag** — Bedeutung wird sichtbar an Race-Tag, Comeback, persönlicher Bestleistung. Im Alltag bleibt der Ton ruhig und beobachtend. (Details siehe §1.3.2)

### 1.2 Was ist minsaga NICHT?

minsaga grenzt sich bewusst ab. Sieben Anti-Patterns:

| # | Pattern | Beispiele | Warum nicht |
|---|---|---|---|
| 1 | **Social-Sport-Plattform** | Strava, Nike Run Club | Keine Kudos, keine Leaderboards. Dein Training, deine Geschichte. |
| 2 | **Daten-Aggregator** | Garmin Connect, Apple Fitness, Runtastic | Daten ohne Einordnung sind kalt. minsaga zeigt Bedeutung, nicht nur Werte. |
| 3 | **Streak-Shaming-App** | (Duolingo-Pattern) | Wenn du einen Tag aussetzt, ist das OK. Keine Drohung, keine Schuld. |
| 4 | **Coach-als-Autorität** | TrainingPeaks (mit Coach) | Ein Begleiter, kein Kommandeur. Vorschlagsmodell, du entscheidest. |
| 5 | **Charakter-Chatbot** | (Maskottchen-Apps mit Eigennamen) | Eine namenlose Präsenz, kein Charakter, der spricht. |
| 6 | **Plattitüden-Generator** | (Kalenderspruch-Apps) | Keine Pseudo-Weisheit. Beobachten, nicht predigen. |
| 7 | **One-Size-Fits-All-Plan** | Fertige PDF-Pläne, statische App-Pläne | Der Plan reagiert auf dich. Statisches passt nicht zu echten Verläufen. |

**Gemeinsamer Nenner der Negativ-Beispiele:** *„Zu unpersönlich."* — Sie lassen den Nutzer mit Daten oder Templates allein. minsaga bleibt persönlich.

### 1.3 Leitprinzipien

#### 1.3.1 Eine Präsenz, drei Stimmen

Der Begleiter wechselt seine Rolle je nach Moment:
- **Coach** wenn etwas zu tun ist (vorausschauend, handlungsleitend)
- **Begleiter** wenn etwas zu fühlen ist (still präsent, geduldig)
- **Zeuge** wenn etwas zu würdigen ist (beobachtend, an Meilensteinen)

→ Vollständig spezifiziert in [`archive/AI_PRESENCE_CONCEPT.md`](archive/AI_PRESENCE_CONCEPT.md). Wird ggf. nach §5.3 migriert.

#### 1.3.2 Saga-Tonfall an Schwellen, sachlich im Alltag

„Saga"- und „Kapitel"-Wortmaterial **nur an konkreten Schwellen**:
- Empty State (kein Ziel gesetzt)
- Race Day
- Post Race
- Tapering-Phase
- Comeback nach Pause
- Persönliche Bestleistung

Im Alltag (Wochenansicht, Session-Detail, Stat-Boxen) bleibt der Ton sachlich.

#### 1.3.3 Nüchtern bei Daten, warm bei Kontext

Stat-Zahlen, HR-Tabellen, Charts, Settings-Pages und Form-Validation **bleiben pur und sachlich** — kein motivierender Beitext, keine Wertung.

**Aber:** Bei Bedarf muss eine **on-demand-Einordnung** verfügbar sein. Beispiel: „TSB +8" — was heißt das? Per Tap/Hover/Info-Icon erscheint eine Erklärung in Begleiter-Sprache.

→ Pattern siehe §5.6 (Voice & Copy).

#### 1.3.4 Beobachtend statt bewertend

> *„Solide Einheit. Form blieb sauber, RPE 7/10."*  ✅
> *„Super gemacht! 🎉"*  ❌

Anerkennung des Aufwands ohne Notenvergabe. Kein Hochjubeln.

#### 1.3.5 Direkte Anrede in 2. Person — kein „wir"

Die App spricht zu „dir", nicht als „wir". Es gibt keine Wir-Instanz (kein Team, keine Crew, keine App-Stimme im Plural). Die Präsenz ist namenlos und einzeln.

#### 1.3.6 Lagom — keine Plattitüden, kein Trainings-Jargon als Verb

Verbotene Muster (Beispiele aus Iteration):

| ❌ | Warum |
|---|---|
| *„Ruhe ist Training — dein Körper adaptiert jetzt."* | Kalenderspruch + Jargon („adaptieren") |
| *„Lass die Beine sich erinnern — die Geschwindigkeit kommt zurück."* | Yoga-Lehrer-Stil, übertrieben poetisch |
| *„Setz den Horizont — wir zeigen dir den Weg dorthin."* | Wir-Plural + Kalenderspruch |
| *„Optimal getapert · halte diese Form"* | „getapert" als Verb (Jargon) |

Typografisch: Lange Gedankenstriche (—) vermeiden. Stattdessen Punkt oder kurzer Strich (–).



### 1.4 Inspirationen / Anti-Inspirationen

*[tbd nach S1 — welche Apps inspirieren, welche stoßen ab, warum]*

---

## 2. Zielgruppe & Jobs

> 🎙️ **Interview Session 2** — User Journey & Jobs To Be Done.

### 2.1 Persona

*[tbd nach S2 — Nils selbst als Persona-Typ: ambitionierter Hobbyläufer mit Wettkampfziel; Datenliebe + Coach-Bedürfnis]*

### 2.2 User Journey

#### 2.2.1 Mikro: Eine typische Trainingswoche (Aufbau/Belastung)

| Tag | Training | App-Touchpoints |
|---|---|---|
| **Mo** | Lauf | morgens: Heute-Blick (Goal-Status + Today-Session) · während: nur Apple Watch · nach: Upload FIT + Analyse + Insights |
| **Di** | Krafttraining | nach Training: Upload + Auswertung |
| **Mi** | Lauf | morgens: Workout-Export auf Watch (📍 Pain Point) + Heute-Blick · während: Watch · nach: Upload + Auswertung |
| **Do** | Krafttraining | nach Training: Upload + Auswertung |
| **Fr** | Lauf | wie Mi |
| **Sa** | Lauf | wie Mi |
| **So** | Ruhetag | **abends: Wochen-Review + Vorbereitung kommende Woche + Workout-Export für Mo** |

Wochenstruktur: **4 Läufe + 2 Krafttrainings + 1 Ruhetag**

**Zwischendurch (anlassbezogen):**
- *„Wo stehe ich bezüglich Ziel?"* → Goal Readiness (Heute oder Analyse)
- *„Wie habe ich mich entwickelt?"* → Analyse-Tab
- *„Ich habe ein Trainings-Problem (Technik, Pace, Verletzung)"* → AI Coach Chat (FAB)

#### 2.2.2 Makro: Wettkampf-Vorbereitung (HM Sub-2h, ~16 Wochen)

| Phase | Wochen vor Race | Was ich brauche | Tab/Feature |
|---|---|---|---|
| Ziel-Setting | 16 | Plan erstellen, Zielzeit definieren | Plan |
| Aufbau | 12–14 | Wochenstruktur, Konsistenz prüfen | Heute, Training |
| Belastung | 6–10 | Form überwachen, Überlastung erkennen | Analyse |
| Tapering | 1–2 | Form maximieren — Wochenstruktur bleibt ähnlich, aber Goal-Readiness-Card und KI-Insight zeigen Tapering-spezifische Inhalte | Analyse, Heute |
| Race-Tag | 0 | **Vor Race:** Pacing-Strategie geklärt + verfügbar zum Nachschlagen · **Während Race:** Pacing-Strategie auf Mobile/Watch, „Worauf achten"-Hinweise · **Companion (MVP-Feature):** Watch-App begleitet aktiv während des Laufs | Plan (Pacing) + Companion-Watch-App |
| Reflexion | +1 | Auswertung „Wie war es?" + Erkenntnisse fließen in neuen Trainingsplan ein | Analyse + Plan |

#### Race-Day-spezifische Bedürfnisse (jetzt MVP-Features)

- **Streckenprofil laden** (GPX/Höhenprofil) — beeinflusst Pacing
- **Versorgungs-Punkte** auf der Strecke (Wasser, Verpflegung) → **Gel-Strategie** ableitbar
- **Pacing-Strategie auf der Watch** während des Laufs (gleichmäßig / negativ / konservativ)
- **Companion-Mode**: Watch-App begleitet aktiv (Splits, Pace-Hinweise, ggf. Begleiter-Stimme)

→ Mit nativer iOS-App + Apple-Watch-Companion realisierbar (siehe §6.8 Strategie-Pivot).

#### Wochen-Review (Pflicht, automatisch)

Am Ende jeder Woche:
- Auswertung der Woche (Plan-Treue, Volumen, Intensitätsverteilung, Form-Entwicklung)
- **Vorschlag für Trainingsanpassung der Folgewoche** (siehe §5.7 Plan Adaptation)

Nach jedem einzelnen Training **bei Bedarf**:
- Wenn ein wichtiger Insight rauskommt (Form kippt, Verletzungssignal, Pace-Sprung) → eigene Adaptions-Empfehlung

#### Equipment-Tracking (Vision)

- Pro Training festhalten/sehen: **welche Schuhe** wurden getragen
- Kilometerstand pro Schuh tracken → **Ausmusterungs-Warnung** bei Erreichen Lebensdauer (typisch 600–1000 km)

#### 2.2.3 Workflow Pain Points

| Pain | Heute (Stand 2026-04) | Soll |
|---|---|---|
| **Workout-Export auf Apple Watch** | 3-Schritt-Prozess: Web-App → iPhone-Download → Health Fit-Import → Apple Watch-Export | Ein Tap. Vermutlich erst mit nativer iOS-App + Watch-Companion möglich. Siehe `MEMORY.md` Native iOS App Strategie. |
| **Web-only Mobile-Zugriff** | Browser-Reibung auf dem iPhone | Native iOS-App (siehe oben) |

### 2.3 Jobs To Be Done

Format: *„Wenn [Situation], möchte ich [Job], damit [Outcome]."*

#### Tagesbezogene Jobs

1. **Sonntag-abends-Vorbereitung**
   *„Wenn ich Sonntag-abend die kommende Woche durchgehe, möchte ich sehen was ansteht und das Workout für Montag auf meine Watch bekommen, damit ich morgen direkt starten kann."*
   → **Plan-Tab** + **Workout-Export** (heute Pain Point)

2. **Morgen-vor-dem-Lauf**
   *„Wenn ich morgens die App öffne, möchte ich in 5 Sekunden sehen wo ich zum Ziel stehe und welches Training heute ansteht."*
   → **Heute-Tab** (Goal Readiness + PlannedSessionCard)

3. **Nach-dem-Lauf**
   *„Wenn ich gerade gelaufen bin, möchte ich die FIT-Datei hochladen und sofort kontextualisierte Insights bekommen — nicht nur Zahlen."*
   → **Training-Tab** (Upload + Session-Detail mit Soll/Ist-Vergleich)

4. **Nach-dem-Krafttraining**
   *„Wenn ich Krafttraining gemacht habe, möchte ich die Daten hochladen und auswerten — gleicher Flow wie nach Lauf."*
   → **Training-Tab** (Upload + Session-Detail, Strength-Discipline-Variante)

#### Anlassbezogene Jobs

5. **Status-Check zwischendurch**
   *„Wenn ich kurz nachsehen will wie ich auf Kurs bin, möchte ich Goal Readiness + Trend in einem Blick haben."*
   → **Heute** (Goal Card) oder **Analyse** (Trend)

6. **Entwicklungs-Check**
   *„Wenn ich wissen will wie ich mich entwickelt habe, möchte ich Trends sehen — Pace, HR-Effizienz, Volumen, Plan-Treue."*
   → **Analyse-Tab** (Trends Deep Dive)

7. **Trainings-Problem lösen**
   *„Wenn ich ein konkretes Trainings-Problem habe (z.B. Technik-Element ergänzen, Verletzungsverdacht), möchte ich die KI fragen können und kontextualisierte Antworten erhalten."*
   → **AI Coach Chat (FAB)** — auf jeder Seite verfügbar

#### Race-bezogene Jobs

8. **Race-Vorbereitung**
   *„Vor dem Wettkampf möchte ich eine Pacing-Strategie haben (gleichmäßig / negativ / konservativ), das Streckenprofil kennen und meine Gel-Strategie an Versorgungs-Punkten ausrichten."*
   → **Plan-Tab → Pacing-Rechner** (mit Streckenprofil + Versorgungs-Punkten)

9. **Race-Day-Begleiter (Vision)**
   *„Am Wettkampftag möchte ich meine Pacing-Strategie auf der Watch / im Mobile schnell nachsehen können und während des Laufs aktiv begleitet werden — Splits, Pace-Hinweise, worauf achten."*
   → **Companion-Mode** (native Watch-App, Vision)

10. **Post-Race-Reflexion**
    *„Nach dem Wettkampf möchte ich eine Auswertung sehen ('Wie war es?') und die Erkenntnisse sollen in den nächsten Plan einfließen können."*
    → **Analyse-Tab** (Race-Auswertung) + **Plan-Tab** (Plan-Update)

#### Wochenrhythmus-Jobs

11. **Sonntag-abend Wochen-Review**
    *„Wenn ich Sonntag abend die Woche abschließe, möchte ich eine Auswertung der vergangenen Woche sehen und einen konkreten Anpassungs-Vorschlag für die kommende Woche bekommen."*
    → **Heute / Analyse** (automatisches Wochen-Review)

12. **Insight-getriebene Plan-Anpassung**
    *„Wenn nach einem einzelnen Training ein wichtiger Insight rauskommt (Form kippt, Verletzungssignal, Pace-Sprung), möchte ich darauf hingewiesen werden und einen Anpassungs-Vorschlag bekommen."*
    → **AI Coach Insight** (Heute) → **Plan-Anpassung-Vorschlag** (siehe §5.7)

#### Equipment-Jobs (Vision)

13. **Schuh-Tracking**
    *„Beim Training möchte ich wissen welche Schuhe ich heute tragen soll und wie viele Kilometer die schon haben — bevor sie ausgemustert werden müssen."*
    → **Heute** (Schuh-Hinweis) + **Profil/Equipment** (Tracking)

### 2.5 Journey-Walkthroughs

> Konkrete Schritt-für-Schritt-Reisen pro Use Case. Drei Journey-Typen:
> **Daily** (mehrmals/Woche) · **Weekly/Monthly** · **Lifecycle** (selten, lebenswichtig).

#### 2.5.1 Daily — Morgens vor dem Lauf

**Trigger:** Nutzer wacht auf, will wissen was anliegt.
**Frequenz:** 4–6× pro Woche (an Trainings-Tagen).
**Erwartete Verstehzeit:** 5 Sekunden.

**Mentales Modell (priorisiert):**
1. *„Was steht heute an?"* — heutige Trainings-Session
2. *„Wo stehe ich zum Ziel?"* — Goal Readiness

**Hauptpfad:**
1. App öffnen → Heute-Tab
2. **Erste Sicht (Top → Bottom):**
   - **AI Coach Insight** (Alert variant=ai)
     — *bei Form-Issue oder Anpassungs-Empfehlung: hier sofort*
   - **GoalCard (Hero)** — Race + Tage-Countdown + ReadinessRing + 4 Faktoren
   - **WeekOverviewCard mit heutiger Session-Detail** — Trainings-Typ, Pace, Distanz, CTA
3. **Primärer CTA:** „Auf Watch exportieren" — heute 3-Schritt-Pain, soll ein Tap werden (native iOS-App)
4. **Bei Anpassungs-Empfehlung:** Akzeptieren/Ablehnen direkt aus Insight-Card → §5.8 Plan Adaptation
5. Exit: App weg, Training läuft über Watch

**Schmerz im Ist:**
- Workout-Export ist 3-Schritt-Prozess (Web-App → iPhone → Health → Watch)
- Goal Readiness fehlt als prominenter Block (Score ist heute Hero)
- AI Insight ist nicht erstes Element

**Soll-Erlebnis:**
- Goal-Status + heutiges Training in einem Screen, in 5 Sekunden verstanden
- „Auf Watch" als ein Tap (erfordert native iOS-App; Fallback heute: 3 Schritte)
- Bei Form-/Plan-Issue: Anpassungs-Empfehlung sofort sichtbar UND actionable (nicht erst nach dem Lauf)

**Edge Cases:**
- Heute kein Training → *„Heute kein Training."* (Copy §5.6)
- Kein Ziel gesetzt → Empty State *„Jede Saga braucht ein Ziel."* (§5.4)
- Form schlecht → AI Coach Insight schlägt Anpassung vor (§5.8 Goal-Realism-Check)

**Screen-Anforderungen (für Figma):**
- Heute · Default
- Heute · mit Anpassungs-Empfehlung
- Heute · Empty State (kein Ziel)
- Heute · kein Training heute
- Anpassungs-Vorschlag-Modal/Sheet
- Native iOS Watch-Export-Flow (separat)

**Komponenten-Bedarf:**
- Vorhanden: Alert(ai), GoalCard, WeekOverviewCard
- Neu: Schuh-Hint-Komponente (Equipment, optional in Slot 1 oder als Footer)

---

#### 2.5.2 Daily — Nach dem Lauf (Upload + Coach-Quittung)

**Trigger:** Lauf/Kraft beendet, FIT-Datei vom Watch synchronisiert, User öffnet App.
**Frequenz:** ~6× pro Woche (4 Lauf + 2 Kraft).
**Erwartete Verstehzeit:** 5–10 Sekunden für die Quittung; Drilldown nach Belieben.

**Mentales Modell (priorisiert):**
1. *„Was sagt mir der Coach dazu?"* — AI Insight als Hero
2. *„Was waren die Eckdaten?"* — Pace, HR, Distanz, Dauer
3. *(sekundär)* *„Wie war Soll/Ist?"* — bei Plan-Verknüpfung

**Hauptpfad (Soll):**
1. **Auto-Erkennung** der neuen FIT (HealthKit-Listener) → Toast/Heute-Card *„Neue Session erkannt"*
2. **Ein-Tap-Upload** mit auto-ausgefülltem Datum + erkanntem Typ
3. Direkt nach Upload: Session-Detail-Page mit **automatisch generierter KI-Analyse** (Pre-fetch)
4. **Erste Sicht (Top → Bottom):**
   - **AI Coach Insight (Hero)** — Kurz-Quittung in Begleiter-/Zeugen-Stimme, z.B. *„Solide Einheit. Pace 6s/km schneller als Schnitt für Tempoläufe. HR-Drift im normalen Bereich."*
   - **Eckdaten-Stat-Reihe** kompakt: Pace · HR · Distanz · Dauer
   - **Soll/Ist-Vergleich-Card** (nur wenn Plan-Verknüpfung)
   - **Sub-Sektionen** (HR-Zonen · Laps · GPS-Karte · RPE/Notizen) **collapsed by default**, Tap zum Aufklappen
5. Optional: Anpassungs-Vorschlag wenn Insight es nahelegt → §5.8
6. Exit: App weg oder zurück auf Heute

**Schmerz im Ist:**
- Upload-Flow zu komplex (Datei → Typ → Datum → Detail, 3+ Schritte)
- Session-Detail überladen — alles auf einer Seite stapelt sich, KI-Insight nicht prominent
- KI-Analyse muss explizit per Button angefragt werden, nicht automatisch

**Soll-Erlebnis:**
- HealthKit-Listener erkennt FIT, ein Tap zum Upload (erfordert native iOS-App)
- AI Insight als Hero — sofort lesbar, ohne Suchen
- Progressive Disclosure: Kurz-Quittung sofort, alles weitere collapse-bar
- KI-Analyse läuft automatisch im Hintergrund (Pre-fetch nach Upload)

**Edge Cases:**
- Upload-Fehler → Fehler-Card mit klarem Retry
- KI-Analyse noch nicht fertig → Skeleton/Spinner statt leerer Hero
- Keine Plan-Verknüpfung → Soll/Ist-Sektion fehlt komplett, kein Hinweis
- Doppel-Upload → erkennen, *„Diese FIT ist schon hochgeladen"*-Toast

**Screen-Anforderungen (für Figma):**
- Upload-Trigger · Auto-Erkennungs-Toast oder Heute-Card *„Neue Session"*
- Session-Detail · Default (mit AI Insight Hero, collapsed Sub-Sektionen)
- Session-Detail · KI-Analyse läuft (Skeleton)
- Session-Detail · ohne Plan-Verknüpfung
- Session-Detail · Sub-Sektionen aufgeklappt
- Upload-Fehler-State
- Doppel-Upload-Hinweis

**Komponenten-Bedarf:**
- Vorhanden: SessionDetailPage (überarbeiten), Alert(ai), StatBox, GPS-Karte (Leaflet)
- Neu: **Collapse/Accordion-Sektion** für HR-Zonen, Laps, Karte, RPE, Notizen
- Neu: **Soll/Ist-Compare-Card** mit visuellem Diff
- Neu: **Auto-Upload-Indikator** (Toast und/oder Heute-Block)
- Neu: **Skeleton-Variante** der Session-Detail (während KI-Analyse läuft)

---

#### 2.5.3 Weekly — Sonntag abends · Wochen-Review + Vorbereitung

**Trigger:** Sonntag abend, Woche zu Ende, User schaut zurück + voraus.
**Frequenz:** 1× pro Woche.
**Erwartete Dauer:** 5–15 Minuten (mit Tiefe).

**Mentales Modell (priorisiert):**
1. *„Wie war die letzte Woche?"* — Rückblick zuerst
2. *„Was schlägt die App vor?"* — Anpassungs-Empfehlung
3. *„Was steht nächste Woche an?"* — Vorblick mit ggf. übernommenen Anpassungen

**Hauptpfad:**
1. App öffnen → Heute-Tab oder Plan-Tab (TBD: welcher Einstieg)
2. **Wochen-Rückblick prominent** — *nicht versteckt in Sektion*:
   - Zusammenfassung der Woche (Plan-Treue, Volumen, Form-Entwicklung)
   - Highlights *(„Tempolauf gut gelaufen — neue Best-Pace")*
   - Einordnung im Kontext der Phase
3. **Anpassungs-Vorschlag der App** *(falls relevant)* — direkt nach Rückblick:
   - Konkreter Vorschlag mit Begründung *(„Letzte 2 Wochen ACWR > 1.4 — regenerative Mikrozyklus empfohlen, 1× Tempolauf statt 2 nächste Woche")*
   - **Akzeptieren / Ablehnen / Anpassen** als Aktionen
4. **Vorblick auf nächste Woche** — mit ggf. übernommenen Anpassungen:
   - 7-Tage-Layout (Mo–So) mit konkreten Sessions
   - **Sessions verschieben per Drag-and-Drop** (heute schon implementiert)
   - Equipment-Check pro Session (Schuh-Vorschlag, KM-Stand) — *Vision*
5. **Workout-Export für Mo** — *idealerweise ein Tap*:
   - Heute Pain: 3-Schritt-Prozess Web-App → iPhone → Health Fit → Watch
   - Soll: native iOS-App + Watch-Companion → ein Tap
6. Exit: App weg, Sonntag fertig

**Schmerz im Ist:**
- **Watch-Export** ist der größte Schmerz (3-Schritt-Prozess pro Session)
- Wochen-Review existiert (`POST /api/v1/weekly-review/generate`), aber UI wenig prominent
- Anpassungs-Vorschlag fehlt heute komplett
- Rückblick + Vorblick sind getrennt (Plan-Tab vs. Analyse-Tab)

**Soll-Erlebnis:**
- **Ein zusammenhängender Sonntag-Abend-Flow:** Rückblick → Vorschlag → Vorblick → Export
- App proaktiv mit Anpassungs-Vorschlag (datenbasiert, siehe §5.7 + §5.8)
- Watch-Export als ein Tap (native iOS-App)
- Equipment-Check ist Teil des Vorblicks (welche Schuhe für welche Session, KM-Stand)

**Edge Cases:**
- Wenig/keine Daten in der Woche (Krankheit) → Rückblick reduziert, Vorschlag „regenerativ" oder „in normalen Rhythmus zurück"
- Plan ist nicht aktiv → kein Vorschlag möglich, Rückblick ohne Plan-Treue-Bezug
- Nutzer überspringt Vorschlag → wird in der nächsten Woche wieder vorgeschlagen wenn Lage sich nicht ändert

**Screen-Anforderungen (für Figma):**
- Wochen-Review · Default (Rückblick + Vorschlag + Vorblick auf einer Seite oder als Wizard)
- Wochen-Review · ohne Anpassungs-Vorschlag (wenn nichts zu tun)
- Wochen-Review · Vorschlag-Detail-Sheet (mit Begründung, Daten, Akzeptieren/Ablehnen)
- Wochen-Vorblick · 7-Tage-Layout mit Drag-and-Drop
- Wochen-Vorblick · mit Schuh-Hint pro Session (Equipment)
- Watch-Export-Trigger (heute manuell, später Companion-App-Flow)

**Komponenten-Bedarf:**
- Vorhanden: WeekOverviewCard (überarbeiten als Vorblick-Komponente), Drag-and-Drop-Kalender
- Neu: **WeeklyReviewCard** (Rückblick + Highlights)
- Neu: **PlanAdaptationProposal-Sheet** (Vorschlag mit Begründung + Aktionen)
- Neu: **EquipmentHint** (Schuh-Vorschlag pro Session-Card)
- Neu: **WatchExport-CTA** (heute Web-Download-Button, später iOS-Companion-Flow)

---

#### 2.5.4 Lifecycle — Plan-Erstellung (für ein Race)

**Trigger:** Nutzer hat ein Race im Auge (z.B. HM Berlin in 14 Wochen) und will den Plan dazu setzen.
**Frequenz:** 1–3× pro Jahr (pro Wettkampf).
**Erwartete Dauer:** 5–10 Minuten.

**Mentales Modell:**
1. *„Ich gebe dir mein Ziel — gib mir den passenden Plan."*
2. Vertrauen in KI-Generierung als Default; manuelle Eingriffe optional
3. Nicht entscheiden müssen wann Plan „startet" — das soll sich aus dem Datum ergeben

**Hauptpfad (Soll):**
1. **Entry:** Plan-Tab → „+ Neuer Plan" oder Heute-Empty-State (wenn kein Ziel) → CTA
2. **Schritt 1 — Ziel eingeben:**
   - Race-Name (z.B. *„Halbmarathon Berlin"*)
   - Datum (Date-Picker)
   - Distanz (HM / Marathon / 10k / 5k / Custom)
   - Zielzeit (Time-Picker, z.B. *Sub-2h* = 1:59:59)
   - *(Optional)* Aktueller Stand: aktuelle HM-Pace, max KM/Woche
3. **Schritt 2 — KI generiert vollständigen Plan:**
   - Skeleton/Progress-Indikator während Generierung (vermutlich 5–15s)
   - Plan kommt komplett: Phasen (Aufbau / Belastung / Tapering) + Wochen-Templates für alle Wochen
4. **Schritt 3 — Review:**
   - **Phasen-Timeline** als Hero (visueller Balken über Wochen, Phase-Marker)
   - **Erste Woche detailliert** sichtbar (Mo–So mit Sessions) — *so versteht User was real auf ihn zukommt*
   - **Plan-Eckdaten**: Anzahl Wochen, Wochenstruktur (z.B. 4× Lauf + 2× Kraft), Phasen-Längen
5. **Schritt 4 — Justieren (optional):**
   - Wochenstruktur ändern (z.B. *„nur 3× Lauf"*)
   - Phase-Längen variieren
   - Einzelne Sessions tauschen
   - KI re-generiert betroffene Bereiche
6. **Schritt 5 — Speichern:**
   - Plan ist gespeichert, **noch nicht aktiv**
   - Auto-Aktivierung beim Beginn der Phase 1 (also bei erstem Sonntag der Plan-Wochen)
   - Hinweis-Card auf Heute: *„Plan startet am [Datum]. X Tage bis Aufbau-Phase."*
7. Exit: zurück auf Heute oder Plan-Übersicht

**Schmerz im Ist:**
- Aktuelle Implementation: KI-Generierung ist pro Phase einzeln, mehrstufig
- Wenig Visualisierung der Phasen-Timeline auf einen Blick
- „Aktivieren"-Schritt explizit nötig
- Komplexe Plan-Editor-Page mit vielen Optionen

**Soll-Erlebnis:**
- **Linear: Ziel → KI → Review → Done.** 5 Minuten, fertig.
- KI-Generierung **komplett**, nicht stückweise
- Phasen-Timeline + erste Woche als **mentaler Anker**
- Auto-Aktivierung statt expliziter Switch (reduziert Cognitive Load)
- Justierung sekundär — Default-KI-Plan soll meistens passen

**Edge Cases:**
- KI-Generierung schlägt fehl → Fallback auf Standard-Vorlage
- Race-Datum zu nah (< 6 Wochen für HM) → Plan wird kondensiert, Hinweis auf Realismus-Kompromiss
- Race-Datum in der Vergangenheit → Validation-Error
- Aktiver Plan vorhanden → Conflict-Dialog: *„Aktiven Plan ersetzen oder zweiten Plan parallel anlegen?"*
- Sehr ambitioniertes Ziel (Pace-Sprung > X%) → Hinweis im Review: *„Dieses Ziel erfordert eine Pace-Steigerung von Xs/km — knapp realisierbar."*

**Screen-Anforderungen (für Figma):**
- Plan-Erstellung · Step 1: Ziel-Eingabe-Form
- Plan-Erstellung · Step 2: KI-Generierung läuft (Skeleton/Progress)
- Plan-Erstellung · Step 3: Plan-Review mit Phasen-Timeline + erste Woche
- Plan-Erstellung · Step 4: Justierung (Wochenstruktur, Phasen, Session-Swap)
- Plan-Erstellung · Step 5: Bestätigung mit Auto-Aktivierungs-Hinweis
- Plan · KI-Fehler-Fallback (Vorlage-Picker)
- Plan · Conflict-Dialog (aktiver Plan ersetzen)
- Plan · Race-zu-nah-Warnung
- Plan · Ambitions-Realismus-Hinweis im Review

**Komponenten-Bedarf:**
- Vorhanden: TrainingPlanEditorPage (komplett überarbeiten), Phase-Komponenten
- Neu: **GoalSetting-Form** (Race + Zielzeit + Distanz + Datum + optional Stand)
- Neu: **PhaseTimeline** (visueller Balken über alle Wochen, Phase-Marker, hervorgehobene aktuelle Phase)
- Neu: **PlanReview-Komponente** (Timeline + erste Woche detailliert + Eckdaten)
- Neu: **PlanAutoActivationHint** (Heute-Card *„Plan startet am [Datum]"*)
- Neu: **PlanConflict-Dialog** (mehrere Pläne / Aktivierungs-Switch)

---

#### 2.5.5 System-initiiert — Plan-Anpassungs-Vorschlag

**Trigger:** App initiiert, nicht Nutzer. Vier Auslöser:
- Nach einem Lauf, wenn Insight Anpassung nahelegt
- Im Sonntag-Wochen-Review (siehe §2.5.3)
- Bei Goal-Realism-Issue (Pace-Vorhersage reicht nicht für Ziel — siehe §5.8)
- Bei Form-Krise (HR-Drift-Trend, ACWR-Sprung)

**Frequenz:** unregelmäßig — etwa 1× pro 2 Wochen.

**Mentales Modell:**
1. *„Etwas ist aufgefallen."* — User wird angesprochen
2. *„Was, warum, was jetzt?"* — verstehen + entscheiden
3. *„Akzeptieren oder Ablehnen — und Schluss."* — keine Nachfrage-Schleife

**Hauptpfad:**
1. **Doppelt verankert:**
   - Vorschlag erscheint **am Trigger-Ort** (z.B. Session-Detail nach Auswertung, Wochen-Review-Sektion am Sonntag) — *direkt im Kontext, in dem der Anlass entstand*
   - **UND auf Heute** als Spiegel (zentrale Inbox) — *wenn User direkt morgens öffnet, sieht er es da*
2. **Komplette Begründung sofort sichtbar** (nicht „mehr"-Tap):
   - Konkreter Vorschlag (z.B. *„1× Tempolauf statt 2 nächste Woche"*)
   - 2–3 Sätze Begründung mit Daten *(z.B. „ACWR letzte 2 Wochen 1.45 — Risiko-Bereich. HR-Drift in Tempoläufen +9 bpm bei gleicher Pace.")*
3. **Aktionen:**
   - **Akzeptieren** → Plan wird angepasst, Bestätigungs-Toast, weg
   - **Ablehnen** → Vorschlag verschwindet sofort, App akzeptiert ohne Nachfrage
4. **Wenn ähnliche Lage in folgender Woche besteht:** Vorschlag erscheint erneut, mit Hinweis *„Erinnerung — die Lage hat sich nicht verändert."*

**Schmerz im Ist:**
- Anpassungs-Vorschlag fehlt komplett (App schlägt nichts proaktiv vor)
- Wochen-Review existiert (`POST /api/v1/weekly-review/generate`) aber ohne Konsequenz/Aktion

**Soll-Erlebnis:**
- App ist proaktiv, ohne aufdringlich zu sein (keine Push, kein Modal)
- Lagom-Regel: präsent, nicht laut
- Komplette Transparenz: User sieht warum und kann nachvollziehen
- Kein Druck: Ablehnen ist legitim, App lernt nicht „weniger Vorschläge", sondern respektiert Einzelentscheidung

**Edge Cases:**
- User ignoriert Vorschlag tagelang → Vorschlag bleibt sichtbar in Heute, aber wird nicht penetranter
- Plan wurde inzwischen anderweitig geändert → Vorschlag deaktiviert sich automatisch
- Mehrere Vorschläge gleichzeitig (z.B. Session-Trigger + Wochen-Trigger) → priorisiert nach Schwere; ältere Vorschläge bleiben in Inbox

**Screen-Anforderungen:**
- Heute · mit Anpassungs-Vorschlag-Card (am Top, vor GoalCard)
- Session-Detail · mit Anpassungs-Vorschlag-Inline (am Ende der KI-Insight-Section)
- Wochen-Review · mit Anpassungs-Vorschlag inline
- Vorschlag · Akzeptieren-Toast (nach Tap)
- Vorschlag · Ablehnen-Toast (kurz, ohne Nachfrage)
- Vorschlag · „Erinnerung"-Variante (zweite Iteration desselben Vorschlags)

**Komponenten-Bedarf:**
- Vorhanden: Alert(variant=ai)
- Neu: **PlanAdaptationProposal** — Card-Komponente mit Begründung + Daten-Snippet + Akzeptieren/Ablehnen-Aktionen
- Neu: **AdaptationToast** — Bestätigungs-Feedback (akzeptiert/abgelehnt)

---

#### 2.5.6 Lifecycle — Race-Day-Flow

**Trigger:** Wettkampf — der Höhepunkt der Vorbereitung.
**Frequenz:** 1–3× pro Jahr.
**Drei Phasen:** Vorabend → Race-Morgen → Während Race → (Post-Race siehe Reflexion)

**Mentales Modell:**
1. **Vorabend** = Operationen — alles muss sitzen
2. **Morgen** = Emotion + schneller Check — bereit, jetzt los
3. **Während** = Stille — App stört nicht

**Hauptpfad — Vorabend (T-1 Tag):**

App zeigt **Pre-Race-Checklist** prominent auf Heute (oder Race-Card auf Plan-Tab):
- ☐ Pacing-Strategie final + auf Watch exportiert
- ☐ Streckenprofil eingespielt (GPX-Upload mit Höhenprofil)
- ☐ Gel-/Versorgungs-Strategie (Marker auf Strecke, Gel-KM-Plan)
- *(optional)* GoalCard zeigt Tapering-Final-State

Jeder Punkt ist ein Tap zur jeweiligen Action. Wenn alle ☑: Card kollabiert mit *„Bereit für morgen."*

**Hauptpfad — Race-Morgen:**

GoalCard wechselt in `state=raceday`:
- Caption: *„Du hast alles getan. Jetzt lauf deine Saga."* (Saga-Tonfall an Schwelle, siehe §1.3.2 + §5.6)
- **Pacing-Strategie als großer Tap-Punkt** — ein Klick öffnet Splits-Übersicht (operationell zugänglich, keine Such-Reibung)
- Streckenprofil + Versorgungs-Marker auf Wunsch sichtbar

**Hauptpfad — Während Race:**

**App ist still.** Watch übernimmt das Tracking, Mobile kein Touchpoint erwartet.
- Optional Heute-Indikator *„Race läuft"* — passiv, dezent
- Nutzer braucht Mobile nicht in der Hand

**Hauptpfad — Direkt nach Race:**

Übergang in Post-Race-State (Siehe §5.6 Copy: *„Dein Kapitel ist geschrieben. Was kommt als Nächstes?"*) — Auswertungs-Journey separat (im Reflexions-Block; folgt).

**Schmerz im Ist:**
- Streckenprofil-Upload existiert nicht
- Gel-/Versorgungs-Strategie existiert nicht
- Race-Day-State der GoalCard ist nur in Figma, nicht in Code
- Pre-Race-Checklist existiert nicht
- Pacing-auf-Watch-Export ist 3-Schritt-Pain (siehe Journey 1)

**Soll-Erlebnis:**
- **Vorabend:** alles in einem Flow erreichbar, Checklist macht Status sichtbar
- **Morgen:** emotional aufgeladen (Saga-Caption) + sofort operativ (Pacing-CTA)
- **Während:** App schweigt
- **Vision (nicht MVP):** Companion-Mode auf Watch begleitet aktiv mit ruhigen Splits/Hinweisen

**Edge Cases:**
- Race-Datum verschoben → Plan-Update
- Race ausgefallen (DNS / Wetter) → User markiert, GoalCard reagiert mit milder Caption
- DNF während Race → später als DNF markieren, Post-Race-State respektiert (kein Saga-Triumph)
- Streckenprofil-Upload schlägt fehl → manueller Höhenmeter-Eintrag oder Race ohne Profil
- Pacing nicht final → Pre-Race-Checklist warnt am Vorabend prominent

**Screen-Anforderungen (für Figma):**
- Heute · Vorabend mit Pre-Race-Checklist
- Heute · Race-Morgen (state=raceday) mit Saga-Caption + Pacing-CTA
- Heute · Race läuft (passiv, Indikator)
- Heute · DNF / DNS-State
- Pacing-Strategie · Race-Modus mit Streckenprofil + Versorgungs-Markern
- Streckenprofil · GPX-Upload-Flow + Visualisierung
- Gel-Strategie · Versorgungs-Punkte als Marker, Gel-KM-Empfehlung
- Companion-Mode (Vision, nicht MVP)

**Komponenten-Bedarf:**
- Vorhanden: GoalCard (`state=raceday` in Figma vorhanden, in Code fehlt), PacingPage, RoutesPage
- Neu: **PreRaceChecklist** — Card mit 3–4 Status-Punkten + Tap-Aktionen
- Neu: **RaceStrategy-View** — Pacing + Streckenprofil + Versorgungs-Marker zusammenhängend
- Neu: **GelStrategy** — Versorgungs-Punkte als Marker auf Strecke, Gel-KM-Empfehlung
- Neu: **RaceState-Heute-Block** — passiver „läuft gerade"-Indikator
- Vision: Native iOS Companion-Mode (Watch-App, später)

---

#### 2.5.7 Lifecycle — Onboarding (First-Time-User)

**Trigger:** Nutzer öffnet App das erste Mal.
**Frequenz:** 1× pro User-Lifetime (zzgl. Re-Onboarding nach langer Pause).
**Erwartete Dauer:** 2–5 Minuten.

**Mentales Modell:**
1. *„Wer ist diese App?"* — erste Begegnung mit der Marke
2. *„Was muss ich preisgeben?"* — möglichst wenig, schnell zum Wert
3. *„Wann fängt das eigentliche Training an?"* — klar Pfade

**Hauptpfad:**
1. **Welcome-Screen** — Brand (Wortmarke + Bildmarke), kurzer Pitch (1–2 Sätze), CTA *„Los geht's"*
2. **Account/Login** (existiert: Email / Apple / Google)
3. **Coach-Dialog (KI-geführt)** — kein Wizard, sondern strukturierter Trainer-Dialog in Begleiter-Stimme. Setzt direkt die Drei-Stimmen-Tonalität (siehe §1.3.1):
   - Begrüßung
   - Frage 1: *„Hast du ein Wettkampf-Ziel im Auge?"* — Antwort: Ja / *„Später"* (skip)
     - Falls Ja → Race-Name + Datum + Distanz + Zielzeit
   - Frage 2 (optional): *„Wie ist dein aktueller Stand?"* (z.B. letzter HM-Pace) — skip möglich
   - Frage 3 (optional): *„Wie sieht deine typische Trainingswoche aus?"* (Anzahl Lauf/Kraft pro Woche) — skip möglich
   - Coach: *„Alles klar. Ich richte das ein."*
4. **Plan-Generierung** (wenn Ziel gesetzt) — siehe Journey 2.5.4 Step 2–5
5. **Bewusst NICHT im Onboarding:**
   - **HF-Werte (Athleten-Profil)** → werden durch Nutzung erstellt, primär durch **Schwellentest** der nach 1–2 Wochen aktiv angeboten wird. Ruhe-HF kann via Apple Health gelesen werden (wenn HealthKit verbunden).
   - **AI-Provider-Key** → User gibt KEINEN Key ein. Lauf über **Entwickler-Key** + Abomodell-Schicht (siehe §10).
   - **Pricing/Abo-Auswahl** → Onboarding macht keinen Druck. Free-User bekommt 1×-KI-Plan-Sample, Wochenabo wird erst aufploppen wenn er KI-Features aufruft.
6. **Erster Screen nach Onboarding:**
   - Mit Ziel: Heute mit *„Plan startet am [Datum]"*-Hint (Auto-Aktivierung)
   - Ohne Ziel: Heute · Empty State *„Jede Saga braucht ein Ziel."* + CTA „Ziel festlegen"

**Schmerz im Ist:**
- Onboarding existiert vermutlich minimal / ohne KI-Coach-Dialog
- AI-Provider-Key wird heute vom User selbst eingegeben (Hürde, technisch, schreckt ab)
- HF-Werte werden direkt im Profil-Setup abgefragt → harte Hürde im ersten Eindruck
- Athletenprofil-Page ist heute eine eigene Seite — als Onboarding-Stop schwer

**Soll-Erlebnis:**
- Erste Begegnung = Coach-Dialog → setzt Tonalität, fühlt sich wie Trainer-Gespräch an
- Minimal-Setup: Account + (optional) Ziel
- Datentiefe entsteht durch Nutzung, nicht durch Setup-Hürde
- Kein API-Key-Reibung — User merkt nichts vom Backend-Setup

**Edge Cases:**
- User skippt alle Coach-Fragen → Heute mit Empty State, App nutzbar aber leer
- User hat kein gültiges Abo → siehe §6.7 Abomodell-Schicht
- HealthKit nicht freigegeben → manuelle HF-Eingabe später, kein Onboarding-Block

**Screen-Anforderungen (für Figma):**
- Welcome (Brand + Pitch + CTA)
- Login (existiert, ggf. Onboarding-Variante)
- Coach-Dialog · Begrüßung
- Coach-Dialog · Ziel-Frage (Ja/Später)
- Coach-Dialog · Ziel-Eingabe (Race + Datum + Zielzeit)
- Coach-Dialog · Stand-Frage (skipbar)
- Coach-Dialog · Wochenstruktur-Frage (skipbar)
- Coach-Dialog · Abschluss
- Plan-Generierung läuft (Skeleton)
- Plan-Review (siehe Journey 2.5.4)
- Heute · mit Plan-Start-Hint
- Heute · Empty State (Ziel skipped)
- Schwellentest-Angebot (später, in Heute-Inbox eingeschoben)

**Komponenten-Bedarf:**
- Vorhanden: Auth-Pages, ChatPage (als Inspiration)
- Neu: **WelcomeScreen** (Brand + Pitch + CTA)
- Neu: **CoachDialog** — strukturierter Dialog-Wizard mit Skip-Option, nutzt KI-Chat-Pattern aber linear gefuehrt
- Neu: **OnboardingShell** mit Progress-Indikator
- Neu: **SchwellentestPrompt** — wird ~1–2 Wochen nach Onboarding in Heute eingeschoben

#### 2.5.8 Daily — Trainings-Problem-Konsultation (KI-Chat)

**Trigger:** Nutzer hat ein konkretes Trainings-Problem oder eine Frage.
**Frequenz:** unregelmäßig — von 0 bis mehrmals pro Woche.

**Mentales Modell:**
1. *„Ich habe eine Frage / ein Problem."*
2. *„Die KI soll mir helfen, mit Kontext zu meinem Training."*
3. Output sollte umsetzbar sein, ggf. zurück in Plan einfließen

**Beispiel-Anlässe:**
- *„Ich habe eine Pause gehabt, wie steige ich wieder ein?"*
- *„Mein Knie zwickt nach Tempoläufen — was kann ich tun?"*
- *„Wie integriere ich Lauf-ABC in meinen Wochenplan?"*
- *„Mein letzter Tempolauf war schlecht — woran kann das liegen?"*
- *„Was bedeutet eigentlich VO2max für mich?"*

**Hauptpfad (Soll):**
1. **Trigger:** Nutzer tippt auf Chat-FAB (rechts unten, auf jeder Seite verfügbar — siehe §3.2)
2. Chat öffnet als **Sheet/Drawer** über aktueller Seite (nicht als eigene Page) — Kontext der aktuellen Seite bleibt sichtbar
3. **Eingabefeld + Konversations-Verlauf** — Streaming-Antwort
4. **Kontextpicker** — KI weiß automatisch aus aktueller Seite (z.B. Session-Detail aufgerufen → KI hat diese Session als Kontext); manueller Override möglich
5. Antwort kommt in **Coach-Stimme** (siehe §1.3.1)
6. **Wenn Antwort eine Plan-Änderung nahelegt:** direkt aus Chat *„Plan-Änderung übernehmen?"*-Button (existiert bereits laut Audit)
7. Exit: Sheet schließt, Nutzer ist wieder auf vorheriger Seite

**Schmerz im Ist:**
- Chat ist eigene Page (`/chat`) statt FAB-Overlay
- Kontextpicker existiert, aber nicht automatisch aus aktueller Seite gefuellt
- Coach-Stimme inkonsistent (heutige KI-Antworten sind eher generisch)

**Soll-Erlebnis:**
- Chat überall, ohne Page-Wechsel
- Kontext kommt automatisch aus aktueller Seite
- Coach-Stimme: Begleiter im Default, Coach bei konkreten Plan-Eingriffen
- Plan-Änderungs-Übernahme bleibt erhalten (Audit zeigt: existiert)

**Edge Cases:**
- KI-Antwort schlägt Plan-Änderung vor, User akzeptiert → Plan-Adaptation-Flow (Journey 2.5.5)
- KI hat keine Antwort → ehrliche Antwort: *„Da bin ich nicht sicher. Frag dich, ob..."*
- Sehr lange Konversation → Scrollbar, Verlauf bleibt erhalten
- Ohne Internet → Offline-Hinweis, keine Antwort möglich (KI ist Cloud-Service)

**Screen-Anforderungen:**
- Chat-FAB · auf jeder Seite (existiert als Komponente in AppLayout)
- Chat-Sheet · default mit Begrüßung, Vorschläge für Quick-Actions
- Chat-Sheet · Konversation läuft (Streaming-Antwort)
- Chat-Sheet · Antwort mit Plan-Änderungs-CTA
- Chat-Sheet · Antwort mit Drilldown-Link (z.B. *„Lies Insight zu Tempolauf X"*)
- Chat-Page (existiert, als Full-Screen-Fallback)
- Chat · Offline-State

**Komponenten-Bedarf:**
- Vorhanden: ChatPage, ChatFAB-Komponente in AppLayout, KI-Endpoints (Streaming, Plan-Anwendung)
- Neu/Anpassen: **ChatSheet** als Drawer/Sheet-Variante des Chats — überlagert aktuelle Seite, schließt zurück
- Anpassen: **AutoContextPicker** — füllt Kontext automatisch aus aktueller Page

---

### 2.6 Journey-Übersicht (Tabelle)

Konsolidierte Sicht auf alle 8 Journeys:

| # | Journey | Typ | Frequenz | Tab(s) |
|---|---|---|---|---|
| 2.5.1 | Morgens vor dem Lauf | Daily | 4–6×/Wo | Heute |
| 2.5.2 | Nach dem Lauf (Upload + Coach-Quittung) | Daily | ~6×/Wo | Training |
| 2.5.3 | Sonntag · Wochen-Review + Vorbereitung | Weekly | 1×/Wo | Plan + Heute |
| 2.5.4 | Plan-Erstellung für ein Race | Lifecycle | 1–3×/Jahr | Plan |
| 2.5.5 | Plan-Anpassungs-Vorschlag (System-initiiert) | unregelmäßig | ~1×/2 Wo | Heute + Trigger-Ort |
| 2.5.6 | Race-Day-Flow | Lifecycle | 1–3×/Jahr | Heute + Plan |
| 2.5.7 | Onboarding (First-Time) | Lifecycle | 1×/Lifetime | Auth + Coach-Dialog |
| 2.5.8 | Trainings-Problem-Konsultation (KI-Chat) | Daily/On-demand | 0–mehrmals/Wo | Querschnitt (FAB) |

### 2.4 Anti-Jobs

Was die App **nicht** für mich tun soll:

- *Mich daran erinnern, dass ich gestern nicht trainiert habe* (Streak-Logik — explizit unerwünscht, siehe §1.2 Anti-Pattern #3)
- *Mich mit anderen Athleten vergleichen* (kein Social — siehe §1.2 #1)
- *Mir motivierende Kalendersprüche pushen* (siehe §1.2 #6)
- *Plan-Änderungen heimlich vornehmen* (siehe §5.7 — Vorschlagsmodell, Transparenz)

---

## 3. Information Architecture

### 3.1 Navigation: 5 Haupt-Tabs

> ⚠️ **Tab-Labels final festzulegen.** Aktueller Diskussionsstand:

| # | Arbeitsname | Vorschlag final | Zweck (kurz) | Frequenz |
|---|---|---|---|---|
| 1 | Heute | **Heute** | Tagesblick, was steht an, wie geht's mir | täglich |
| 2 | Training | **Training** | Alle Sessions (Wochenansicht default + History) | täglich |
| 3 | Fortschritt | **Analyse** | Auswertung, Trends, Insights, Form/Score | wöchentlich |
| 4 | Plan | **Plan** | Strategische Saison-Planung mit Ziel + Phasen + Pacing | gelegentlich |
| 5 | Bibliothek | **Sammlung** | Wiederverwendbare Bausteine: Routen, Vorlagen, Übungen | gelegentlich |

**Begründungen für Umbenennungen** *(zu finalisieren mit Nils)*:
- „Fortschritt" → „Analyse": Tab ist primär Auswertung, nicht nur Score-Verlauf
- „Bibliothek" → „Sammlung": Truncation-sicher (≤ 8 Zeichen) und treffender für „wiederverwendbare Bausteine"

**Konvention für Tab-Labels:** 1 Wort, ≤ 8 Zeichen, deutsch, kein Wortspiel. Truncation in der UI ist als Sicherheitsleine implementiert (`textTruncation: ENDING`), nicht als Designziel.

### 3.2 Sondernavigation (nicht in Bottom Nav)

- **Profil & Einstellungen:** Avatar oben rechts im Header. Keine eigene Tab-Position.
- **AI Coach Chat:** Floating Action Button (FAB) rechts unten. Auf allen Seiten verfügbar, kontextbezogen.

### 3.3 URL-Struktur

*[tbd — wird beim Finalisieren der Tab-Namen aktualisiert]*

```
/heute                         → Heute (Dashboard)
/training                      → Wochenansicht (Default)
/training/sessions             → Alle Sessions
/training/sessions/:id         → Session-Detail
/training/sessions/new         → Session hochladen
/analyse                       → Analyse-Übersicht
/analyse/trends                → Deep Dive Trends
/plan                          → Aktiver Plan
/plan/:planId                  → Plan-Detail
/plan/:planId/pacing           → Pacing-Rechner
/sammlung                      → Sammlung-Übersicht
/sammlung/routen               → Routen-Liste
/sammlung/vorlagen             → Vorlagen-Liste
/sammlung/uebungen             → Übungen-Liste
/profil                        → Profil & Einstellungen
```

**Migration:** Alte Pfade `/fortschritt` → `/analyse`, `/bibliothek` → `/sammlung` mit Redirect.

### 3.4 Layout (Desktop / Mobile)

**Source of Truth: Figma File.** Mockups verlinken statt zu duplizieren.

- Desktop: Sidebar links, Avatar + Chat-FAB oben rechts → *[Figma Link einfügen]*
- Mobile: Bottom Nav (5 Slots), Header mit Avatar + KI-Icon → *[Figma Link einfügen]*

---

## 4. Feature-Spezifikation pro Tab

> Jeder Tab folgt der gleichen Struktur: **Zweck → Figma → Komposition → Komponenten → Empty States → verwandte Jobs**.
> ASCII-Mockups bewusst nicht enthalten — Figma ist die visuelle Wahrheit.

### 4.1 Heute (Dashboard)

**Zweck:** Persönlicher Tagesblick — was steht heute an, wie geht's mir, wo stehe ich zum Ziel.

**Figma:** *[Link zum Heute-Frame einfügen]*

**Komposition (von oben nach unten):**

1. **AI Coach Insight** (Alert variant=ai oder eigenständige Card) — eine Zeile, kontextbezogen
2. **Goal Readiness Card** (Hero) — Race + Zielzeit + Tage-Countdown + ReadinessRing + Faktoren-Aufschlüsselung
3. **WeekOverviewCard** — Wochenstruktur mit 7-Tage-Statusleiste; Detail-Sektion zeigt heutige Session + ist Sprungpunkt zu anderen Tagen der Woche

> Anmerkung: PlannedSessionCard ist **in WeekOverviewCard integriert** (Detail-Sektion zeigt heutige Session). Kein separater Heute-Card-Block.

**Absprungpunkte:**
- Aus WeekOverviewCard → Session-Detail (heutige + andere Tage der Woche)
- Über Tab **Training** → komplette Sessions-History
- Über Tab **Analyse** → Insights + Trends

**Komponenten verwendet:**
- `Alert` (variant=ai) — Figma `3804:260`
- `GoalCard` — Figma `2740:5477`
- `WeekOverviewCard` — Figma `2988:3995` (mit eingebetteter PlannedSessionCard-Detail)

**Empty States:**
- Kein Ziel gesetzt → siehe §5.4 + §5.6 Copy-Bibliothek („Jede Saga braucht ein Ziel.")

**Verwandte Jobs:** §2.3 #2, #5, #11, #12, #13

**Phasen-Spezifisches:**
- Tapering: GoalCard zeigt Tapering-State; AI Coach Insight ist Tapering-fokussiert
- Race-Tag: GoalCard wechselt in `state=raceday` (Caption: *„Du hast alles getan. Jetzt lauf deine Saga."*)
- Post-Race: GoalCard wechselt in `state=postrace` (Caption: *„Dein Kapitel ist geschrieben."*)

---

### 4.2 Training

**Zweck:** Alle Sessions an einem Ort — Wochenansicht (default) + komplette History + Upload + Detail.

**Figma:** *[Link einfügen]*

**Komposition:** *[tbd]*

**Komponenten verwendet:** *[tbd]*

**Empty States:** *[tbd]*

**Verwandte Jobs:** *[tbd]*

---

### 4.3 Analyse

**Zweck:** Auswertung — Trends, Insights, Form-Beurteilung, was muss ich ändern.

**Figma:** *[Link einfügen]*

**Komposition:** *[tbd]*

**Komponenten verwendet:** *[tbd]*

**Empty States:** *[tbd]*

**Verwandte Jobs:** *[tbd]*

---

### 4.4 Plan

**Zweck:** Strategische Saison-Planung — Ziel, Phasen, Wochen, Pacing-Rechner.

**Figma:** *[Link einfügen]*

**Komposition:** *[tbd]*

**Komponenten verwendet:** *[tbd]*

**Empty States:** *[tbd]*

**Verwandte Jobs:** *[tbd]*

---

### 4.5 Sammlung

**Zweck:** Wiederverwendbare Trainingsbausteine — Routen, Vorlagen, Übungen.

**Figma:** *[Link einfügen]*

**Komposition:** *[tbd — Sub-Tab-Leiste: Routen \| Vorlagen \| Übungen]*

**Komponenten verwendet:** *[tbd]*

**Empty States:** *[tbd]*

**Verwandte Jobs:** *[tbd]*

---

## 5. Querschnittskonzepte

> Konzepte, die nicht zu einem einzelnen Tab gehören, sondern App-weit gelten.

### 5.1 Goal Readiness

*[Migration aus `archive/GOAL_READINESS_CONCEPT.md`]*

**Idee:** Beantwortet die Frage *„Bin ich bereit für dieses Rennen in X Tagen in Zeit Y?"*.

**Status:** Konzept liegt vor (siehe Archiv), Implementation steht aus.

*[Detailspezifikation aus archive/GOAL_READINESS_CONCEPT.md hierher migrieren — TBD]*

### 5.2 Fitness-Score & Form (CTL/ATL/TSB)

*[tbd — Definition + Ableitung + Verweis auf reference/DOMAIN_MODEL.md]*

### 5.3 AI Coach (Insights + Chat)

*[Migration aus `archive/AI_ANALYSIS_INTEGRATION.md`]*

**Komponenten:**
- **AICoachInsight Card** auf Dashboard — Bot-Icon + Header „Insight · KI-GENERIERT" + Body-Text
- **Chat-FAB** rechts unten auf allen Seiten — kontextbezogen

*[Detailspezifikation TBD]*

### 5.4 Empty States

*[tbd — App-weite Patterns: kein Ziel, keine Sessions, keine Routen, etc.]*

### 5.5 Errors & Edge Cases

*[tbd — Pattern-Library für Fehlerzustände]*

### 5.6 Voice & Copy

**Tonalitäts-Regeln** siehe §1.3 (Leitprinzipien §1.3.2 – §1.3.6).

**On-demand-Einordnung-Pattern:**
- Stat-Zahlen und Fach-Begriffe (TSB, CTL, ATL, RPE, GA1, ACWR) bleiben in der UI **pur** — keine inline-Erklärung
- Direkt am Wert ein **Info-Icon (i)** oder unsichtbarer Tap-Bereich
- Per Tap/Hover/Long-Press erscheint Popover mit Erklärung in **Begleiter-Sprache**
- Beispiel: Tap auf „TSB +8" → *„Du bist gut erholt. Werte zwischen +5 und +15 zeigen, dass dein Tapering greift."*

**Copy-Bibliothek (Beispiele, validiert):**

| Kontext | Copy |
|---|---|
| Empty State (kein Ziel) — Headline | *„Jede Saga braucht ein Ziel."* |
| Empty State (kein Ziel) — CTA | „Ziel festlegen" *(neutral, kein Untertext)* |
| Race Day — GoalCard Caption | *„Du hast alles getan. Jetzt lauf deine Saga."* |
| Post Race — GoalCard Caption | *„Dein Kapitel ist geschrieben. Was kommt als Nächstes?"* |
| Tapering — TaperingFocusCard | Title: *„Du bist in Form."* · Desc: *„Halte sie."* |
| Rest Day — WeekOverviewCard Detail | *„Heute kein Training."* |
| Ruhelauf — PlannedSessionCard Description | *„Lockerer Lauf. Plauderton, Puls unter 140."* |
| Completed Session — WeekOverviewCard Detail | *„Solide Einheit. Form blieb sauber, RPE 7/10."* |

### 5.7 Insights

> Insights sind das **Herzstück der Analyse**. Sie sind nicht nur Datenanzeige, sondern **trainingswissenschaftlich fundierte Beobachtungen mit konkreter Handlungsempfehlung**.

#### 5.8.1 Anforderungen an einen Insight

Jeder Insight muss diese 5 Kriterien erfüllen:

1. **Trainingswissenschaftlich fundiert** — basiert auf etablierten Konzepten (Pace/HR-Decoupling, ACWR, Polarized Training, Lauf-ABC, etc.) — keine Trivialkorrelationen.
2. **Mehrdimensional** — bezieht mehrere Datenquellen ein (z.B. HR + Pace + Wetter + Schlaf), nicht nur eine Metrik isoliert.
3. **Handlungsleitend** — von der Diagnose zur **konkreten Maßnahme**: was kann ich beim nächsten Training tun? Welche Übung? Welcher Pace?
4. **Sprachlich zugänglich** — keine Abkürzungs-Salven (CTL/ATL/TSB/ACWR …) ohne Kontext. Fachbegriffe via On-demand-Pattern erklärbar (siehe §5.6).
5. **An Plan-Anpassung koppelbar** — wenn ein Insight eine Plan-Änderung nahelegt, muss ein Vorschlag direkt umsetzbar sein (siehe §5.8).

#### 5.8.2 Insight-Kategorien

| Kategorie | Wann | Beispiel |
|---|---|---|
| **Datenkorrelation** | Auffällige Abweichung in einer Session | *„HR 8 bpm höher als sonst bei dieser Pace. Aber: 3°C wärmer, Schlaf nur 5:40h. Wahrscheinlich Hitze + Müdigkeit. Pace dafür stark — du hast kompensiert."* |
| **Technik-Auffälligkeit** ⭐ | Kadenz, Bodenkontakt, Schrittlänge etc. weichen ab | *„Kadenz 168 (sonst 172) bei ähnlicher Pace. Hinweis auf Ermüdung. Konkret: nächste Einheit Lauf-ABC vorschalten — Skippings, Anfersen, Kniehebelauf je 3×30m. Beim Tempolauf bewusst auf 172+ achten."* |
| **Plan-Abweichung mit Diagnose** | Soll/Ist passt nicht | *„Geplant 4×1000m @ 4:15. Gelaufen: 4:18, 4:14, 4:22, 4:28. Ab Intervall 3 verlangsamt — typisches Muster bei zu schnellem Start. Nächstes Mal: 1. Intervall 5s langsamer angehen."* |
| **Form-Trend mit Empfehlung** | Form-Entwicklung sichtbar | *„Deine Form steigt seit 4 Wochen sauber. Belastung und Erholung im Gleichgewicht. Diese Woche kannst du etwas drauflegen."* (statt CTL/ATL/ACWR-Abkürzungen) |
| **Frühwarnung Verletzungsrisiko** | Multi-Session-Trend | *„HR-Drift bei den letzten 3 Tempoläufen +4, +6, +9 bpm trotz gleicher Pace. Trend zu steigender Belastung. Wenn Schlaf knapp ist: morgen lockerer."* |
| **Plan-Anpassungs-Vorschlag** ⭐ | Datenbasiert, trainingswissenschaftlich begründet | *„Letzte 2 Wochen ACWR > 1.4, HR-Drift in Tempoläufen steigt. Empfehlung: regenerative Mikrozyklus, 1× Tempolauf statt 2 in der nächsten Woche. Soll ich das so anpassen?"* (Anpassung folgt Belastungs-Modell, nicht „X von Y"-Heuristik) |

⭐ = vom Nutzer als besonders wichtig markiert

#### 5.8.3 Anti-Patterns (was Insights NICHT sein sollen)

| ❌ | Warum |
|---|---|
| *„Du warst 6s/km schneller als sonst."* | reine Datenanzeige, keine Erklärung, keine Maßnahme |
| *„CTL +3, ATL stabil, ACWR 1.05."* | Abkürzungs-Salve ohne Kontext, technisch |
| *„Plan-Treue: 4 von 5 Sessions."* | Score-Logik, nichts gelernt |
| *„PB auf 5km! 🎉"* | Achievement-Modus, kein Verständnis |
| *„Du hast eine Session abgebrochen — ich passe den Plan an."* | Heuristisch, nicht datenfundiert |

#### 5.8.4 Datenpunkte (vollständig)

Insights können auf diese Datenpunkte zurückgreifen:

**Aus dem Lauf:**
- Pace · Distanz · Zeit · Höhenmeter · Höhenprofil
- HR (Mittel, Max) · HR-Zonen-Verteilung · HR-Drift · HR/Pace-Decoupling
- Kadenz · Bodenkontaktzeit · Schrittlänge · vertikale Oszillation *(in Erweiterte-Analyse-Sektion, siehe §9.4)*
- Splits/Laps · Pace-Verlauf innerhalb der Session
- Untergrund (Asphalt / Trail / Bahn)

> Hinweis: GCT-Balance (links/rechts) ist mit Apple Watch **nicht** verfügbar (siehe §9.4) — daher nicht in Insights nutzbar.

**Plan-Bezug:**
- Soll/Ist (geplante vs. tatsächliche Pace, Distanz, Intervalle)
- Trainingstyp + Phase

**Form-Bezug:**
- Belastung / Erholung / Form-Indikator (CTL/ATL/TSB intern berechnet, in Sprache übersetzt)
- ACWR (Acute-Chronic Workload Ratio) — als Risiko-Indikator
- Multi-Session-Trends (Konsistenz, Steigerung, Stagnation)

**Kontext:**
- Wetter (Temperatur, Wind, Niederschlag)
- Schlaf (sofern verfügbar via Apple Health oder manueller Eingabe)
- Tageszeit
- Streckenwiederholung (Vergleich gleicher Route über Zeit)

### 5.8 Plan Adaptation

Der Trainingsplan ist ein lebendiges Dokument. Vier Prinzipien:

**1. Transparenz** — Nichts ändert sich im Hintergrund. Jede vorgeschlagene Änderung ist sichtbar und mit Begründung versehen.

**2. Nutzerkontrolle (Vorschlagsmodell)** — Die App schlägt vor, der Nutzer akzeptiert oder lehnt ab. Niemals automatische, stille Plan-Mutation.

**3. Adaptions-Auslöser:**
- **Nach jedem Lauf** — Was ist gelaufen? Wie war die Form? Wirkt sich auf nächste Sessions aus.
- **Wöchentlich** — Review der vergangenen Woche → nächste Woche feinjustieren.
- **Auf Nutzer-Anstoß** — *„Diese Woche war ich krank — plan um."*

**4. Adaptions-Scope** — Alles ist potenziell anpassbar:
- Pace-Vorgaben (basierend auf aktueller Form)
- Session-Anzahl und -Intensität
- Reihenfolge der Sessions in der Woche
- Verschiebung von Höhepunkten (langer Lauf, Tempolauf)
- Phasen-Umfang
- Das Ziel selbst (siehe Sonderfall)

**Sonderfall: Goal-Realism-Check**

Wenn ein Ziel anhand der Daten unwahrscheinlich wird (z.B. Pace-Vorhersage für Sub-2h reicht nicht mehr), spricht die App das offen an:

> *„Sub-2h wird mit der aktuellen Form schwer. Ein realistischeres Ziel wäre 2:05h — soll ich den Plan darauf anpassen?"*

Nutzer kann:
- **Akzeptieren** → neues Ziel + neuer Plan
- **Ablehnen** → ursprüngliches Ziel bleibt, App akzeptiert die Entscheidung



---

## 6. Bestand & Migration: was existiert, was wird umgebaut

> **Wichtig:** minsaga ist kein Greenfield. Es gibt bereits eine produktive App
> (Frontend + Backend + Daten). Diese Sektion macht transparent, **welcher Code/Feature
> bleibt, was umgebaut wird, was neu kommt, was wegfällt** — Brücke zwischen PRD und Build.

### 6.1 Status-Klassifikation

Pro Feature/Bereich eines von vier Labels:

| Label | Bedeutung | Beispiel |
|---|---|---|
| 🟢 **KEEP** | Existiert, wird übernommen, keine Änderung | CSV-Parser für Apple Watch Format |
| 🟡 **ADAPT** | Existiert, muss angepasst werden (UI, API, Naming) | Sessions-Liste → unter Tab „Training" einordnen |
| 🔵 **NEW** | Existiert nicht, wird neu gebaut | Goal Readiness, AI Coach Chat-FAB |
| 🔴 **REMOVE** | Existiert, wird ersatzlos entfernt | Level-System (FITNESS_LEVEL_SYSTEM_V2 → siehe Archiv) |

### 6.2 Routen-Map (Frontend) — Ist-Zustand

> Erfasst per Code-Audit am 2026-04-28.

| Aktuelle Route | Page-Komponente | Was der User dort macht | PRD-Tab | Status |
|---|---|---|---|---|
| `/heute` | `TodayPage` | Begrüßung, Fitness-Score (CTL/ATL/TSB), Wochenfortschritt, letzte Session, Insights, Ziel-Countdown, nächste Session | **Heute** | 🟡 ADAPT — Score ist Hero statt GoalCard; AI Insight nicht erstes Element |
| `/sessions` | `SessionsPage` | Session-Liste mit Filter, Pagination | **Training** | 🟡 ADAPT — Routing → `/training/sessions` |
| `/sessions/new` | `UploadPage` | FIT/CSV-Upload | **Training** | 🟡 ADAPT — Routing |
| `/sessions/new/strength` | `StrengthSessionPage` | Krafttraining manuell erfassen | **Training** | 🟡 ADAPT — Routing |
| `/sessions/:id` | `SessionDetailPage` | HR-Zonen, Laps, GPS-Karte, KI-Analyse, RPE, Notizen, FIT-Export | **Training** | 🟡 ADAPT — Routing; Soll/Ist-Vergleich-UI bitte verifizieren |
| `/sessions/:id/race-report` | `RaceReportPage` | Wettkampf-Auswertung mit km-Splits + KI | **Training/Analyse** | 🟡 ADAPT — Routing |
| `/analyse` | `AnalysePage` | Trends Pace/HR/Volumen, Kraft-Progression, Balance | **Analyse** | 🟡 ADAPT — Goal Readiness fehlt hier |
| `/plan` | `WeeklyPlanPage` | Wochenplan: 7-Tage, Drag-and-Drop, KI-Wochenreview | **Plan** | 🟡 ADAPT — Wochenplan ist „falscher" Default; PRD will Saison-Phasen als Hero |
| `/plan/goals` | `GoalsPage` | Wettkampfziele CRUD | **Plan** | 🟢 KEEP |
| `/plan/pacing` | `PacingPage` | Pacing-Strategie, Wetter, Höhenprofil, FIT-Export | **Plan** | 🟢 KEEP |
| `/plan/programs` (+ `/new`, `/:id`) | `TrainingPlansPage` / `TrainingPlanEditorPage` | Saison-Pläne mit Phasen, KI-Generierung, Changelog | **Plan** | 🟡 ADAPT — Naming („Programme" → „Plan") |
| `/plan/templates` (+ `/new`, `/:id`) | `SessionTemplates*` | Session-Vorlagen CRUD | **Sammlung** | 🟡 ADAPT — Routing → `/sammlung/vorlagen` |
| `/plan/exercises` (+ `/:id`) | `ExerciseLibrary*` | Übungsbibliothek | **Sammlung** | 🟡 ADAPT — Routing → `/sammlung/uebungen` |
| `/plan/routes` (+ `/new`, `/:id`) | `Routes*` / `RouteEditorPage` | Routen zeichnen, OSRM-Snap, Segmente, Pacing, GPX/FIT-Export | **Sammlung** | 🟡 ADAPT — Routing → `/sammlung/routen` |
| `/profile` | `AthleteProfilePage` | Profil, HF, KI-Keys, Provider | Header-Avatar | 🟢 KEEP |
| `/chat` | `ChatPage` | KI-Chat (Konversationen, Streaming, Plan-Anwendung) | AI Coach FAB | 🟡 ADAPT — Chat als FAB überall, nicht eigene Seite |
| `/ki-log` | `KiLogPage` | Alle KI-Calls (Debug) | (intern) | 🔴 REMOVE oder → `/admin` |
| `/admin/users` | `AdminUsersPage` | User-Verwaltung | (Admin) | 🟢 KEEP |

### 6.3 User-Flows (Ist-Zustand)

| Flow | Status | Anmerkung |
|---|---|---|
| Session-Upload Laufen (FIT/CSV) | 🟢 vollständig | — |
| Session-Upload Kraft (manuell) | 🟢 vollständig | — |
| Heute-Blick | 🟡 teilweise | Goal Readiness fehlt als Hero, Wochenkontext ohne heutige-Session-Detail |
| Pacing-Strategie | 🟢 vollständig | Wetter + Höhenprofil integriert |
| Wochenplan pflegen | 🟢 vollständig | Drag-and-Drop, KI-Review |
| KI-Chat | 🟡 teilweise | Chat ist isolierte Seite, kein FAB überall |
| Trainingsplan KI-generiert | 🟢 vollständig | Phasen, Wochentemplates, Changelog |
| Wochen-Review | 🟢 vorhanden | UI wenig prominent |
| Route zeichnen | 🟢 vollständig | Leaflet, OSRM, GPX/FIT-Export |
| Post-Race-Analyse | 🟢 vollständig | km-Splits + KI |

### 6.4 Backend-Capabilities (Ist-Zustand)

**Kernendpoints — alle 🟢:**
- Sessions CRUD + Upload + KI-Analyse + Empfehlungen
- Fitness: `/today`, `/score`, `/history`, `/insights`, `/quality` (CTL/ATL/TSB/ACWR/Form)
- Trends, Training-Balance, Wochen-Review-Generation
- Wochenplan + geplante Sessions
- Goals CRUD, Pacing-Berechnung + gespeicherte Strategien
- Trainingspläne + Phasen + KI-Generierung + Changelog
- Routen + OSRM + GPX/FIT-Export
- Session-Templates, Übungs-Bibliothek (mit Claude-Enrichment)
- KI-Chat (Konversation + Streaming SSE)
- Threshold-Tests (LTHR), Athletenprofil, Auth

**Externe Integrationen — alle 🟢:**
- OSRM (Routen-Snap, Rundkurse)
- Open-Meteo (Wetter)
- Claude API / OpenAI (User-Key wählbar)
- free-exercise-db (Übungs-Daten)

**🔴 Anti-Pattern-Verletzung gefunden:**
- `/api/v1/streak` Endpoint + `_build_motivation()` in `backend/app/api/v1/fitness.py` enthält Streak-Logik. Widerspricht §1.2 #3 (Anti-Streak-Shaming). **Fix**: Motivation-String entstreak-shamen, Endpoint deprecaten oder umfunktionieren (z.B. „90-Tage-Aktivitäten-Heatmap" ohne Streak-Wertung).

### 6.5 Domain-Modell (Ist-Zustand)

| Entität | Status |
|---|---|
| `users`, `refresh_tokens` (Auth) | 🟢 KEEP |
| `workouts` (alle Sessions, GPS, HR, Laps, TRIMP, Wetter-Enrichment) | 🟢 KEEP — Naming-Inkonsistenz: API/Frontend sagen „session", DB sagt „workout" |
| `athletes` (HF, KI-Keys, Provider, max CTL) | 🟢 KEEP |
| `threshold_tests`, `exercises`, `session_templates` | 🟢 KEEP |
| `race_goals`, `pacing_strategies`, `training_routes` | 🟢 KEEP |
| `training_plans`, `training_phases`, `weekly_plan_days`, `planned_sessions` | 🟢 KEEP |
| `ai_analysis_log`, `ai_recommendations`, `weekly_reviews`, `plan_changelog` | 🟢 KEEP — Plan-Changelog stützt §5.8 Transparenz |
| `chat_conversations`, `chat_messages` | 🟢 KEEP |

> **Korrektur ggü. älterem Plan:** `race_goals` als eigene Entity bleibt — funktioniert gut, kein Migrationsdruck zum Plan-internen Goal.

### 6.6 Lücken zur PRD-Vision (🔵 NEW)

**Tab-Ebene:**
- Bottom Nav: aktuelle 5 Slots ≠ PRD (Sessions/Profil raus, Sammlung/Training rein)
- Sammlung-Tab existiert nicht — Inhalte (Routen/Vorlagen/Übungen) sind unter `/plan/*` versteckt

**Heute-Tab (§4.1):**
- GoalCard als Hero (mit ReadinessRing + Faktoren) — nicht implementiert
- AI Coach Insight als erstes Element — falsche Reihenfolge
- WeekOverviewCard mit eingebetteter PlannedSessionCard-Detail — `WeekProgress` existiert, aber ohne Detail-Section
- GoalCard Tapering-/Race-Day-/Post-Race-State — alle nicht implementiert

**Plan-Tab (§4.4):**
- Plan = Saison-Hero statt Wochenplan-Hero (Strukturumbau)

**Querschnitt:**
- Equipment-/Schuh-Tracking (§2.3 #13) — kein Datenmodell, keine UI
- Workout-Export auf Apple Watch (ein Tap) — Pain Point, native iOS-App nötig
- Race-Day-Companion-Mode (Watch-App) — Vision
- Gel-Strategie / Versorgungs-Punkte auf Pacing — fehlt
- Voice & Copy: Tonalitäts-Regeln + Copy-Library im Code noch nicht etabliert

**Chat:**
- Chat-FAB-Konzept reconcilen: ChatFAB-Komponente in AppLayout existiert ABER `/chat`-Page parallel — Konzepte zusammenführen

### 6.7 Empfehlung — pragmatische Reihenfolge

> Vom Code-Explorer-Agent priorisiert nach Wert/Komplexität.

| # | Story | Wert | Komplexität |
|---|---|---|---|
| 1 | **Routing-Umbau** (`/sessions` → `/training`, `/plan/templates|exercises|routes` → `/sammlung/*`) + Sammlung-Tab | hoch | niedrig |
| 2 | **GoalCard als Hero auf Heute** (Race + Tage-Countdown + ReadinessRing) | hoch | mittel |
| 3 | **AI Insight als erstes Element auf Heute** | hoch | niedrig |
| 4 | **Streak-Anti-Pattern fixen** (`_build_motivation` in `fitness.py`) | mittel | niedrig |
| 5 | **Chat-FAB-Konzept reconcilen** (FAB überall + `/chat` als Full-Screen-Fallback) | mittel | mittel |
| 6 | **Equipment-/Schuh-Tracking Datenmodell + UI** | hoch | mittel |
| 7 | **Tapering-/Race-Day-/Post-Race-States auf GoalCard** | mittel | mittel |
| 8 | **Plan-Tab-Umbau** (Saison-Planung als Hero, Wochenplan als Untersektion) | mittel | hoch |

**Schlüsselerkenntnis:** Backend ist sehr weit. Kern-Endpoints, Domain-Modell, KI-Integrationen sind alle vorhanden und produktionsreif. Der Lift zur PRD-Vision ist **mehr UI-Routing + Komposition als Backend-Arbeit**.

### 6.8 Strategie-Pivot: Native iOS-App-Only (2026-04-28)

**Ursprünglicher Plan:** Web-App als primärer Channel, Quick Wins waren Web-Refactor (Routing, GoalCard-Hero, etc.).

**Neuer Plan:** Native iOS-App ist das Produkt. Web-App bleibt internes Dev-Tool / Dogfooding-Plattform.

#### Konsequenzen für die Bestand-Bewertung

| Asset | Vorher (Web-Strategie) | Jetzt (iOS-Strategie) |
|---|---|---|
| Web-App (React/TS) | 🟡 ADAPT (Hauptprodukt umbauen) | 🟡 ADAPT als internes Tool / Dogfooding |
| Backend (FastAPI + DB) | 🟢 KEEP, Hauptproduktion | 🟢 KEEP, Hauptproduktion (auch für iOS-App) |
| Native iOS-App | ⊘ existiert nicht | 🔵 NEW — komplett zu bauen (3–6 Monate SwiftUI) |
| Apple Watch Companion | Vision (Roadmap) | 🔵 NEW — wird MVP-Feature für Race-Day |

#### Was im Backend angepasst werden muss

- **HealthKit-Integration** (Endpoint zum Empfangen von Apple-Watch-/iPhone-Health-Daten)
- **StoreKit-Receipt-Validation** (eigene API zur Apple-Subscription-Validierung)
- **Subscription-Authorization-Schicht** (vor jedem KI-Call, hängt an StoreKit-Status)
- Keine Stripe-Integration (nicht nötig)

#### Realistischer Zeithorizont

Native iOS-Entwicklung Solo-Solo: **4–6 Monate** bis App Store Launch.

#### Web-App-Status (entscheiden)

Drei Optionen für die existierende Web-App:

| Option | Was |
|---|---|
| **A — Dogfooding-Tool** *(Empfehlung)* | Personal-Dev-Plattform, nicht öffentlich verkauft. Quick Wins (Routing-Umbau etc.) als Konzept-Schärfung machen. |
| **B — Marketing-Site** | Landing-Page mit Pricing + Beta-Sign-Up. Keine App-Funktion auf Web. |
| **C — Stilllegen** | Web-App komplett aufgeben. Alles auf iOS. |

→ **Aktuelle Entscheidung: A** — Web-App weiterentwickeln als Dogfooding-Plattform. Quick Wins schärfen Konzepte vor SwiftUI-Investment.

#### Personal-Use-First-Phase (2026-04-28)

**Wichtige Strategie-Klarstellung:** Markt-Launch ist nicht der nächste Schritt.

| Phase | Plattform | Zugang | Compliance-Druck | Zeithorizont |
|---|---|---|---|---|
| **1: Personal Use** | Apple TestFlight (Internal) | nur Nils' Geräte | minimal | nächste **6–12 Monate** |
| **2: Erweiterte Beta** | TestFlight External | bis 10k externe Tester | mittel (TestFlight-spezifisch) | wenn Konzept reif |
| **3: Markt-Launch** | Apple App Store | Public | voll (DSGVO + AGB + Subscription + Versicherung) | wenn Phase 2 erfolgreich |

**Konsequenzen:**

- **Keine Compliance-Bürokratie sofort** — DSGVO + AGB + AVVs + Berufshaftpflicht werden Phase-3-Items
- **Keine Subscription-Implementierung** — StoreKit-Integration wartet bis Phase 3
- **Keine Marketing/Pricing-Tests** — Pricing-Spec im PRD bleibt als Plan, nicht als Pflicht
- **Dogfooding = primärer Treiber** — Konzept reift durch eigene Nutzung über Monate
- **Monetarisierung = Optionalität** — kann später aktiviert werden, ist nicht Daily-Driver

→ **Effekt:** Die nächsten 6+ Monate fokussieren wir auf Native-iOS-App-Build, nicht auf Markt-Vorbereitung. §10 (Geschäftsmodell) und §11 (Compliance) bleiben **vollständig dokumentiert für Phase 3**, sind aber **nicht jetzt umzusetzen**.

#### Sprint-Roadmap (priorisiert: Personal Use first)

**Phase 1 — Personal Use (TestFlight, primärer Fokus für 6+ Monate):**

| Sprint | Was | Aufwand |
|---|---|---|
| **1.0** | Apple Developer Account + TestFlight-Setup | klein |
| **1.1** | Native iOS-App-Setup (SwiftUI, Architektur, AppShell, Navigation) | groß |
| **1.2** | HealthKit-Integration + Auto-FIT-Import + Auto-Workout-Erkennung | mittel |
| **1.3** | Heute-Tab nativ (GoalCard-Hero, WeekOverview, AI Coach Insight) | groß |
| **1.4** | Training-Tab nativ (Sessions, Detail, Soll/Ist-Compare, Collapse-Sektionen) | mittel |
| **1.5** | Plan-Tab nativ + Pacing-Rechner | mittel |
| **1.6** | Analyse-Tab nativ + Insights-Engine | mittel |
| **1.7** | Sammlung-Tab nativ (Routen, Vorlagen, Übungen) | mittel |
| **1.8** | Apple Watch Companion (Workout-Export, Race-Day-Begleitung) | mittel-groß |
| **1.9** | Personal-Use-Phase: 3–6 Monate eigene Nutzung, Konzept feinjustieren | — |

**Phase 2 — Erweiterte Beta (wenn Konzept reif, ~6 Monate später):**

| Sprint | Was | Aufwand |
|---|---|---|
| **2.0** | TestFlight External (bis 10k Tester) öffnen | klein |
| **2.1** | Feedback-Mechanismus für Beta-Tester | mittel |
| **2.2** | Konzept-Iterationen aus Beta-Feedback | variabel |

**Phase 3 — Markt-Launch (wenn Beta erfolgreich, Entscheidung zu Monetarisierung):**

| Sprint | Was | Aufwand |
|---|---|---|
| **3.0** | StoreKit-Integration + Tier-Logik + Upgrade-CTAs | mittel |
| **3.1** | Compliance (DSGVO, AGB, Datenschutzerklärung, Disclaimer) | mittel |
| **3.2** | Berufshaftpflicht-Versicherung + ggf. UG-Umfirmierung | klein |
| **3.3** | App Store Submission + Marketing | mittel |

**Realistischer Zeithorizont Phase 1:** 4–6 Monate Solo-Entwicklung bis personal-nutzbar.

**Parallel auf der Web-App (Phase 1, niedrige Priorität):** Quick Wins als Konzept-Schärfung — Routing-Umbau, GoalCard-Hero, AI-Insight-First, Streak-Anti-Pattern-Fix. Dogfooding-Plattform für dich selbst.

### 6.7 Abomodell-Schicht (Verweis)

Der Endnutzer gibt **keinen eigenen AI-Provider-Key** ein — alle KI-Calls laufen über den Entwickler-Key. Damit das Geschäft trägt, braucht es eine Abomodell-Schicht.

→ **Vollständige Spezifikation in [§10 Geschäftsmodell](#10-geschäftsmodell).**

**Folgen für andere Sektionen:**
- §2.5.7 Onboarding: KI-Provider-Key wird nicht abgefragt
- §6.4 Backend: Authorization-Schicht vor KI-Endpoints
- §7 Was nicht: Abomodell ist **explizit IM Scope**, nicht ausgeschlossen

---

## 7. Was wir bewusst NICHT machen

- **Levels / Gamification** → siehe [`archive/FITNESS_LEVEL_SYSTEM_V2.md`](archive/FITNESS_LEVEL_SYSTEM_V2.md) für Begründung
- **Social Features** (Follower, Kudos, Activity-Feed) — minsaga ist Solo-Coach, kein soziales Netz
- **Wearable-Integrationen** (Garmin Connect, Apple Health) — vorerst nicht, manueller Upload reicht
- *[weitere Anti-Features im Interview ergänzen]*

---

## 8. Offene Fragen / Entscheidungs-Backlog

| # | Frage | Status | Owner | Notiz |
|---|---|---|---|---|
| 1 | Tab-Namen final | offen | Nils | „Analyse" + „Sammlung" sind Vorschläge, müssen im Interview validiert werden |
| 2 | URL-Migration `/fortschritt` → `/analyse` | offen | Nils | Mit Redirect oder Breaking Change? |
| 3 | AICoachInsight ↔ Alert-Komponente | offen | — | Im Figma wurde Alert(variant=ai) erstellt, AICoachInsight noch nicht entfernt |
| 4 | Goal Readiness — Implementation-Scope | offen | — | Konzept liegt vor, Build-Story fehlt |
| 5 | Mental Model / Vokabular | offen | Nils | Wird in S3 erfasst |
| 6 | `AppShell` vs `AppShellMobile` konsolidieren | offen | — | Funktional sehr ähnlich — eine sollte die andere ersetzen |
| 7 | `AppShellDesktop` — 4 Content-Slots | offen | — | Verwendung der 3 Sub-Slots (Content Slot 2, Content2) zu klären |
| 8 | `AICoachInsight` deprecaten | offen | — | Wird durch `Alert(variant=ai)` abgelöst — alte Komponente löschen, Verwendungen migrieren |
| 9 | `Avatar` Bild-Modus | offen | — | Nur Initialen-Modus implementiert — Bild-Variante ergänzen, falls für Profil-Bild gewünscht |
| 10 | `Progress.fill` als Variant | offen | — | 11 Stufen (0/10/.../100) — keine kontinuierliche Animation. Für glatten Verlauf code-getriebene Implementation |
| 11 | **Race-Day-Companion-Mode** auf Watch | Vision | — | Active-Begleitung während Race (Splits, Pace-Hinweise, Streckenprofil). Erfordert native Watch-App. Siehe §2.2.2 Race-Day. |
| 12 | **Streckenprofil + Versorgungs-Punkte** für Race-Pacing | offen | — | GPX-Import, Wasser/Verpflegung als Marker. Beeinflusst Pacing-Strategie und Gel-Strategie. Siehe §2.3 Job 8. |
| 13 | **Equipment-Tracking (Schuhe)** | offen | — | Pro Training Schuh festhalten, KM-Stand pro Schuh, Ausmusterungs-Warnung. Siehe §2.3 Job 13. |
| 14 | **Insights-Spezifikation** | offen | Nils | Welche Datenpunkte fließen ein, wie tief gehen die Insights. **Wird in S2 / Insights-Fragerunde geklärt.** |
| 15 | **Wetter-Berücksichtigung in Insights** | erledigt-bestätigt | — | Open-Meteo ist angebunden (siehe §6.4). Korrelations-Insights können auf Wetterdaten zugreifen. |
| 16 | **Streak-Logik in `_build_motivation`** | **Fix erforderlich** | — | Backend-Endpoint `/api/v1/streak` + Motivation-String widersprechen Anti-Pattern §1.2 #3. Siehe §6.4. Fix als Story Priorität 4. |
| 17 | **`workouts` vs. „session" Naming** | offen | — | DB-Tabelle heißt `workouts`, API/Frontend sagen „session". Konsistenz herstellen oder bewusst tolerieren? |
| 18 | **Abomodell — Free vs. Paid Tier** | erledigt-2026-04-28 (rev2) | Nils | Spezifiziert in §10 (Free + Wochenabo 3,99 / Monatsabo 12,99 / Jahresabo 99 — kein Trial, Wochenabo statt Trial, Free hat 0 KI außer Onboarding-Sample) |
| 19 | **Companion-Mode Apple Watch** | Vision (Roadmap) | — | Aktive Begleitung während Race + ggf. Training. Erfordert native Watch-App. Siehe §2.5.6. |
| 20 | **HealthKit-Integration** | offen | — | Auto-FIT-Erkennung + Schlaf + Ruhe-HF aus Apple Health. Siehe §2.5.2 + §2.5.7. |

---

## 9. Glossar & Vokabular

> Erfasst in **Interview S3 (2026-04-28)**. Verweis auf technische Entitäten: [`reference/DOMAIN_MODEL.md`](reference/DOMAIN_MODEL.md).

### 9.1 Klassifikations-Schema

Jeder Trainings-Begriff fällt in eine von vier Klassen:

| Klasse | Bedeutung | UI-Verhalten |
|---|---|---|
| ✅ **Frei** | Nutzer verwendet im Alltag | direkt in UI ohne Zusatz |
| 🔁 **Mit Erklärung** | Coach-Sprache; Nutzer versteht, will lesen | in UI mit On-Demand-(i)-Icon (Pattern §5.6) |
| ❌ **Nicht in UI** | Jargon, vermeiden | komplett raus |
| ❓ **Im Glossar zu klären** | nicht selbsterklärend / unsicher | Definition + UI-Entscheidung TBD |

### 9.2 Belastung & Form

✅ **Frei**: Form · Belastung · Erholung · Müdigkeit · Fitness · Tagesform · Überbelastung · Tapering

🔁 **Mit Erklärung**: Frische · Trainingsload · TSB · CTL · ATL · ACWR

❌ **Nicht in UI**:
- ~~Form-Indikator~~ → durch **„Form"** ersetzt (synonym, vereinheitlicht)

### 9.3 Trainingstypen & Intensität

✅ **Frei**: Tempolauf · Intervalltraining · Longrun / langer Lauf · **Lockerer Lauf** · Regenerationslauf · Fahrtspiel / Fartlek · Schwellenlauf · VO2max · Zone 1–5 · Zielpace

🔁 **Mit Erklärung**: GA1 / GA2 · Schwelle · RPE · **Polarized Training** · **Pyramidal Training**

🔁 **Sub-Form**: **Wiederholungslauf / Repetitions** wird als Sub-Form von „Intervalltraining" geführt (z.B. „Kurze Intervalle"), kein eigenständiger Trainingstyp.

❌ **Nicht in UI**:
- ~~Ruhelauf~~ → durch **„Lockerer Lauf"** ersetzt (User-Vokabular)
- ~~Marathonpace~~ → für HM-Athlet nicht relevant. Nur **„Zielpace"** verwenden.

### 9.4 Technik & Übungen

✅ **Frei**: Kadenz · Lauf-ABC · Skippings · Anfersen · Kniehebellauf · Steigerungslauf · Dehnen · Cool-down · Phase · **Warm-Up**

🔁 **Mit Erklärung**: Schrittlänge · Bodenkontaktzeit

🔁 **Nur in „Erweiterte Analyse"-Sektion**: **Vertikale Oszillation** (Apple Watch sammelt diese Daten ab WatchOS 9)

❌ **Nicht in UI**:
- ~~GCT-Balance~~ → Apple Watch kann diese Daten nicht sammeln. Garmin-spezifisch (HRM-Pro/Running Dynamics Pod). Komplett raus.
- ~~Aktivierung~~ → durch **„Warm-Up"** ersetzt

### 9.5 minsaga-spezifisch (Marken-Wortmaterial)

🔁 **Mit Erklärung** (App muss aktiv einführen): Goal Readiness · Saga · Kapitel

✅ **Frei**: Phase

> **Wichtige Erkenntnis:** „Saga" und „Kapitel" sind keine Wörter, die der Nutzer selbst im Alltag nutzt. Die App führt sie ein. Sparsam und an Schwellen einsetzen (siehe §1.3.2).

### 9.6 Geklärte Sprach-Entscheidungen (2026-04-28)

| # | Entscheidung | Begründung |
|---|---|---|
| 1 | „Form-Indikator" → durch „Form" ersetzen | synonym, vereinheitlicht |
| 2 | „Ruhelauf" → durch „Lockerer Lauf" ersetzen | User-Vokabular |
| 3 | „Wiederholungslauf/Repetitions" → Sub-Form von Intervalltraining | nicht eigenständiger Trainingstyp |
| 4 | „Polarized Training" → mit Erklärung in UI | aktiv als Konzept einführen |
| 5 | „Pyramidal Training" → mit Erklärung in UI | parallel zu Polarized, zur Vergleichbarkeit |
| 6 | „Marathonpace" → komplett raus | für HM-Athlet nicht relevant |
| 7 | „GCT-Balance" → komplett raus | Apple Watch sammelt nicht (Garmin-only) |
| 8 | „Vertikale Oszillation" → nur Erweiterte Analyse-Sektion | Apple Watch sammelt ab WatchOS 9, optional sichtbar |
| 9 | „Aktivierung" vs. „Warm-Up" → **„Warm-Up"** | fitness-typisch, kürzer |

---

## 10. Geschäftsmodell

> Erfasst in Abomodell-Session (2026-04-28). Mehrfach iteriert nach Cost-Realismus-Check.
>
> ⏰ **Phasen-Status:** Diese Sektion beschreibt das Modell für **Phase 3 (Markt-Launch)**. In Phase 1 (Personal Use, TestFlight) und Phase 2 (Beta) ist Subscription-Layer **nicht aktiv**. Siehe §6.8 Sprint-Roadmap.

### 10.1 Grundprinzipien

- **Der Endnutzer gibt KEINEN AI-Provider-Key ein** — alle KI-Calls laufen über Entwickler-Key
- **Free-Tier ist echt nutzbar** im Sinne eines voll-funktionalen **Werkzeugs**, aber **ohne KI-Coach**
- **Klare Trennlinie:** Werkzeug (algorithmische Funktionen) Free · Coach (KI-Funktionen) Paid
- **Wochenabo statt Trial** — selbst-finanzierender Einstieg statt Subvention
- **Transparente, einfach kündbare Bezahlung**
- **Keine Dark Patterns** — kein Streak-Lock, keine Daten-Geisel, keine Manipulation

### 10.2 Tier-Architektur

**Vier Tiers:** Free + drei Paid-Optionen mit unterschiedlicher Commitment-Tiefe.

| Bereich | Free | Wochenabo | Monatsabo | Jahresabo |
|---|---|---|---|---|
| Sessions hochladen, verwalten | ✅ | ✅ | ✅ | ✅ |
| **Algorithmischer Plan-Generator** (Templates) | ✅ | ✅ | ✅ | ✅ |
| Wettkampfziel, Pacing | ✅ | ✅ | ✅ | ✅ |
| Trends, Stats, CTL/ATL/TSB als Zahlen | ✅ | ✅ | ✅ | ✅ |
| Goal Readiness als Score (numerisch) | ✅ | ✅ | ✅ | ✅ |
| Routen, Übungs-Bibliothek | ✅ | ✅ | ✅ | ✅ |
| Algo-Wochen-Review (regel-basiert) | ✅ | ✅ | ✅ | ✅ |
| **KI-Insights nach Sessions** | ❌ | ✅ | ✅ | ✅ |
| **AI Coach Chat** | ❌ | ✅ | ✅ | ✅ |
| **KI-Wochen-Review** | ❌ | ✅ | ✅ | ✅ |
| **KI-Plan-Generierung** | **1× Lifetime beim Onboarding** | ✅ unbegrenzt | ✅ | ✅ |
| **Plan-Anpassungs-Vorschläge** | ❌ | ✅ | ✅ | ✅ |
| Coach-Sprache (Begleiter / Coach / Zeuge) | ❌ | ✅ | ✅ | ✅ |

### 10.3 Onboarding-KI-Sample (Free-User)

**Einmalig beim Onboarding** generiert die KI dem Free-User einen vollständigen Trainings-Plan (Coach-Dialog → KI-Plan).

- Zeigt einmal das Coach-Erlebnis
- Macht den Free-Plan persönlicher als der algorithmische Default
- Danach: KI-Plan-Anpassungen + Insights + Chat nur mit Wochenabo+

**Cost pro Free-User**: ~$0.20 einmalig (Plan-Generierung).

### 10.4 Pricing

| Tier | Preis | Pro Tag | Vergleich |
|---|---|---|---|
| **Free** | 0 € | — | algorithmische Funktionen + 1× Onboarding-KI-Plan |
| **Wochenabo** | 3,99 € | 0,57 €/Tag | niedrige Einstiegshürde, selbst-finanzierender Einstieg |
| **Monatsabo** | 12,99 € | 0,43 €/Tag | knapp unter Runna (~17 €), klar über Strava (~10 €) |
| **Jahresabo** | 99 € | 0,27 €/Tag | ~36% Rabatt vs. Monatsabo |

**Pricing-Logik:** Wer länger committed, zahlt weniger pro Tag. Klare Anreize zur längeren Bindung.

### 10.5 Wochenabo statt Trial

Statt klassischem Trial (gratis 14 Tage, dann Subvention-Rückstand) bieten wir **selbst-finanzierende Wochenmitgliedschaft** als Einstieg:

| Modell | Cost/User | Revenue | Net |
|---|---|---|---|
| Trial 14 Tage | ~$2 | 0 € | **−$2** |
| Wochenabo 3,99 € | ~$1 | $4 | **+$3** (75% Marge) |

**Bonus-Effekte:**
- User hat schon Zahlungsdaten in Stripe/Apple → Friction für Upgrade auf Monat/Jahr minimal
- Echtes Commitment → höhere Conversion-Wahrscheinlichkeit
- Wochenabo kann auto-renewing sein (default off, opt-in)

### 10.6 Distribution — Apple StoreKit only

**Strategische Entscheidung (2026-04-28):** Vertrieb ausschließlich über Apple App Store.

| Kanal | Status | Begründung |
|---|---|---|
| **Apple StoreKit** | ✅ einziger Channel | Native iOS-App ohnehin geplant (Companion-Watch + Sensor-Zugriff) |
| ~~Stripe (Web)~~ | ❌ entfällt | Web-App bleibt internes Tool, kein Verkauf |
| ~~Google Play~~ | ❌ vorerst nicht | Apple-Demographic priorisiert |

**Konsequenzen:**

- ✅ Apple regelt MwSt + Refunds + Auto-Renewal + Family-Sharing automatisch
- ✅ Operativ einfacher (keine OSS-Verfahren, keine eigene MwSt-Pflicht)
- ✅ Companion-Apple-Watch wird realisierbar (Race-Day, Live-Begleitung)
- ✅ HealthKit-Integration für Auto-FIT-Import ohne Workflow-Friction
- ❌ Apple-Cut 30% Jahr 1 (15% ab Jahr 2)
- ❌ Android-User komplett ausgeschlossen (vorerst)
- ❌ Apple kann App ablehnen → totaler Plattform-Verlust (Risiko)

→ **Eigentliche Konsequenz:** Web-App-Strategie wird obsolet. Native iOS-App ist das Produkt. Web-App = internes Dev-Tool für Dogfooding. Siehe §6.8.

### 10.7 Cost-Modell — Apple StoreKit only (mit MwSt-Korrektur)

Mit **Claude Sonnet 4.5/4.6** ($3 input / $15 output per 1M tokens) — Premium-Qualität.

#### Cost pro KI-Call (konservativ realistisch)

| Feature | Token-Mix | Cost/Call |
|---|---|---|
| Insight nach Session | 9.500 in / 700 out | **~$0.039** |
| Chat-Konversation (10 Msg) | 62k in / 6k out | **~$0.28** |
| Wochen-Review | 15k in / 1.5k out | **~$0.068** |
| KI-Plan-Generierung (mehrstufig) | 25k in / 8k out | **~$0.20** |
| Plan-Anpassungs-Vorschlag | 7.5k in / 700 out | **~$0.033** |

#### Echtes Net-Revenue pro Tier (mit MwSt-Abzug)

Pricing ist **brutto** (inkl. 19% MwSt). Apple ist Merchant-of-Record — zieht MwSt + Apple-Cut automatisch ab.

**Apple iOS Jahr 1 (30% Cut, MwSt vorab):**

| Tier | **Net** |
|---|---|
| Wochenabo | **2,34 €** |
| Monatsabo | **7,64 €** |
| Jahresabo (per-Mo) | **4,85 €** |

**Apple iOS Jahr 2+ (15% Cut):**

| Tier | **Net** |
|---|---|
| Wochenabo | **2,85 €** |
| Monatsabo | **9,28 €** |
| Jahresabo (per-Mo) | **5,89 €** |

#### Margen-Tabelle mit echten Zahlen (Apple)

KI-Cost aktiv ~3,85 €/Monat (= $4.20 bei $1.09/€).

| Tier × Phase | Net/Mo | Marge |
|---|---|---|
| Apple Monatsabo · Jahr 1 | 7,64 € | **50%** |
| Apple Monatsabo · Jahr 2+ | 9,28 € | **59%** |
| **Apple Jahresabo · Jahr 1** | **4,85 €** | **21%** ⚠️ ENG |
| Apple Jahresabo · Jahr 2+ | 5,89 € | **35%** |
| Apple Wochenabo (1 Wo) | 2,34 € · J1 / 2,85 € · J2 | **~50–60%** |

#### ⚠️ Apple-Jahresabo Jahr 1: nur 21% Marge

Strukturell tragbar wegen langer Apple-User-Retention (LTV holt das auf), aber **Risiko-Faktor bei Skalierung**.

→ **Aktuelle Entscheidung:** Pricing bei 3,99 € / 12,99 € / 99 € lassen, Apple-Jahresabo-Risiko in Jahr 1 bewusst tragen. Nach Jahr 1 → 35% Marge.

#### Profitabilitäts-Szenarien (Apple-only, mit MwSt + 30% Cut Jahr 1)

Annahme: 60% Monatsabo, 30% Jahresabo, 10% Wochenabo (rotierend).

| Szenario | Free | Paid | Apple-Net-Revenue | KI-Cost | **Net** |
|---|---|---|---|---|---|
| Klein, 5% Conv. | 95 | 5 | ~32 € | ~17 € | **+15 €** ✅ |
| Mittel, 10% Conv. | 450 | 50 | ~322 € | ~168 € | **+154 €** ✅ |
| 5k User, 10% Conv. | 4.500 | 500 | ~3.220 € | ~1.680 € | **+1.540 €** ✅ |

→ Modell trägt auch Apple-only, aber **40% niedriger** als bei Stripe-Mix wegen 30% Apple-Cut. Nach Jahr 1 wird das deutlich gesünder (Cut sinkt auf 15%).

#### Modell-Wahl

**Default Sonnet überall** — wird mit Real-Daten optimiert. Mögliche spätere Optimierung:
- Haiku für Insights/Wochen-Review (5× günstiger)
- Sonnet bleibt für Chat (Begleiter-Stimme nicht kompromittierbar) und Plan-Generierung
- Opus für Premium-Tier (falls je eingeführt — aktuell nicht geplant)

### 10.8 Technische Anforderungen (🔵 NEW, alle nicht implementiert)

#### Subscription-Layer

- **Subscription-Status** in `users` oder eigener `subscriptions`-Tabelle
- **Subscription-Tier-Tracking** (none / weekly / monthly / yearly)
- **Subscription-Lifecycle-Events** (created, renewed, cancelled, expired, refunded)
- **Authorization-Middleware** vor jedem KI-Endpoint (Subscription-Check)
- **Onboarding-Sample-Counter** pro User (1× KI-Plan Lifetime)

#### Payment-Integration (Apple StoreKit only)

- **Apple StoreKit 2-Integration** (Receipt-Validation, Subscription-Lifecycle)
- **Subscription-Group** in App Store Connect mit drei Produkten (Wochen / Monat / Jahr)
- **Server-Side-Receipt-Validation** über Apple Server-to-Server Notifications
- **Family-Sharing-Support** (Apple-Standard, ein Sub teilbar in Family-Group)
- **Restore-Purchases-Funktion** (Pflicht laut Apple Guidelines)
- **Cancel-Subscription-Link** in App-Settings (Pflicht laut Apple Guidelines)

> Stripe-Integration entfällt (siehe §10.6).

#### Algorithmische Fallbacks (Free-Tier-Säule)

- **Algorithmischer Plan-Generator** als separater Service (kein LLM) — Templates × Phasen × Wochen
- **Algorithmischer Wochen-Review-Generator** (regel-basiert) — Plan-Treue · Volumen-Δ · Highlights aus Daten
- *Hinweis:* algorithmischer Insight-Generator entfällt (Free hat keine Insights mehr — durch Wochenabo abgedeckt)

#### UI-Komponenten

- **Tier-Picker** (Wochenabo / Monatsabo / Jahresabo) als Komponente, kontextabhängig
- **Upgrade-CTA-Card** (in Heute, Session-Detail, Chat — wenn Free-User KI-Feature aufruft)
- **Subscription-Status-Anzeige** im Profil/Settings (aktuelles Tier, Renewal-Datum, Cancel-Link)
- **Onboarding-Sample-Banner** im Heute, der den 1×-KI-Plan kommuniziert

→ Diese Anforderungen sind Basis für Sprint-Planung; vor Marktstart Pflicht.

### 10.9 Cost-Schutz für Chat (Power-User-Risiko)

**Problem:** Chat ist mit Abstand das teuerste Feature ($0.28 pro 10-Message-Konversation, längere Konversationen $1–3+ wegen Token-Wachstum). Heavy-User (5 Chats/Tag) verursachen $42/Monat KI-Cost — das wäre struktureller Verlust.

**Vier Maßnahmen, kombiniert wirksam:**

#### Maßnahme 1 — Konversations-Hard-Cap

Pro Konversation: max **30 Messages** ODER max **10.000 Tokens Input**. Bei Erreichen: User-freundliches Framing *„Neue Konversation für mehr Klarheit starten?"*.

→ Verhindert Token-Explosion in extrem langen Konversationen. Pro-Konversation-Cost capped bei ~$0.50.

#### Maßnahme 2 — Daily- und Monthly-Limits (Soft-Caps)

Pro Tier:

| Tier | Konversationen/Tag | Konversationen/Monat | Beim Erreichen |
|---|---|---|---|
| Wochenabo (3,99 €) | max 5 | 25 | *„Heute genug Coach-Gespräche. Weiter morgen."* |
| Monatsabo (12,99 €) | max 10 | 100 | analog |
| Jahresabo (99 €) | max 10 | 100 | analog |

→ Soft-Caps mit menschlicher Sprache. 99% der User merken nichts. 1–5% Heavy-User werden sanft gebremst.

#### Maßnahme 3 — Context-Compression

Bei Konversationen mit >10 Messages: ältere Messages werden automatisch durch eine Zusammenfassung ersetzt, statt komplett mitgeschickt.

- Vorher: 30 Messages × 200 Tokens = 6.000 input pro neuer Message
- Nachher: Zusammenfassung 500 + letzte 5 Messages × 200 = 1.500 input

→ **75% Token-Reduktion** in langen Konversationen, ohne dass User es bemerkt.

#### Maßnahme 4 — Hard-Cap als Notausgang

Bei Überschreiten des Soft-Limits (z.B. via Bot/Script):

- 24h Hard-Stop
- Email-Notification *„Außergewöhnliche Nutzung erkannt"*
- Bei wiederholtem Auftreten: Account-Review

→ Schutz vor Bot-Attacken.

#### Cost-Modell mit Limits (100 Paid-User, Pareto 70/25/5)

| Profil | Anzahl | Cost/Person | Gesamt |
|---|---|---|---|
| Light (5 Chats/Mo) | 70 | $1.40 | $98 |
| Medium (30 Chats/Mo) | 25 | $5.50 | $138 |
| Heavy (Limit erreicht) | 5 | $18 | $90 |
| **Total Cost** | 100 | — | **$326** |
| Revenue (100 × $13.40 net) | | | $1.340 |
| Stripe-Fees | | | $80 |
| **Net** | | | **+$934/Monat (~75% Marge)** |

→ Modell trägt **auch mit Heavy-User-Anteil**, weil Limits Verluste begrenzen.

### 10.10 Anti-Abuse-Maßnahmen

- **E-Mail-Verifikation** Pflicht bei Account-Erstellung (gegen Multi-Account-Onboarding-Sample-Reset)
- **Ein Account pro User** (über Email + Apple-ID + Google-ID Tracking)
- **Rate-Limit** auf API-Ebene (gegen Bot/Script-Abuse)
- **KI-Prompt-Hardening** gegen Token-Burning-Attacks (z.B. „Erzähl mir Geschichte mit 100k Wörtern")
- **Conversation-Limits** siehe §10.9

### 10.11 Rechtsform & Steuern

**Empfehlung für Solo-Founder beim Start:** Einzelunternehmer / Gewerbeanmeldung.

| Form | Stammkapital | Haftung | Wann |
|---|---|---|---|
| **Einzelunternehmer** | 0 € | privat (voll) | **Start** — niedrigste Hürde |
| UG (haftungsbeschränkt) | ~1k € | beschränkt | bei >50k €/Jahr Umsatz oder Haftungs-Sorgen |
| GmbH | 25k € | beschränkt | wenn Investoren / B2B / Mitgründer |

**Operative Pflichten:**

- [ ] Steuerberater konsultieren (Apple/Stripe + OSS + Reverse-Charge — kompliziert)
- [ ] Gewerbeanmeldung beim lokalen Ordnungsamt
- [ ] Geschäftskonto trennen vom Privatkonto
- [ ] Buchhaltungs-Software (Lexoffice / Sevdesk / Buchhaltungsbutler)
- [ ] Berufshaftpflicht-Versicherung gegen KI-Plan-Haftungsfälle prüfen

**MwSt-Handling (Apple-only):**

Apple ist Merchant-of-Record in EU — zieht MwSt automatisch ab + führt sie ab. Du erhältst Net-Beträge auf dein Geschäftskonto. Steuerlich einfach: Apple-Auszahlungen als gewerbliche Einnahmen verbuchen.

> Stripe entfällt (siehe §10.6). Damit kein USt-Schuldner-Komplex, kein OSS-Verfahren.

**Kleinunternehmerregelung** (bis 22k €/Jahr Umsatz keine MwSt-Pflicht): bei Apple-Sales nicht anwendbar (EU-grenzüberschreitend), praktisch wenig Vorteil im SaaS-Modell.

#### Apple Developer Account-Typ

Apple unterscheidet zwei Konto-Typen:

| Account-Typ | Verfügbar | Voraussetzung | Marken-Sichtbarkeit |
|---|---|---|---|
| **Individual** | ✅ als Einzelunternehmer | Gewerbeanmeldung + Bankkonto + Apple ID | Persönlicher Name im App Store |
| **Organization** | ❌ Einzelunternehmer | UG/GmbH/AG + D-U-N-S Number | Firmenname im App Store |

→ **Als Einzelunternehmer KEIN Problem für App-Veröffentlichung**, aber:
- Im App Store erscheint dein **persönlicher Name** als Entwickler (nicht „minsaga")
- Migration von Individual → Organization ist später möglich (bei Umfirmierung auf UG)

#### Hauptrisiko: persönliche Haftung

Der eigentliche Grund für UG/GmbH ist **nicht** Apple oder Stripe, sondern Haftung:

- Einzelunternehmer haftet mit **Privatvermögen** (z.B. bei Klagen wegen KI-Plan-bedingten Verletzungen)
- UG/GmbH beschränkt Haftung auf Stammkapital + Rücklagen
- Berufshaftpflicht mildert ab, aber nicht 100%

→ **Strategie:** Start als Einzelunternehmer (niedrige Hürde, Markt-Test). Umfirmieren auf UG bei >500 Paid-Usern oder erstem Haftungs-Vorfall.

---

## 11. Compliance & Datenschutz

> Pflicht-Spezifikation für **Phase 3 (Markt-Launch)**. DSGVO + EU AI Act + Apple App Store.
>
> ⏰ **Phasen-Status:** In Phase 1 (Personal Use) reduzierte Anforderungen. Voller Compliance-Stack wird vor App Store Submission aktiviert. Siehe §6.8 Sprint-Roadmap, Phase 3.

### 11.1 DSGVO-Pflichten

#### Datenschutzerklärung (Privacy Policy)

Pflicht auf Website + in der App (Settings + Onboarding-Link). Inhalt:

- Welche Daten erhoben werden: Name, Email, Trainings-Daten, optional Health-Daten (HF, Schlaf), Geräte-/Apple-Watch-Metadaten, Zahlungsdaten (über Stripe/Apple)
- Zweck pro Datenkategorie
- Rechtsgrundlage (Art 6 DSGVO):
  - „Vertragserfüllung" für App-Funktion
  - **„Einwilligung" für KI-Verarbeitung**
- Empfänger / Auftragsverarbeiter: Anthropic, Stripe, Apple, Hetzner (Hosting), Email-Provider
- Speicherdauer pro Datenkategorie
- Betroffenenrechte: Auskunft, Berichtigung, Löschung, Datenexport, Widerspruch, Beschwerde bei Aufsichtsbehörde
- Kontakt-Email für Datenschutz-Anfragen

#### Auftragsverarbeitungs-Verträge (AVV)

Pflicht mit jedem, der personenbezogene Daten verarbeitet:

| Anbieter | AVV verfügbar | Action |
|---|---|---|
| **Anthropic** | ja, [anthropic.com/legal/dpa](https://www.anthropic.com/legal/dpa) | unterschreiben |
| **Stripe** | ja, automatisch im Account | bestätigen |
| **Apple** | über App Store Connect | automatisch |
| **Hetzner / Coolify** | im Hetzner-Robot | unterschreiben |
| **Apple/Google OAuth** | über OAuth-Setup | bestätigen |

#### Einwilligung für KI-Verarbeitung

Im Onboarding **explizit** einholen, separat von App-Nutzung:

> *„Ich willige ein, dass minsaga meine Trainings-Daten an die KI-Anbindung (Anthropic Claude) sendet, um personalisierte Insights und Coaching zu liefern."*  ☐

- Default: nicht angekreuzt
- Frei widerrufbar in Settings
- Bei Widerruf: keine KI-Features mehr, App weiter nutzbar (algorithmische Funktionen)

#### Datenexport & Löschung

- **Export** (Art 20 DSGVO): User kann alle Daten als JSON/CSV-Export anfordern (Settings-Button)
- **Löschung** (Art 17 DSGVO): Account-Löschung mit allen Daten innerhalb 30 Tagen
- **Backup-Bereinigung** parallel — Backups dürfen User-Daten nicht beliebig lange behalten (Standard: 30 Tage)

### 11.2 Datenminimierung beim KI-Call

Strikt definiert, was an Anthropic geht:

**✅ Wird mitgeschickt:**
- Trainings-Daten (Pace, HR, Distanz, Datum, Splits, Kadenz)
- Plan-Kontext (Phasen, Wochenstruktur, Race-Goal)
- Wetter-Kontext (für Korrelations-Insights)
- Interne, anonyme User-ID (UUID)

**❌ Wird NICHT mitgeschickt:**
- Email
- Name (Vor-/Nachname)
- Geburtstag
- Telefon
- Bezahl-Daten
- Geo-Standort (außer zur Strecken-Berechnung, dann ohne Personen-Bezug)

### 11.3 Privacy-Pledge (User-Trust)

Im Onboarding + Settings + Datenschutzerklärung deutlich kommuniziert:

> *„Deine Trainings-Daten werden NICHT zum Training von KI-Modellen verwendet. Die Anthropic-API-Calls sind explizit ausgeschlossen vom Modell-Training (siehe Anthropic AGB)."*

Wichtige Trust-Botschaft, weil viele User Sorge haben.

### 11.4 EU AI Act

Gilt voll ab August 2026. **minsaga ist nicht Hochrisiko-Klassifikation** (kein Hochrisiko-Anwendungsfall wie Bewerbungsentscheidung, Kreditvergabe, Strafverfolgung).

**Reduzierte Pflichten:**

| Pflicht | Erfüllt |
|---|---|
| **Transparenz** — User muss wissen, dass mit KI interagiert | ✅ via „Insight · KI-GENERIERT"-Pattern (§5.6 / Brand Style Guide) |
| **Kein Manipulieren** — KI darf User nicht zu Aktionen drängen | ✅ via Lagom-Regel + Vorschlagsmodell (§5.8 + §1.2 #4) |
| **Foundation-Model-Pflichten** | ❌ trifft Anthropic, nicht minsaga |
| **Logging von KI-Entscheidungen** | ✅ existiert (`ai_analysis_log`, siehe §6.5) |

### 11.5 Apple App Store Compliance

Apple lehnt Apps ab, die nur Paywall sind. Pflicht:

- **Free-Tier substantiell**: minsaga's Free hat algorithmische Funktionen + 1× Onboarding-Sample → **erfüllt**, sofern Apple das so wertet
- **Cancel-Subscription-Link** in der App sichtbar (in Settings)
- **Restore-Purchases-Button** für Re-Login auf neuem Device
- **Subscription-Disclosure** im Pricing-Screen: Auto-Renewal-Klausel, Pricing, Cancel-Hinweis
- **Family-Sharing** als Option im StoreKit (User entscheidet, ob er teilen will)

### 11.6 Haftungs-Disclaimer für KI-Trainingspläne

In Onboarding + bei Plan-Generierung sichtbar:

> *„minsaga ist Lauf-Begleiter und Coach-Werkzeug. Die KI-generierten Pläne und Empfehlungen ersetzen nicht die Beratung durch einen ausgebildeten Trainer oder Sportarzt. Bei Beschwerden, Verletzungen oder gesundheitlichen Bedenken konsultiere bitte einen Arzt."*

**Berufshaftpflicht-Versicherung** prüfen (Schutz gegen Schadensersatz-Klagen).

### 11.7 Operative Compliance-To-Dos vor Markt-Launch

- [ ] Datenschutzerklärung erstellen (Vorlage + Anwalt-Review)
- [ ] AVVs mit allen Anbietern unterschrieben
- [ ] Onboarding-Einwilligung implementiert
- [ ] Datenexport-Funktion implementiert
- [ ] Account-Löschung-Flow implementiert (mit Backup-Bereinigung)
- [ ] „KI-GENERIERT"-Pattern app-weit konsistent
- [ ] Cancel-Subscription-Link prominent
- [ ] Restore-Purchases implementiert
- [ ] Haftungs-Disclaimer in Plan-Generation + Onboarding
- [ ] Berufshaftpflicht-Versicherung abgeschlossen (oder Risiko bewusst akzeptiert)
- [ ] Anwalt-Review der gesamten Compliance vor Launch

---

## Anhang A: Versionshistorie

| Datum | Was geändert | Begründung |
|---|---|---|
| 2026-04-27 | PRD-Skelett angelegt, alte Konzept-Docs nach `archive/` verschoben | Konsolidierung Single Source of Truth |
| 2026-04-28 | §6 Code-Audit · §2.5/2.6 8 User-Journeys · §10 Geschäftsmodell | Interview-Sessions S1–S3, Code-Audit, Journey-Vertiefung, Abomodell-Definition |
| 2026-04-28 | §10.7 MwSt-Korrektur · §10.11 Rechtsform · §11 Compliance | Cost-Realismus-Check + Compliance-Block (DSGVO, EU AI Act, Apple App Store, Haftung) |
