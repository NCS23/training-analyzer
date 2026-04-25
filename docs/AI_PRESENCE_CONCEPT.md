# AI-Präsenz — Konzept

> **Status:** Entwurf v1
> **Letzte Aktualisierung:** 2026-04-25
> **Verwandt:** [BRAND_STYLE_GUIDE.md](BRAND_STYLE_GUIDE.md) · [REDESIGN_KONZEPT.md](REDESIGN_KONZEPT.md)
> **Mockups:** [docs/mockups/ai-presence-symbol.html](mockups/ai-presence-symbol.html) (Iteration v1: Polarstern · [PR #749](https://github.com/NCS23/training-analyzer/pull/749))

---

## Kontext

Der AI Coach in minsaga ist heute auf Alerts mit Robo-Icon beschränkt. Das Konzept
beschreibt die emotionale Erweiterung zu einer **durchgehenden KI-Präsenz**, die
den Nutzer onboarded und durch die App begleitet — unter Einhaltung der Marken-DNA
(*„Coach, nicht Werkzeug"*, *„nüchtern bei Daten, warm bei Kontext"*, Tidlöshet,
Hygge, Lagom).

Die folgenden vier Grundsatzentscheidungen sind aus der Konzept-Diskussion
hervorgegangen und bilden die Basis für jede weitere Designentscheidung
(Komponenten, Animationen, Tonalität, Vollbild-Auftritte).

---

## 1. Eine Präsenz, drei Stimmen

Die KI-Präsenz spricht **immer als dieselbe Instanz**, aber in **drei Tonalitäten**,
die durch den Anlass bestimmt sind — nicht zufällig.

| Stimme | Rolle | Auslöser |
|---|---|---|
| **Begleiter** *(Grundton)* | geht den Weg mit, fragend, warm | Tagesbegrüßung, Reflexion, Empty States, weiche Momente, schwache Läufe |
| **Coach** | klar, handlungsleitend, diagnostisch | konkrete Trainingsempfehlung, Warnung (Verletzungsrisiko, Übertraining), Plan-Anpassung, Onboarding-Schritte |
| **Zeuge** | beobachtend, würdigend, still | Level-Up, Meilenstein, Saga-Rückblick |

### Übersetzung in die Markensprache

Die drei Stimmen entsprechen exakt den **vier visuellen Haltungen** aus dem
Brand Style Guide (Section 3):

- **Begleiter** → *„Warm & still"* (Alltag der App)
- **Coach** → *„Nordlicht-Energie"* (Aktion, Vorwärtsbewegung)
- **Zeuge** → *„Feier"* (still, warm, verdient — Level-Up-Moment)

### Das Muster — wann wechselt die Stimme?

Die Stimme wechselt **an Kanten**:

- **Wenn etwas zu tun ist** → Coach
- **Wenn etwas zu fühlen ist** → Begleiter
- **Wenn etwas zu würdigen ist** → Zeuge

### Beispiele

**Begleiter — schwacher Lauf:**

> „Manche Läufe sind einfach zäh. Das hat heute nichts gekostet.
> Schlaf, Wetter, Kopf — irgendwas davon. Morgen ist ein neuer Tag."

**Coach — schwacher Goal-Readiness-Wert:**

> „Deine Tempoläufe ziehen den Wert nach unten.
> Bis zum Rennen brauchst du 2–3 Einheiten nahe Zielpace. Der Rest ist da.
> Soll ich dir eine für diese Woche vorschlagen?"

**Coach — Verletzungswarnung (ACWR > 1.5):**

> „Deine Belastung ist diese Woche stark gestiegen.
> Das ist der Bereich, in dem Verletzungen passieren — nicht wenn du müde bist, sondern jetzt.
> Plan für morgen: locker oder Ruhetag."

**Zeuge — Level-Up auf „In voller Stärke":**

> „In voller Stärke.
>
> Es hat dich 11 Wochen und 47 Einheiten gekostet."

---

## 2. Symbol statt Eigenname

Die KI-Präsenz hat **keinen Eigennamen**. Sie ist eine namenlose Präsenz mit einem
visuell wiedererkennbaren Symbol.

### Begründung

| Argument | Folge |
|---|---|
| **Markenkonflikt mit „minsaga"** | Eine Figur namens „Saga" konkurriert mit dem Markennamen — *Setz dir ein Ziel* vs. *Saga setzt dir ein Ziel* wäre verwirrend. Das Subjekt der Saga ist der Nutzer (`min`), nicht die App-Figur. |
| **Drei-Stimmen-Modell** | Eine Person mit drei Stimmen wirkt unaufrichtig oder gespalten. Eine namenlose Präsenz mit drei Stimmen wirkt natürlich. |
| **Tidlöshet (5. Säule)** | Eigennamen altern. Eine namenlose Form-Präsenz altert nicht. |
| **Funktionaler KI-Chat** | Die geplanten Use Cases sind fachlich (Trainingswissen, Plan-Anpassung, Literatur-Erklärung). Bei Sachgesprächen baut sich Bindung über Antwortqualität auf, nicht über Persönlichkeit. Ein benanntes Maskottchen, das Sportwissenschaft erklärt, untergräbt Autorität. |
| **Internationalisierung** | Namen tragen kulturelle Last. Ein Symbol skaliert sprach- und kulturunabhängig. |

### Konsequenz

- Die App stellt sich nicht vor („Hi, ich bin …"). Die Präsenz ist einfach da.
- Der Nutzer darf der Präsenz im Kopf einen privaten Namen geben — die App tut es nicht.
- Im Chat sitzt das Symbol als Avatar neben jeder Antwort. Kein Absender-Label nötig.

---

## 3. Strukturell verankert, anlassbezogen sprechend

Die KI-Präsenz hat einen **festen Wohnsitz in der App** (den FAB), aber sie spricht
**nur anlassbezogen** — kein Dauerkommentar.

### Verhalten pro Ort

| Ort | Sichtbarkeit | Dominante Stimme |
|---|---|---|
| **Heute-Dashboard** | AI-Coach-Subline (eine Zeile, Fuchsia-Akzent), erscheint immer | Begleiter, Coach bei Warnung |
| **FAB** | permanent als Symbol | — *(wartet)* |
| **Chat (FAB geöffnet)** | Avatar neben jeder Antwort | Coach-dominant |
| **Fortschritt / Insights** | Insight-Cards (1–2 sichtbar, rotierend) | Coach |
| **Level-Up / Meilenstein** | Vollbild-Moment, Symbol expandiert | Zeuge |
| **Empty States** | Symbol + Text, narrativ | Begleiter |
| **Sonstige Screens** | schweigt, FAB bleibt sichtbar | — |

### Übergänge — eine Präsenz, nicht drei Auftritte

Damit drei Stimmen nicht wie drei verschiedene Wesen wirken, gibt es zwei
Kontinuitätsschichten:

**Visuell — Atem-Wechsel:** Das Symbol hat einen Ruhe-Atem. Wenn etwas Neues
wartet (Insight, Warnung, Coach-Subline), beschleunigt sich der Atem dezent.
Wenn der Nutzer es liest, kehrt es zur Ruhe zurück.

**Sprachlich — Erinnerungs-Schicht:** Die AI-Coach-Subline ist nicht stateless —
sie referenziert die letzten 1–3 Tage explizit, wo es Sinn macht.

> „Gestern hast du geliefert. Heute schaust du, wo du stehst."

### Lagom-Regel

- **Symbol pulsiert nur bei neuer Information** (max. 1–2× pro Tag), sonst völlig ruhig.
- `motion-reduce:transition-none` wird respektiert (Style Guide §12).
- Bei **Vollbild-Feier-Momenten** (Level-Up) verschwindet alles andere — auch der FAB.
  Der Moment gehört nicht der Präsenz als Werkzeug, sondern als Zeuge.

---

## 4. Form — stilisiertes Marken-Symbol in Fuchsia-Familie

> **Stand:** Iteration v2 (Rabe). Iteration v1 (Polarstern, [PR #749](https://github.com/NCS23/training-analyzer/pull/749)) ist verworfen, dokumentiert.

### Entscheidung

Die KI-Präsenz wird durch eine **stilisierte Rabe-Silhouette** dargestellt, in
einem hellen Plum-Ton aus der **Fuchsia-Familie**, auf einer Lavendel-Avatar-Bubble.

### Begründung — gemessen an den fünf Säulen

| Säule | Bewertung | Begründung |
|---|---|---|
| **Funktionalismus** | ✓ | Fuchsia signalisiert AI (Style Guide §5: `accent-4` = AI / Coach). Rabe-Silhouette ist auf 24 px wiedererkennbar. Nichts Dekoratives. |
| **Lagom** | ✓ | Plum (gedämpft, nicht voll-Fuchsia). Bubble ist hell, nicht laut. Zwei Fuchsia-Layer maximal. |
| **Hygge** | ✓ | Warm, einladend. Schwarzer/realistischer Rabe wäre düster — würde Hygge brechen. |
| **Demokratisk** | ⚠ | Kontrast Plum-Rabe auf Lavendel-Bubble muss WCAG-geprüft werden (3:1 für große Icons). |
| **Tidlöshet** | ✓ | Marken-Symbol, kein realistisches Tier. Keine externe Mythologie-Referenz (Hugin/Munin etc.), keine Trend-Anhaftung. |

### Wichtige Einsichten zur Form

**Der Rabe ist kein realistischer Rabe.** Er ist ein stilisiertes
Marken-Symbol in Rabe-Form — analog zum minsaga-Logo, das aus zwei Berg-Symbolen
besteht, nicht aus einem fotorealistischen Berg.

**Die Form bleibt über alle drei Stimmen identisch.** Variation ausschließlich
über Atem-Geschwindigkeit, Halo-Intensität, Gradient-Aktivität — niemals über
die Tier-Farbe selbst. Eine Person mit Stimmungen, nicht drei verschiedene
Charaktere.

### Skalierungs-Anforderungen

| Größe | Verwendung | Anforderung |
|---|---|---|
| 24 px | Chat-Avatar | Silhouette muss noch erkennbar sein — ggf. vereinfachte Mini-Variante (Kopf-Profil oder reduzierte Vollkörper-Silhouette) |
| 40–44 px | Insight-Card-Avatar | Standard, aktuell getestet |
| 120 px | Onboarding-Hero, Insight-Card-Header (Hero-Variante) | Detail-Tiefe sichtbar |
| Vollbild | Level-Up-Moment | Symbol expandiert, Nordlicht-Gradient flutet (nur in diesem Moment, Style Guide §5 erlaubt Gradient-Background nur für Level-Up) |

### Stimmen-Verhalten — visuell

| Stimme | Atem (Pulsieren) | Halo (Fuchsia-Glow) | Gradient-Aktivität |
|---|---|---|---|
| **Begleiter** | langsam, ruhig (3–4 s Zyklus) | weich, schmal | ruhend, kaum bewegt |
| **Coach** | wacher, präziser (1.5–2 s) | etwas stärker, klarer Rand | leicht in Bewegung |
| **Zeuge** | kein Atem — Stillstand | großer, weiter Halo | Nordlicht-Gradient flutet langsam (nur in diesem Moment) |

### Explizite KI-Markierung im Label

Das Symbol (Rabe in Fuchsia-Familie) ist die **Marken-Codierung** für KI. Bis diese
Konvention im Nutzer-Bewusstsein etabliert ist, trägt das Card-Header-Label
zusätzlich eine **explizite Klassifikation**.

#### Begründung

| Argument | Folge |
|---|---|
| **Mental Model in der Lernphase** | Beim ersten Kontakt erkennt ein Nutzer die Konvention „Fuchsia + Rabe = KI" noch nicht. Eine explizite Markierung verankert die Bedeutung. |
| **Style Guide §5** | *„Fuchsia signalisiert sofort: KI-generierter Inhalt."* — eine Markenfarbe allein trägt diese Last nur für geschulte Augen. |
| **EU AI Act / Compliance** | Transparenz ist Pflicht: Nutzer haben das Recht zu wissen, wann KI im Spiel ist. Eine Markenfarbe allein reicht juristisch nicht. |

#### Card-Header-Struktur

Zwei-teiliges Label mit `·` als Trenner:

```
Insight · KI-GENERIERT
```

| Teil | Stil | Rolle |
|---|---|---|
| **Hauptwort** *(z.B. „Insight")* | DM Sans, Sentence-case, Fuchsia | das *Was* — Funktion der Card |
| `·` | DM Sans, Slate (muted) | Trenner |
| **Klassifikation** *(z.B. „KI-GENERIERT")* | DM Sans, **all-caps**, semibold, `tracking-wider`, `text-muted` (Slate) | das *Woher* — Quelle / KI-Marker |

Die `uppercase tracking-wider text-muted`-Form folgt dem **App-weiten Eyebrow-Pattern**
(belegt in `Dashboard.tsx`, `TrainingPlanReadView.tsx`, `DayCard.tsx`,
`SessionMetricsGrid.tsx`, `WeatherCorrelationCard.tsx`, `AppLayout.tsx`).
Sentence-case wäre ein Bruch.

#### Erweiterbarkeit

Das Klassifikations-Slot ist nicht auf „KI-GENERIERT" beschränkt. Anlassbezogen:

| Anlass | Klassifikation |
|---|---|
| Generischer Coach-Tipp / Tagesinsight | `KI-GENERIERT` |
| Konkrete Plan-Empfehlung | `KI-EMPFEHLUNG` |
| Verletzungsrisiko / Warnung | `KI-WARNUNG` |
| Reflexions-Frage / Begleiter-Modus | `KI-IMPULS` *(Vorschlag, zu validieren)* |

Die `KI-`-Vorsilbe bleibt konstant — sie ist der wiedererkennbare Marker, nicht das
Wort danach.

#### Schreibweise

- **Bindestrich** ist Pflicht (`KI-GENERIERT`, nicht `KI GENERIERT`) — zusammengesetztes
  Adjektiv im deutschen Sprachgebrauch (analog zu „CO2-neutral", „handgemacht").
- **All-caps**, weil Klassifikation, nicht Aussage.
- **Deutsch**, weil App-Sprache deutsch (Style Guide §10).

---

## Verworfene Ansätze

| Konzept | Grund für Verwurf |
|---|---|
| **Eigenname** (Saga, Min, Nord, Lumen / Lys) | Markenkonflikt mit „minsaga". Drei-Stimmen-Modell wird mit benannter Person fragil. Tidlöshet-Risiko. Keiner der Namen überzeugt vollständig — Indikator gegen die ganze Richtung. |
| **Polarstern** *(Iteration v1, [PR #749](https://github.com/NCS23/training-analyzer/pull/749))* | Visuell zu generisch („AI-stock-Sparkle"). Trug emotional zu wenig — wirkte wie Logo, nicht wie Präsenz. Lieferte den Anstoß zur figürlichen Lösung. |
| **Punkt mit Glow / atmender Kreis** | Zu generisch ohne Kontext (Notification-Dot-Konnotation). Zu nah an Siri-Glow. |
| **Polarfuchs** | Niedlichkeit-Risiko. Bei einer Sub-2h-Performance-App untergräbt ein süßes Tier die Coach-Autorität. |
| **Schwarzer / dunkler Rabe** | Bricht die Fuchsia-Regel (Style Guide §5: AI = Fuchsia). Hugin/Munin-Mythologie ist eine externe Referenz, die im Brand-Universum nicht vorkommt. Düstere Konnotation widerspricht Hygge. |
| **Tier-Farbe pro Stimme variieren** | Bricht „Eine Form, drei Stimmen" — Variation darf nur in Atem/Halo/Gradient liegen, nicht in der Form selbst. Drei Farben = drei Wesen. |
| **Allgegenwärtig sprechend** (Modell 3 in Iteration) | Killt Lagom. Verstößt gegen *„nüchtern bei Daten"*. Wird gemutet oder die App gewechselt. |
| **Card-Header `Insight` allein** (ohne KI-Markierung) | Trägt die KI-Identität nur über Fuchsia + Rabe — funktioniert erst nach Etablierung der Konvention, nicht beim ersten Kontakt. Compliance-Lücke (EU AI Act). |
| **Card-Header `AI Coach · INSIGHT`** | „AI Coach" als Eigenname-Etikett widerspricht Punkt 2 (Symbol statt Eigenname). Drei Fuchsia-Layer auf einer Card (Bubble + Rabe + Label) sind zu laut. |
| **Card-Header `KI · INSIGHT`** *(KI größer + Fuchsia, INSIGHT kleiner + Slate)* | „KI" dominiert visuell, „Insight" wird zur Untertitel-Klassifikation — Hierarchie ist umgekehrt zur Funktion. Wirkt wie Tech-Schlagzeile, nicht wie ruhige Meta-Zeile. |
| **Card-Header `Insight · KI generiert`** *(sentence-case, ohne Bindestrich)* | Bricht das App-weite Eyebrow-Pattern (`uppercase tracking-wider`). „KI generiert" ohne Bindestrich liest sich auf den ersten Blick als Verb, nicht als Klassifikation. |

---

## Offene Punkte

- [ ] **Token-Bindung** — konkreter Plum-Ton aus L3/L4-Tokens, ggf. dediziertes AI-Token in [MINSAGA_TOKENS.md](MINSAGA_TOKENS.md) ergänzen
- [ ] **Kontrast-Prüfung** — Plum-Rabe auf Lavendel-Bubble (WCAG 3:1 für große Icons)
- [ ] **24 px-Variante** — vereinfachte Mini-Silhouette für Chat-Avatar
- [ ] **Vollbild-Auftritt (Zeuge)** — Symbol-Expansion, Nordlicht-Flut, Fraunces-Überschrift
- [ ] **Stimmen-Varianten visualisieren** — Begleiter / Coach / Zeuge nebeneinander, nur über Atem/Halo/Gradient unterschieden
- [ ] **Animation spezifizieren** — Atem-Zyklen, Übergänge, `motion-reduce`-Verhalten
- [ ] **Tonalitäts-Library** — Beispiel-Texte pro Stimme und Anlass (gehört eher in Style Guide §10 oder eigenes Dokument)
- [ ] **Nordlig DS Komponente** — `AIPresence` oder Erweiterung von `Card`-Variante mit AI-Avatar-Slot

---

## Referenzen

- [BRAND_STYLE_GUIDE.md](BRAND_STYLE_GUIDE.md) §3 (Designprinzipien), §5 (Farbsystem, Fuchsia für AI), §10 (Tonalität & AI Coach), §12 (Animationen)
- [REDESIGN_KONZEPT.md](REDESIGN_KONZEPT.md) — UX-Konzept & FAB-Verankerung
- [MINSAGA_TOKENS.md](MINSAGA_TOKENS.md) — Token-Architektur
- [PR #749](https://github.com/NCS23/training-analyzer/pull/749) — Iteration v1 (Polarstern, verworfen)
- [docs/mockups/ai-presence-symbol.html](mockups/ai-presence-symbol.html) — HTML-Skizze v1
