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
| Race-Tag | 0 | **Vor Race:** Pacing-Strategie geklärt + verfügbar zum Nachschlagen · **Während Race:** Pacing-Strategie auf Mobile/Watch, „Worauf achten"-Hinweise · **Companion-Vision:** Watch-App begleitet aktiv während des Laufs | Plan (Pacing) + Companion-App (Vision) |
| Reflexion | +1 | Auswertung „Wie war es?" + Erkenntnisse fließen in neuen Trainingsplan ein | Analyse + Plan |

#### Race-Day-spezifische Bedürfnisse (Vision)

- **Streckenprofil laden** (GPX/Höhenprofil) — beeinflusst Pacing
- **Versorgungs-Punkte** auf der Strecke (Wasser, Verpflegung) → **Gel-Strategie** ableitbar
- **Pacing-Strategie auf der Watch** während des Laufs (gleichmäßig / negativ / konservativ)
- **Companion-Mode**: Watch-App begleitet aktiv (Splits, Pace-Hinweise, ggf. Begleiter-Stimme)

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

### 6.2 Mapping pro Tab/Bereich

> *[wird im Interview / parallelem Code-Audit befüllt]*

| Bereich | Aktueller Stand | Status | Was zu tun ist | Aufwand |
|---|---|---|---|---|
| **Heute (Dashboard)** | Existiert, mit alten Stats-Cards | 🟡 ADAPT | Cards austauschen (siehe §4.1), AICoachInsight + Goal Readiness Card neu | M |
| **Training-Wochenansicht** | Existiert | 🟡 ADAPT | In Tab „Training" einordnen, Soll/Ist-Vergleich ergänzen | M |
| **Sessions-Liste + Detail** | Existiert | 🟢 KEEP | Nur Routing anpassen | S |
| **Session-Upload (CSV/FIT)** | Existiert | 🟢 KEEP | — | — |
| **Trainingsplan + Phasen** | Existiert | 🟡 ADAPT | Ziel-Felder integrieren (kein separater Ziele-Tab) | M |
| **RaceGoal als Entity** | Existiert | 🔴 REMOVE | Migration: in Plan überführen, Tabelle deprecaten | M |
| **Pacing-Rechner** | Existiert | 🟡 ADAPT | Quelle Plan statt RaceGoal | S |
| **Routen-Bibliothek** | Existiert | 🟡 ADAPT | Sub-Tab unter „Sammlung", vereinfachtes Datenmodell (siehe REDESIGN_KONZEPT.md §6) | L |
| **Übungen-Bibliothek** | Existiert | 🟢 KEEP | — | — |
| **Vorlagen** | tbd | tbd | — | — |
| **Goal Readiness** | Konzept liegt vor | 🔵 NEW | Komplette Implementation: Backend + Frontend Card | L |
| **AI Coach Insight Card (Dashboard)** | Existiert in Figma, Frontend tbd | 🔵 NEW | Komponente + Insight-Engine | M |
| **AI Coach Chat (FAB)** | tbd | 🔵 NEW | Floating UI + Chat-Backend | L |
| **Level-System (Score 0-100, 4 Levels)** | Konzept war geplant, nie implementiert | 🔴 REMOVE | Konzept im Archiv lassen, im Code keine Spuren | — |
| **Stats/Statistiken-Tab** | Existiert | 🔴 REMOVE | Funktion geht in Tab „Analyse" auf | M |
| **Profil als Bottom-Nav-Tab** | Existiert | 🟡 ADAPT | Wird zum Avatar oben rechts | S |
| **KI-Chat als isolierter Menüpunkt** | Existiert evtl. | 🟡 ADAPT | Wird zum FAB, kontextbezogen auf jeder Seite | M |

> Aufwands-Schätzung: S (≤ 1 Tag), M (2–5 Tage), L (1+ Woche). Wird nach Interview verifiziert.

### 6.3 Datenbank-Migrationen (vorläufig)

> *[wird im Code-Audit konkretisiert]*

- `race_goals` → in `training_plans` integrieren (Felder: `race_name`, `race_date`, `race_distance_km`, `target_time_seconds`)
- `level_score`, `level_name` etc. (falls vorhanden) → entfernen
- Sub-Tab-Struktur unter `/sammlung` → URL-Redirects für `/bibliothek/*`

### 6.4 Übersicht: was bleibt vs. was kommt neu

**Großteils bleibt (Backend):**
- CSV-Parser (Apple Watch Format)
- FIT-Import
- Session-Entitäten + API
- Trainingsplan-Generator
- HR-Zonen-Logik
- CTL/ATL/TSB-Berechnung

**Großteils neu (Frontend):**
- Tab-Struktur (Heute / Training / Analyse / Plan / Sammlung)
- Dashboard-Cards (AICoachInsight, Goal Readiness)
- AI Coach Chat-FAB
- Konsolidierte Sub-Navigation in „Sammlung"

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
| 15 | **Wetter-Berücksichtigung in Insights** | offen | — | Wetter (Temperatur, Wind) als Kontext für HR-/Pace-Abweichungen. Erfordert Wetter-API + Korrelation. |

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

## Anhang A: Versionshistorie

| Datum | Was geändert | Begründung |
|---|---|---|
| 2026-04-27 | PRD-Skelett angelegt, alte Konzept-Docs nach `archive/` verschoben | Konsolidierung Single Source of Truth |
