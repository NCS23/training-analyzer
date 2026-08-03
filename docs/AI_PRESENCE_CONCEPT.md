# AI-Präsenz — Konzept

> **Status:** Entwurf v2
> **Letzte Aktualisierung:** 2026-07-30
> **Verwandt:** [BRAND_STYLE_GUIDE.md](design/BRAND_STYLE_GUIDE.md) · [PRD](PRD.md) §1.3
> **Design-Referenz (verbindlich):** Claude-Design-Projekt „Minsaga Design System" — `preview/comp-ai-presence.html` (Zeichen + Größen), `comp-ai-presence-stimmen.html` (drei Stimmen), `comp-ai-presence-kontexte.html` (Insight-Card / Chat / FAB) · Handoff-Paket `minsaga/.import/design_handoff_saga_ai_presence/` (SVG-Geometrie, Transforms, Animationswerte)
> **Historische Mockups:** [mockups/ai-presence-symbol.html](mockups/ai-presence-symbol.html) (Symbol-Iteration v1: Polarstern · [PR #749](https://github.com/NCS23/training-analyzer/pull/749))

---

## Kontext

Der Coach in minsaga war ursprünglich auf Alerts mit Robo-Icon beschränkt. Das Konzept
beschreibt die emotionale Erweiterung zu einer **durchgehenden KI-Präsenz**, die
den Nutzer onboarded und durch die App begleitet — unter Einhaltung der Marken-DNA
(*„Coach, nicht Werkzeug"*, *„nüchtern bei Daten, warm bei Kontext"*, Tidlöshet,
Hygge, Lagom).

Die folgenden vier Grundsatzentscheidungen sind aus der Konzept-Diskussion
hervorgegangen und bilden die Basis für jede weitere Designentscheidung
(Komponenten, Animationen, Tonalität, Vollbild-Auftritte).

> **v2 (2026-07-30):** Symbol-Iteration v4 („Präsenz-Zeichen") ersetzt den Raben (v2)
> und die Korona (v3) — siehe §4 und „Verworfene Ansätze". Namenlosigkeit bestätigt (§2).
> Feier-Trigger ohne Level-System definiert (§1, §3) — Levels sind verworfen (PRD §7 · #757).

---

## 1. Eine Präsenz, drei Stimmen

Die KI-Präsenz spricht **immer als dieselbe Instanz**, aber in **drei Tonalitäten**,
die durch den Anlass bestimmt sind — nicht zufällig.

| Stimme | Rolle | Auslöser |
|---|---|---|
| **Begleiter** *(Grundton)* | geht den Weg mit, fragend, warm | Tagesbegrüßung, Reflexion, Empty States, weiche Momente, schwache Läufe |
| **Coach** | klar, handlungsleitend, diagnostisch | konkrete Trainingsempfehlung, Warnung (Verletzungsrisiko, Übertraining), Plan-Anpassung, Onboarding-Schritte |
| **Zeuge** | beobachtend, würdigend, still | Bestleistung, Race-Finish, Comeback, Saga-Rückblick |

### Übersetzung in die Markensprache

Die drei Stimmen entsprechen exakt den **vier visuellen Haltungen** aus dem
Brand Style Guide (Section 3):

- **Begleiter** → *„Warm & still"* (Alltag der App)
- **Coach** → *„Nordlicht-Energie"* (Aktion, Vorwärtsbewegung)
- **Zeuge** → *„Feier"* (still, warm, verdient — Feier-Moment)

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

**Zeuge — Bestleistung (Halbmarathon):**

> „Dein Kapitel ist geschrieben.
>
> 1:58:41. Es hat dich 11 Wochen und 47 Einheiten gekostet."

---

## 2. Symbol statt Eigenname

Die KI-Präsenz hat **keinen Eigennamen**. Sie ist eine namenlose Präsenz mit einem
visuell wiedererkennbaren Symbol.

> **Bestätigt 2026-07-30:** Ein Design-Zwischenstand (Handoff-Paket) nannte den Coach
> „Saga". Die Entscheidung wurde erneut geprüft und bleibt bestehen: **kein Eigenname.**
> „Saga" ist Marken- und Story-Wortmaterial (PRD §9.5), nicht der Name des Coaches.
> Der technische Bezeichner `SagaMark` (Komponente) ist davon unberührt.

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
- **KI-Kennzeichnung:** Wo KI-Inhalte gelabelt werden (Insight-Cards), gilt einheitlich
  **„Insight · KI-GENERIERT"** (EU-AI-Act-Transparenz, PRD §11.4) — nie ein Name.

---

## 3. Strukturell verankert, anlassbezogen sprechend

Die KI-Präsenz hat einen **festen Wohnsitz in der App** (den FAB), aber sie spricht
**nur anlassbezogen** — kein Dauerkommentar.

### Verhalten pro Ort

| Ort | Sichtbarkeit | Dominante Stimme |
|---|---|---|
| **Heute-Dashboard** | Coach-Insight (erstes Element, Fuchsia-Akzent) | Begleiter, Coach bei Warnung |
| **FAB** | permanent als Symbol | — *(wartet)* |
| **Chat (FAB geöffnet)** | Avatar neben jeder Antwort | Coach-dominant |
| **Analyse / Insights** | Insight-Cards (1–2 sichtbar, rotierend) | Coach |
| **Feier-Moment (Bestleistung · Race-Finish · Comeback)** | Vollbild-Moment, Symbol expandiert | Zeuge |
| **Empty States** | Symbol + Text, narrativ | Begleiter |
| **Sonstige Screens** | schweigt, FAB bleibt sichtbar | — |

### Übergänge — eine Präsenz, nicht drei Auftritte

Damit drei Stimmen nicht wie drei verschiedene Wesen wirken, gibt es zwei
Kontinuitätsschichten:

**Visuell — ruhige Dauerpräsenz:** Das Zeichen ist im Ruhezustand still (Begleiter:
kein Schein). Wenn etwas Neues wartet (Insight, Warnung, Coach-Subline), wird der
Schein wacher. Wenn der Nutzer es liest, kehrt Ruhe ein.

**Sprachlich — Erinnerungs-Schicht:** Die Coach-Subline ist nicht stateless —
sie referenziert die letzten 1–3 Tage explizit, wo es Sinn macht.

> „Gestern hast du geliefert. Heute schaust du, wo du stehst."

### Lagom-Regel

- **Schein-Aktivität nur bei neuer Information** (max. 1–2× pro Tag), sonst völlig ruhig.
- `prefers-reduced-motion` wird respektiert (Style Guide §12) — und weil jeder
  Stimm-Unterschied **im Standbild lesbar** sein muss (§4), geht dabei keine Bedeutung verloren.
- Bei **Vollbild-Feier-Momenten** (Bestleistung, Race-Finish, Comeback) verschwindet alles
  andere — auch der FAB. Der Moment gehört nicht der Präsenz als Werkzeug, sondern als Zeuge.

---

## 4. Form — das Präsenz-Zeichen

> **Stand:** Symbol-Iteration v4 (2026-07-30). Iterationen v1 (Polarstern), v2 (Rabe)
> und v3 (Korona) sind verworfen und unten dokumentiert.

### Entscheidung

Die KI-Präsenz wird durch die **Bildmarke dargestellt, ausgespart aus einer
Aurora-Scheibe** — die Marke selbst bekommt ein Gesicht. Kein Funke, kein Bot-Icon,
kein Tier, kein Buchstabe.

**Aufbau (zwei Ebenen, immer in dieser Reihenfolge):**

1. **Aurora-Scheibe** — geschlossene Kontur mit drei sanften Wellen
   (`r(θ) = 45 + 3.2 · sin(3θ − π/2)`, Catmull-Rom-geglättet). Trägt den Farbverlauf
   `fuchsia-500 → coach-accent` (#d946ef → #a21caf).
2. **Bildmarke** (M/S-Berge, Quelle `assets/bildmarke-mono.svg`) — als **Negativform**
   aus der Scheibe gestanzt, zeigt den Hintergrund durch.

Der exakte SVG-Pfad, die Transforms und der verpflichtende Paint-Fallback
(`fill="url(#…) #c026d3"`) sind im Claude-Design-Projekt und im Handoff-Paket
verbindlich hinterlegt — **nicht nachzeichnen, 1:1 übernehmen.**

### Begründung — gemessen an den fünf Säulen

| Säule | Bewertung | Begründung |
|---|---|---|
| **Funktionalismus** | ✓ | Markeneigen statt Branchenstandard. Kleinstufen-Regel ist gemessen (0,79-px-Steg), nicht geschätzt. |
| **Lagom** | ✓ | Ein Zeichen, zwei Farbebenen, kein Trägerkreis. Lavendel-Bubbles sind zurückgezogen — sie doppelten die Form. |
| **Hygge** | ✓ | Weiche Aurora-Kontur, warmer Plum-Verlauf. Kein Tier, keine Niedlichkeit, keine Düsternis. |
| **Demokratisk** | ⚠ | Kontrast auf Weiß/stone-50 wirkt tragfähig, finale WCAG-Messung (3:1 für große Icons) steht aus. |
| **Tidlöshet** | ✓ | Die Bildmarke ist das langlebigste Asset der Marke. Keine externe Referenz, keine Trend-Anhaftung. |

### Abgrenzung zum Logo — zentrale Regel

| Zeichen | Behandlung | Bedeutung |
|---|---|---|
| Wortbildmarke, Nordlicht-Gradient | Header, Splash | „Die Marke ist da" |
| Bildmarke, Fuchsia + Aussparung | Coach-Avatar, FAB, Insight-Card | „Der Coach spricht" |

Dieselbe Grundform, zwei Behandlungen. **Nie vertauschen.**

### Skalierung — genau eine Grenze bei 32 px

| Rendergröße | Behandlung | Verwendung |
|---|---|---|
| **> 32 px** | Scheibe trägt die Farbe, Marke ist die Aussparung | Hero (120), FAB (56), Coach-Avatar in Cards (40–44) |
| **≤ 32 px** | Marke trägt die Farbe selbst, **keine Scheibe** | Chat-Zeile (32), Inline-Hinweis, Run-Overlay (28) |

Grund: Bei 24 px hätte der schmalste Steg der Marke als Aussparung nur 0,79 px und
würde zulaufen. Die Schwelle sitzt **in der Komponente** (`SagaMark`, `size <= 32`),
nicht an der Aufrufstelle.

### Stimmen-Verhalten — visuell

**Die Form bleibt über alle drei Stimmen identisch** — sie ist Markenasset, kein
Zustandsanzeiger. Unterschieden wird ausschließlich über Verlauf und Schein:

| Stimme | Verlauf | Schein (Glow-Ebenen) |
|---|---|---|
| **Begleiter** | flacher Kontrast (`fuchsia-500 → 600`), steiler Winkel | keiner |
| **Coach** | tiefer Kontrast (`fuchsia-500 → coach-accent` @65 %), flacher Winkel | eng, zwei Ebenen |
| **Zeuge** | Nordlicht-Gradient (sky → fuchsia → indigo) | weit, zwei Ebenen |

**Regel:** Jeder Unterschied zwischen Stimmen muss **im Standbild** lesbar sein.
Eine Unterscheidung, die nur im Animationstempo existiert, verschwindet bei
`prefers-reduced-motion`. Der Verlauf rotiert *innerhalb* der stehenden Form
(Begleiter 26 s · Coach 9 s · Zeuge 18 s) — Licht wandert über einen festen Himmel;
die Rotation ist Verstärkung, nicht Bedeutungsträger.

Beim Zeuge-Vollbild (Feier-Moment) flutet der Nordlicht-Gradient den Screen,
dann große Fraunces-Überschrift mit Stat-Zusammenfassung. Still, warm, verdient.

---

## Verworfene Ansätze

| Konzept | Grund für Verwurf |
|---|---|
| **Eigenname** (Saga, Min, Nord, Lumen / Lys) | Markenkonflikt mit „minsaga". Drei-Stimmen-Modell wird mit benannter Person fragil. Tidlöshet-Risiko. Keiner der Namen überzeugt vollständig — Indikator gegen die ganze Richtung. **Bestätigt 2026-07-30** (siehe §2). |
| **Polarstern** *(Symbol v1, [PR #749](https://github.com/NCS23/training-analyzer/pull/749))* | Visuell zu generisch („AI-stock-Sparkle"). Trug emotional zu wenig — wirkte wie Logo, nicht wie Präsenz. Lieferte den Anstoß zur figürlichen Lösung. |
| **Punkt mit Glow / atmender Kreis** | Zu generisch ohne Kontext (Notification-Dot-Konnotation). Zu nah an Siri-Glow. |
| **Polarfuchs** | Niedlichkeit-Risiko. Bei einer Sub-2h-Performance-App untergräbt ein süßes Tier die Coach-Autorität. |
| **Rabe** *(Symbol v2, verworfen 2026-07-30)* | Mythologie-Sog: Ein Rabe in nordischem Kontext wird unvermeidlich als Odins Rabe (Hugin/Munin, Fantasy) gelesen — die Distanzierung im Konzept ändert die Lesart der Nutzer nicht. Die naturalistische Umsetzung in Figma verstärkte das Problem. Zudem: jedes Tier ist einen halben Schritt vom Maskottchen entfernt. |
| **Schwarzer / dunkler Rabe** | Bricht die Fuchsia-Regel (Style Guide §5: AI = Fuchsia). Düstere Konnotation widerspricht Hygge. |
| **Korona** *(Symbol v3, 2026-07-30, noch am selben Tag abgelöst)* | Geschlossener, wellenförmiger Aurora-Ring — erfüllte die Anforderungen (geschlossen, icon-tauglich, markennah), blieb aber generisch-abstrakt ohne Markenbezug. Die Weiterentwicklung zur Bildmarken-Aussparung (v4) macht das Zeichen markeneigen. |
| **Lavendel-Bubble als Trägerfläche** | Doppelte die Form — das Zeichen ist selbst eine gefüllte Fläche. Zurückgezogen; einzige Ausnahme ist der FAB auf weißer Scheibe. |
| **Tier-Farbe pro Stimme variieren** | Bricht „Eine Form, drei Stimmen" — Variation darf nur in Verlauf/Schein liegen, nicht in der Form selbst. |
| **Allgegenwärtig sprechend** (Modell 3 in Iteration) | Killt Lagom. Verstößt gegen *„nüchtern bei Daten"*. Wird gemutet oder die App gewechselt. |

---

## Offene Punkte

- [ ] **WCAG-Messung** — Plum-Verlauf auf Weiß / stone-50 formal messen (3:1 für große Icons)
- [ ] **SwiftUI-Port** — `SagaMark`-Referenzimplementierung (React, `ui_kits/app/index.html`) nach SwiftUI portieren, inkl. 32-px-Schwelle in der Komponente und eindeutiger Gradient-/Masken-IDs pro Instanz
- [ ] **Figma-Abgleich** — sobald Figma-Zugang besteht: `rabe`-Komponente, `Icons/bot` und `Icons/sparkles` auf der Foundations-Seite durch das Präsenz-Zeichen ersetzen
- [ ] **Vollbild-Auftritt (Zeuge)** — Übergang FAB → Vollbild-Expansion spezifizieren (Design der Ziel-Szene existiert: `preview/comp-feier-moment.html`)
- [ ] **Tonalitäts-Library** — Beispiel-Texte pro Stimme und Anlass (gehört eher in Style Guide §10 oder eigenes Dokument)

Erledigt seit v1: Form final (v4) · Stimmen-Varianten visualisiert (`comp-ai-presence-stimmen.html`) · Kleinstufen-Variante definiert (32-px-Regel, ersetzt die offene 24-px-Frage) · Animation spezifiziert (Verlaufsrotation + Schein-Puls + `prefers-reduced-motion`-Verhalten im Handoff) · Trägerflächen-Frage entschieden (keine Bubble).

---

## Referenzen

- [BRAND_STYLE_GUIDE.md](design/BRAND_STYLE_GUIDE.md) §3 (Designprinzipien), §5 (Farbsystem, Fuchsia für AI), §10 (Tonalität & Coach), §12 (Animationen)
- [PRD](PRD.md) §1.3 (Leitprinzipien) · §5.3 (Coach) · §5.6 (Voice & Copy) · §9.5 (Marken-Wortmaterial) · §11.4 (EU AI Act)
- Claude-Design-Projekt „Minsaga Design System" — `preview/comp-ai-presence*.html`, `preview/comp-feier-moment.html`, `uploads/BRAND_STYLE_GUIDE.md` („Das Präsenz-Zeichen")
- Handoff-Paket `minsaga/.import/design_handoff_saga_ai_presence/` — verbindliche SVG-Geometrie, Transforms, Animationswerte *(Hinweis: Paket entstand vor der Namens-Entscheidung und nennt den Coach noch „Saga" — §2 gilt)*
- [PR #749](https://github.com/NCS23/training-analyzer/pull/749) — Symbol-Iteration v1 (Polarstern, verworfen)
- [docs/mockups/ai-presence-symbol.html](mockups/ai-presence-symbol.html) — HTML-Skizze v1
