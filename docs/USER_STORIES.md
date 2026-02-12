# 🎯 User Stories & Requirements

**Zweck:** Requirements aus User-Perspektive (Nils-Christian)  
**Format:** User Stories + Akzeptanzkriterien

---

## 🏃‍♂️ Core Use Cases

### UC-1: Training hochladen und analysieren
**Als** Läufer  
**möchte ich** mein Apple Watch Training per CSV hochladen  
**damit** ich sofort Analyse, HF-Zonen und Lap-Details sehe

**Akzeptanzkriterien:**
- [ ] CSV-Upload via Drag & Drop oder File-Browser
- [ ] Parsing läuft in <1 Sekunde
- [ ] Metriken werden sofort angezeigt (Pace, HR, Distance, Duration)
- [ ] Laps werden automatisch klassifiziert
- [ ] HF-Zonen werden berechnet (Gesamt + Arbeits-Laps)
- [ ] Fehlermeldungen sind klar verständlich

**Priorität:** 🔴 CRITICAL (MVP)

---

### UC-2: Lap-Klassifizierung überprüfen und anpassen
**Als** Läufer  
**möchte ich** die automatische Lap-Klassifizierung sehen und bei Bedarf korrigieren  
**damit** die HF-Zonen Arbeits-Laps korrekt sind

**Akzeptanzkriterien:**
- [ ] Jeder Lap zeigt vorgeschlagenen Typ (warmup/interval/etc.)
- [ ] Confidence wird angezeigt (high/medium/low)
- [ ] Dropdown erlaubt manuelle Änderung pro Lap
- [ ] Änderung triggert Neuberechnung der Arbeits-Laps HF-Zonen
- [ ] User Override wird gespeichert

**Priorität:** 🔴 CRITICAL (MVP)

---

### UC-3: Training speichern und später abrufen
**Als** Läufer  
**möchte ich** meine Trainings persistent speichern  
**damit** ich sie später wieder ansehen und vergleichen kann

**Akzeptanzkriterien:**
- [ ] Training wird in Datenbank gespeichert
- [ ] Liste aller Trainings verfügbar (chronologisch)
- [ ] Filter: Datum, Typ (Running/Strength)
- [ ] Detail-Ansicht zeigt alle Metriken
- [ ] Trainings können gelöscht werden

**Priorität:** 🔴 CRITICAL (MVP - Phase 1)

---

### UC-4: Trainingsplan erstellen
**Als** Läufer  
**möchte ich** meinen Trainingsplan (Phasen, Wochen, Ziele) digital abbilden  
**damit** ich Struktur habe und Soll/Ist vergleichen kann

**Akzeptanzkriterien:**
- [ ] Plan hat Name, Ziel, Zeitraum
- [ ] Phasen definieren (Aufbau/Spezifisch/Tapering)
- [ ] Pro Phase: Fokus & Ziel-Metriken
- [ ] Wochenstruktur (Ruhetage, feste Slots)
- [ ] Plan kann bearbeitet werden

**Priorität:** 🟠 HIGH (Phase 2)

---

### UC-5: Geplantes Training definieren
**Als** Läufer  
**möchte ich** für jeden Tag konkrete Trainingsvorgaben festlegen  
**damit** ich weiß was ich machen soll

**Akzeptanzkriterien:**
- [ ] Training einem Datum zuordnen
- [ ] Typ wählen (Intervalle, Tempo, Longrun, etc.)
- [ ] Ziele definieren (z.B. "80 min @ HF <160 bpm")
- [ ] Mehrere Ziele pro Training möglich
- [ ] Optional: Detaillierte Workout-Struktur (Intervalle mit Zeiten)

**Priorität:** 🟠 HIGH (Phase 2)

---

### UC-6: Soll/Ist-Vergleich sehen
**Als** Läufer  
**möchte ich** nach einem Training sofort sehen ob ich die Vorgaben erfüllt habe  
**damit** ich weiß ob ich on track bin

**Akzeptanzkriterien:**
- [ ] Automatischer Vergleich wenn Training geplantes Training zugeordnet
- [ ] Für jedes Ziel: Erreicht Ja/Nein
- [ ] Abweichungen in % angezeigt
- [ ] Warnungen bei kritischen Abweichungen (z.B. "HF zu hoch")
- [ ] Empfehlungen für nächstes Training

**Priorität:** 🟠 HIGH (Phase 2)

**Beispiel:**
```
Geplant: Longrun 80 min @ HF <160 bpm
Tatsächlich: 75 min @ HF Ø 167 bpm
❌ Ziel nicht erreicht
⚠️ WARNUNG: HF deutlich zu hoch (80% der Zeit >160 bpm)
💡 Empfehlung: Nächster Longrun bewusst langsamer starten
```

---

### UC-7: Equipment tracken
**Als** Läufer  
**möchte ich** meine Laufschuhe und deren Kilometer tracken  
**damit** ich weiß wann ich neue brauche

**Akzeptanzkriterien:**
- [ ] Schuhe anlegen (Marke, Modell, Kaufdatum)
- [ ] Jedem Training Schuhe zuordnen
- [ ] Automatische Kilometerzählung
- [ ] Warnung bei >500 km
- [ ] Mehrere Schuhe parallel möglich
- [ ] Historie pro Schuh sichtbar

**Priorität:** 🟡 MEDIUM (Phase 2)

---

### UC-8: Wetter-Kontext sehen
**Als** Läufer  
**möchte ich** das Wetter zum Zeitpunkt des Trainings sehen  
**damit** ich verstehe warum meine HF höher/niedriger war

**Akzeptanzkriterien:**
- [ ] Automatischer Wetter-Fetch nach Upload (via API)
- [ ] Anzeige: Temperatur, Wind, Luftfeuchtigkeit
- [ ] Erklärungen: "Bei 28°C ist HF +12 bpm normal"
- [ ] Historische Wetterdaten (OpenWeatherMap)

**Priorität:** 🟡 MEDIUM (Phase 3)

---

### UC-9: Verletzung dokumentieren
**Als** Läufer  
**möchte ich** Verletzungen/Beschwerden dokumentieren  
**damit** ich Muster erkenne und Return-to-Training plane

**Akzeptanzkriterien:**
- [ ] Verletzung anlegen (Typ, Körperteil, Schwere, Datum)
- [ ] Behandlung dokumentieren
- [ ] Impact auf Training (modifiziert/pausiert)
- [ ] Return-to-Training Protokoll
- [ ] Verletzungshistorie sichtbar
- [ ] Warnung wenn ähnliches Training nach Verletzung

**Priorität:** 🟡 MEDIUM (Phase 3)

**Beispiel Use Case:**
- Wade-Probleme nach KW06 Longrun dokumentieren
- Return-to-Training: KW07 modifiziert (langsamer, kürzer)
- System warnt vor zu schnellem Longrun in KW08

---

### UC-10: AI-Feedback erhalten
**Als** Läufer  
**möchte ich** nach jedem Training AI-Feedback  
**damit** ich weiß was gut war und was verbessert werden kann

**Akzeptanzkriterien:**
- [ ] Automatische Analyse nach Training-Upload
- [ ] 3 Kategorien: Insights, Warnings, Recommendations
- [ ] Kontext-bewusst (Trainingsplan, Historie, Ziele)
- [ ] Klare, umsetzbare Empfehlungen
- [ ] Optionale Verletzungsrisiko-Einschätzung

**Priorität:** ⚪ LOW (Phase 5)

**Beispiel:**
```
✅ INSIGHTS
- Intervalle @ 6:31/km gut gehalten, HF-Progression normal
- Recovery zwischen Intervallen ausreichend (HF Drop >20 bpm)

⚠️ WARNINGS
- Donnerstag-Lauf zu intensiv (159 bpm statt <150 bpm)
- Samstag-Longrun faktisch Tempodauerlauf (80% >160 bpm)
- 3 harte Tage in Folge → Übertrainingsrisiko

💡 RECOMMENDATIONS
- Nächster lockerer Lauf: Bewusst 7:20-7:30/km, HF <150 bpm
- Nächster Longrun: 7:00-7:10/km, "könnte noch 1h laufen"-Gefühl
- Erwäge eine Pause-Woche wenn Wadenschmerzen anhalten
```

---

## 🚫 Explizite Non-Goals (was NICHT im Scope)

### Nicht geplant:
- ❌ Live-Tracking während Training (kein Echtzeit-Coaching)
- ❌ Social Features (keine Freunde, Challenges, Leaderboards)
- ❌ Nutrition-Datenbank (keine Rezepte, Meal Plans)
- ❌ Wettkampf-Registrierung (keine Race-Suche, Anmeldung)
- ❌ Bezahlte Features / Premium-Modell
- ❌ Mobile App (erstmal nur Web)
- ❌ Multi-Sportler-Teams / Coach-Features

### Vielleicht später (Low Prio):
- 🔄 Strava Integration (Import/Export)
- 🔄 Garmin Connect Sync
- 🔄 Public Training Log (teilen mit Freunden)
- 🔄 Wettkampf-Historie

---

## 🎨 UX-Anforderungen

### Design-Prinzipien
1. **Schnell:** Uploads & Analysen in <1 Sekunde
2. **Klar:** Wichtigste Metrik sofort sichtbar
3. **Umsetzbar:** Feedback = konkrete Handlungsempfehlung
4. **Vertrauenswürdig:** Zeige Confidence bei Auto-Suggestions
5. **Fehlertolerant:** Schlechte CSV? → Klare Fehlermeldung, keine Crashes

### Wichtigste Screens
1. **Upload:** Drag & Drop, klare Instructions
2. **Session Detail:** Metriken + HF-Zonen + Lap-Tabelle + Charts
3. **Session List:** Chronologisch, Filter, Quick Stats
4. **Plan Editor:** Phasen + Wochen + Ziele visuell
5. **Evaluation:** Soll/Ist side-by-side, Warnings prominent

### Mobile-Friendly
- Responsive Design (Desktop & Mobile)
- Touch-friendly (große Buttons, keine Hover-only)
- Offline-fähig wünschenswert (PWA)

---

## 📊 Data Quality Requirements

### Training Data
- **Laps:** Min. 90% Accuracy bei Auto-Klassifizierung
- **HF-Zonen:** Auf ±2% genau
- **Pace:** Auf ±5 sec/km genau
- **Elevation:** Auf ±5m genau

### Parsing Robustness
- Handle missing GPS (Indoor)
- Handle missing HR (Sensor-Ausfall)
- Handle malformed CSV
- Handle non-standard formats

---

## 🔐 Security & Privacy

### Requirements
- **Single-User erstmal:** Keine Authentication in Phase 1
- **Data Privacy:** Nur Nils-Christian hat Zugriff
- **Backups:** Wöchentliche DB-Backups
- **No Sharing:** Trainings sind privat

### Später (Multi-User):
- [ ] User Authentication (Email/Password)
- [ ] GDPR-compliant (Daten-Export, Löschung)
- [ ] Optional: Public Profile
- [ ] API Rate Limiting

---

## 🧪 Testing Requirements

### Must be tested:
- ✅ CSV Upload (verschiedene Formate)
- ✅ Lap Classification (Edge Cases)
- ✅ HR Zones Calculation (Accuracy)
- ✅ Soll/Ist-Vergleich (Logic)
- ✅ Equipment KM Counting
- ✅ DB Migrations (up/down)

### Nice to have:
- Load Testing (1000+ Trainings)
- Mobile Responsiveness
- Browser Compatibility

---

## 📈 Success Metrics

### Phase 1 Success
- [ ] 100% meiner Trainings erfolgreich hochgeladen
- [ ] <5% manuelle Lap-Korrekturen nötig
- [ ] 0 Data Loss
- [ ] Ich nutze es jede Woche

### Phase 2 Success
- [ ] Soll/Ist-Vergleich spart mir 10 min Analyse pro Training
- [ ] Equipment-Warnung verhindert 1× "zu alte Schuhe"-Problem
- [ ] Plan-Überblick hilft bei Wochenplanung

### Long-term Success
- [ ] Ich bin verletzungsfrei geblieben (kein Übertraining)
- [ ] Sub-2h geschafft! 🎯
- [ ] Basis für nächste Saison

---

**Diese User Stories leiten die Entwicklung!**

**Prioritäten:**
1. 🔴 CRITICAL → Phase 1 MVP
2. 🟠 HIGH → Phase 2
3. 🟡 MEDIUM → Phase 3
4. ⚪ LOW → Phase 4+
