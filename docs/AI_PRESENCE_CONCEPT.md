# KI-Begleitperson — Konzept & Erarbeitung

Dieses Dokument fasst den aktuellen Stand der Konzeptarbeit zur KI-Präsenz in minsaga zusammen.
Es ist ein lebendes Dokument — offene Entscheidungen sind als solche markiert.

---

## 1. Ausgangssituation

**Ist-Zustand:** KI beschränkt auf Alert-Meldungen mit einem generischen Roboter-Icon.
Technisch funktioniert es. Emotional ist es nichts.

**Vision:** Ein Wesen, das Nutzende durch die App begleitet — nicht als Assistenz-Tool,
sondern als Trainingsbegleitung, die den Kontext kennt, Fortschritte würdigt,
und im richtigen Moment das Richtige sagt.

Die Fuchsia-Farbe (`#d946ef`) ist im Design System bereits exklusiv für KI/Coach reserviert.
Das ist die Grundlage.

---

## 2. Drei-Stimmen-Modell

Die KI spricht nicht immer gleich. Je nach Kontext übernimmt eine andere Stimme.

### Begleiter — die Grundhaltung

Ruhig, präsent, nicht aufdringlich. Kennt den Kontext ohne ihn ständig zu erwähnen.

> "Du hast die letzten 3 Wochen konsequent trainiert — das ist keine Selbstverständlichkeit."

> "Heute läuft nicht alles. Das ist auch Training."

> "HM in 6 Wochen. Du weißt, was du kannst."

### Coach — wenn Aktion gefragt ist

Direkt, klar, orientiert an dem, was jetzt hilft.

> "Nach 4 Tagen Belastung braucht dein Körper morgen Ruhe. Wirklich."

> "Dein HF-Wert heute liegt 8 bpm über dem Schnitt. Geh heute raus, aber locker."

> "Diese Einheit wäre zu viel gewesen. Gut, dass du abgebrochen hast."

### Zeuge — wenn etwas gewürdigt werden soll

Beobachtend, nicht bewertend. Hält inne, wenn ein Moment es verdient.

> "Das war dein erster Lauf nach der Verletzung. Du bist wieder hier."

> "Sub-2h ist noch 14 Wochen hin. Du hast bereits 340 km in diesem Trainingsblock."

> "Dieser Lauf war kein PR. Aber er war genau das, was du heute gebraucht hast."

---

## 3. Präsenz-Modell

**Entschieden: Modell 4 — FAB als Zuhause, anlassbezogene Sprache**

| Aspekt | Entscheidung |
|---|---|
| Permanente Sichtbarkeit | Das Symbol ist immer sichtbar — als FAB |
| Spricht von sich aus | Ja, aber nur bei echten Anlässen |
| Anlässe | Workout abgeschlossen, Milestone, Erholungswarnung, Wochen-Abschluss |
| Initiative des Nutzers | Jederzeit über FAB → Chat |
| Was der Chat kann | Training erklären, Plan anpassen, Literatur, Zielfragen |

**Was die KI nicht tut:**
- Täglich melden ohne Anlass
- Gamification-Push ("Du hast heute noch keinen Run!")
- Generische Motivationsfloskeln
- Sich selbst erklären oder vorstellen

---

## 4. Symbol-Strategie

**Entschieden: Option C — Symbol ohne Namen**

| Option | Beschreibung | Entscheidung |
|---|---|---|
| A — Name + Symbol | "Sigrid", "Lykke" mit eigenem Avatar | Verworfen — zu viel Charakter-Aufbau |
| B — Nur Name | Textbasiert, kein Symbol | Verworfen — braucht visuellen Anker |
| C — Symbol ohne Namen | Erkennbares Symbol, kein Eigenname | **Gewählt** |

Das Symbol braucht:
- Nordischen Bezug (Mythologie, Natur, Geografie)
- Fuchsia als einzige Farbe (kein Gradient im Symbol selbst)
- Lucide-kompatiblen Strich-Stil (1.5–2px, runde Enden)
- Erkennbarkeit bei 24px und kleiner

---

## 5. Icon-Erkundung — Verlauf

### v1 — Asymmetrischer 4-Punkt-Stern

Nordlicht-Gradient innen, Fuchsia-Halo außen. Drei Animationszustände.

**Ergebnis:** Abgelehnt. Zu viele Farben, Gradient unschön, Glow passt nicht zur Form.

### v2 — Organische Füllformen

Linse, Kiesel, Knoten, Komma. Einfarbig Fuchsia.

**Ergebnis:** Abgelehnt. Formen sprechen nicht an. Frage aufgeworfen: Warum Füllung statt Kontur?

### v3 — Aurora-Wellen als Striche

Schleier, Vorhang, Falte, Bogen. Lucide-kompatibel, 1.5px Strich.

**Ergebnis:** Abgelehnt. Qualität der Entwürfe nicht überzeugend.

### Moodboard-Erkundung (Bild-KI)

Fünf nordische Richtungen wurden untersucht:

| Richtung | Beschreibung | Status |
|---|---|---|
| Northlight / Aurora | Wellenförmige Linien, Licht | Zu abstrakt für kleines Icon |
| Kompass / Navigation | Richtung, Orientierung | Zu generisch |
| Rabe | Huginn & Muninn (Odin) | **Aktuelle Richtung** |
| Polarfuchs | Revontulet ("Fuchsfeuer" = Aurora) | Zweite Option |
| Binde-Rune / Rune | Nordische Schriftzeichen | **Verworfen** (politisches Risiko, Lesbarkeit) |
| Polarstern | Orientierungsstern | Zu generisch |
| Eis-Facette | Geometrisch, kristallin | Möglich, noch nicht untersucht |

---

## 6. Aktuelle Richtung: Rabe

### Mythologische Grundlage

Huginn (Gedanke) und Muninn (Erinnerung) — Odins zwei Raben.
Sie fliegen täglich über die Welt und berichten ihm alles.

**Warum das passt:**
- Gedanke + Erinnerung = was ein KI-Coach tun soll
- Odin schickt sie aus, um zu lernen — er konsultiert externe Intelligenz
- Nordische Mythologie, tief verwurzelt, politisch unproblematisch
- Rabe ist ein erkennbares Wesen (kein abstrakte Form nötig)
- Natürliches Tier, kein Fantasy-Konstrukt

### Prompt-Richtung für Bild-KI

Der Prompt für weitere Moodboard-Iteration wurde auf Abstraktion ausgelegt —
die KI soll nicht eine bestimmte Form liefern, sondern 9 echte Variationen zeigen.

**Kernprinzipien:**
- Strichstil, nicht gefüllt
- Einzeln oder als Paar (Huginn & Muninn → zwei Elemente)
- Verschiedene Abstraktionsgrade (von realistisch zu minimal/geometrisch)
- Fuchsia, 24–32px Icon-Format

---

## 7. Technische Rahmenbedingungen

Für die spätere Implementierung:

| Constraint | Vorgabe |
|---|---|
| Farbe | Nur `var(--color-ai-primary)` (→ Fuchsia) |
| Animationen | `prefers-reduced-motion` respektieren |
| Touch-Target FAB | min. 44×44px (lg-Variante Nordlig DS) |
| Stroke-Style | Lucide-kompatibel, `strokeWidth={1.5}`, `strokeLinecap="round"` |
| Viewport | Mobile-First 375px |
| Komponenten | Nordlig DS Button/FAB — kein natives `<button>` |
| Token-Ebene | L3/L4 — keine hardcodierten Farben |

---

## 8. Offene Entscheidungen

- [ ] **Icon-Form final entscheiden** — Rabe weiterverfolgen, Ergebnisse der Bild-KI auswerten
- [ ] **Einzelner Rabe oder Raben-Paar?** — Huginn & Muninn als zwei Elemente vs. einer
- [ ] **Abstraktionsgrad** — Realistischer Vogel vs. minimale Silhouette vs. geometrische Abstraktion
- [ ] **Animation im FAB** — Atemanimation (Pulsieren) oder statisch?
- [ ] **Drei-Stimmen visuell unterscheidbar?** — Oder immer dasselbe Symbol?
- [ ] **GitHub Issue erstellen** — Vor jeder Implementierung (Projekt-Regel 1)
- [ ] **BRAND_STYLE_GUIDE.md erweitern** — KI-Präsenz-Abschnitt hinzufügen sobald Symbol final

---

## 9. Was bleibt

Die KI in minsaga ist kein Assistent.
Sie ist eine Begleitperson — ruhig, nordisch, präzise.
Sie spricht, wenn etwas zu sagen ist. Und sie schweigt, wenn Schweigen das Richtige ist.

Das Symbol ist ihr Gesicht. Es muss ohne Text funktionieren,
bei 24px erkennbar sein, und in Fuchsia strahlen —
weil das ihre Farbe ist und sonst niemandes.
