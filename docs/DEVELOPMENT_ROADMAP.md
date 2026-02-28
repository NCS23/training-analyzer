# 🗺️ Training Analyzer - Development Roadmap

## 🎯 Strategischer Plan (Abgestimmt!)

> **Phase 1:** Web App fertig machen  
> **Phase 2:** iOS Companion App (WorkoutKit)  
> **Phase 3:** Full Native App

---

## 📍 PHASE 1: Web App Feature-Complete (JETZT - nächste 2-3 Monate)

### **Status Quo:**
```
✅ Backend: FastAPI auf NAS (Docker)
✅ Frontend: React/TypeScript
✅ Deployment: GitHub Actions + Docker Compose
✅ CSV Import & Parsing
⏳ FIT Import (in Arbeit)
⏳ Lap Classification (in Arbeit)
⏳ Training Analysis Features
```

### **Ziele Phase 1:**

#### **1. File Import & Parsing (Priorität: HOCH)**
```
✅ CSV Import (Done)
🔄 FIT Import (Current)
   ├─ FIT Parser Integration (fitparse)
   ├─ Running Dynamics Extraktion
   ├─ Power Data
   └─ Workout Structure Auto-Detection
⏳ Bulk Import (mehrere Files auf einmal)
⏳ Auto-Import (Watch Ordner?)
```

#### **2. Lap Classification (Priorität: HOCH)**
```
🔄 Automatic Lap Type Detection
   ├─ HR-basierte Klassifizierung
   ├─ Pattern Recognition (Intervalle)
   ├─ Confidence Scoring
   └─ Manual Override Möglichkeit
⏳ FIT Workout Steps → Lap Types (nutze Workout Structure!)
⏳ Klassifizierung History/Learning
```

#### **3. Training Analysis Dashboard (Priorität: MITTEL)**
```
⏳ Session Overview
   ├─ HR Zones Verteilung
   ├─ Pace Distribution
   ├─ Lap-by-Lap Vergleich
   └─ Trends über Zeit
⏳ Interactive Charts
   ├─ HR over Time
   ├─ Pace over Time
   ├─ HR vs Pace Correlation
   └─ Running Dynamics (wenn FIT)
⏳ Training Load / TSS
```

#### **4. Training Planning (Priorität: MITTEL)**
```
⏳ Create Planned Trainings
   ├─ Intervall-Templates
   ├─ Custom Workouts
   └─ Training Calendar
⏳ Export als .workout File (für HealthFit)
⏳ Export als Anleitung (Text/PDF)
```

#### **5. Data Management (Priorität: NIEDRIG)**
```
⏳ Training Session Editing
⏳ Bulk Delete/Archive
⏳ Export (CSV, JSON)
⏳ Backup/Restore
```

### **Timeline Phase 1:**
```
Woche 1-2:   FIT Import finalisieren ✅
Woche 3-4:   Lap Classification (Auto + Manual)
Woche 5-6:   Analysis Dashboard (Charts, HR Zones)
Woche 7-8:   Training Planning (Basics)
Woche 9-10:  Polish, Testing, Documentation
```

**Meilenstein:** Web App ist vollständig nutzbar für Training Analysis! 🎉

---

## 📍 PHASE 2: iOS Companion App (WorkoutKit) (3-6 Monate später)

### **Kontext:**
- Web App läuft & funktioniert
- Fokus: **Apple Watch Integration**
- Web bleibt Haupt-Platform

### **Ziele Phase 2:**

#### **iOS App Scope (MINIMAL!):**
```
✅ Login (Backend API)
✅ Workout List (von Backend laden)
✅ Workout Detail View
✅ "An Watch senden" Button
   └─ WorkoutKit Integration
   └─ Als GEPLANT auf Watch! ✅
⏳ Optional: Completed Workouts zurück importieren
```

**Wichtig:** **KEINE** Duplikation der Web-Features!  
Die App ist NUR der **"Bridge zur Apple Watch"**.

### **Tech Stack Phase 2:**
```swift
// Minimal Swift App
- SwiftUI (UI)
- URLSession (API Calls zum Backend)
- WorkoutKit (Watch Sync)
- Keychain (Token Storage)
```

### **API Erweiterungen (Backend):**
```python
# Neue Endpoints
GET  /api/v1/workouts/planned          # Liste geplanter Workouts
GET  /api/v1/workouts/planned/{id}     # Workout Details
POST /api/v1/workouts/planned/{id}/sync # Mark as synced to Watch
POST /api/v1/workouts/completed        # Import completed workout
```

### **Timeline Phase 2:**
```
Woche 1:    Setup (Xcode, Project Structure, API Client)
Woche 2:    UI (Login, Workout List, Detail View)
Woche 3:    WorkoutKit Integration & Testing
Woche 4:    Polish, TestFlight Beta, App Store Submission
```

**Meilenstein:** Workouts landen als GEPLANT auf der Watch! 🎉

---

## 📍 PHASE 3: Full Native App (6-12 Monate später)

### **Kontext:**
- Web App funktioniert vollständig
- iOS Companion beweist Konzept
- **Jetzt: Migration zu Native-First**

### **Entscheidungspunkt:**
```
Frage: "Ist Native wirklich besser als Web?"

Evaluierung:
├─ User Experience: Native besser? ✅/❌
├─ Performance: Spürbar schneller? ✅/❌
├─ Wartungsaufwand: Wirklich weniger? ✅/❌
└─ Features: Fehlt etwas von Web? ✅/❌

Wenn mehrheitlich ✅ → GO for Native-First!
Wenn ❌ → Web bleibt Primary, iOS nur Companion
```

### **Ziele Phase 3 (wenn GO):**

#### **Feature Migration:**
```
✅ FIT/CSV Import (nativ)
✅ Lap Classification (Swift Port)
✅ Training Analysis (SwiftUI Charts)
✅ Training Planning
✅ iCloud Sync (Multi-Device)
✅ HealthKit Integration
   ├─ Auto-Import von Workouts
   └─ Write Training Plans
✅ WorkoutKit (bereits da!)
✅ Widgets, Shortcuts, Siri
```

#### **Native-Only Features:**
```
✅ Apple Watch Companion App
   ├─ Quick Stats
   ├─ Planned Workouts View
   └─ Start Workout direkt von Watch
✅ Live Activities (während Training)
✅ Focus Modes Integration
✅ Offline-First (alles lokal!)
```

### **Architektur Phase 3:**
```
┌────────────────────────────────────────┐
│  iOS/iPad/Mac App (SwiftUI)            │
│  ├─ Core Data / Swift Data (lokal)    │
│  ├─ CloudKit (iCloud Sync)             │
│  ├─ WorkoutKit                         │
│  ├─ HealthKit                          │
│  └─ Local Analysis Engine (Swift)     │
└────────────────────────────────────────┘
         │
         │ Optional (Migration Period)
         ↓
┌────────────────────────────────────────┐
│  Web App (Legacy/Backup)               │
│  - Große Analysen am Desktop           │
│  - Backup-Zugriff                      │
│  - Daten-Export                        │
└────────────────────────────────────────┘
```

### **Timeline Phase 3:**
```
Monat 1:   Core Data Models, Sync Engine
Monat 2:   FIT/CSV Parser (Swift)
Monat 3:   Analysis Engine (Swift Port)
Monat 4:   UI (Dashboard, Charts)
Monat 5:   Training Planning
Monat 6:   iCloud Sync, Testing, Polish
Monat 7:   Beta Testing, Feedback
Monat 8:   App Store Launch 🚀
```

**Meilenstein:** Vollständige Native App, NAS optional! 🎉

---

## 🎯 Fokus-Bereiche pro Phase

### **Phase 1: Web App (JETZT)**
**Hauptfokus:**
- ✅ Backend Stabilität
- ✅ Feature-Complete für Analyse
- ✅ Datenmodell finalisieren

**Was NICHT tun:**
- ❌ Mobile Optimierung (kommt später in Native)
- ❌ Komplexe UI-Animationen
- ❌ Übertriebene Visualisierungen

**Mindset:** "Funktional > Fancy"

---

### **Phase 2: iOS Companion (später)**
**Hauptfokus:**
- ✅ WorkoutKit Integration
- ✅ Stabiles API zum Backend
- ✅ Simple, klare UI

**Was NICHT tun:**
- ❌ Feature-Duplikation von Web
- ❌ Komplexe Analysis in App
- ❌ Lokale Datenbank (noch!)

**Mindset:** "Bridge, not Replacement"

---

### **Phase 3: Native App (viel später)**
**Hauptfokus:**
- ✅ Feature Parity mit Web
- ✅ Native Performance
- ✅ iCloud Sync

**Was NICHT tun:**
- ❌ Big Bang Migration (schrittweise!)
- ❌ Web-App sofort abschalten
- ❌ Neue Features während Migration

**Mindset:** "Migration, dann Innovation"

---

## 📊 Success Metrics

### **Phase 1 Erfolg = Web App Done**
```
✅ Alle Core Features implementiert
✅ Lap Classification funktioniert zuverlässig
✅ FIT & CSV Import stabil
✅ Kann für eigenes Training genutzt werden
✅ Dokumentation vollständig
```

### **Phase 2 Erfolg = Watch Integration Works**
```
✅ iOS App im App Store
✅ Workouts landen als GEPLANT auf Watch
✅ Workflow funktioniert: Web Plan → iOS → Watch
✅ Kein manuelles Tippen mehr in HealthFit!
```

### **Phase 3 Erfolg = Native-First Viable**
```
✅ Alle Web-Features auch nativ
✅ iCloud Sync funktioniert zwischen Geräten
✅ Performance besser als Web
✅ Kann Web-App ersetzen (optional NAS abschalten)
```

---

## 🚀 Aktuelle Priorität (JETZT)

### **Diese Woche:**
```
🔄 FIT Import finalisieren
   └─ Running Dynamics, Power, Workout Structure
```

### **Nächste 2 Wochen:**
```
⏳ Lap Classification implementieren
   ├─ Auto-Detection Algorithmus
   ├─ Manual Override UI
   └─ Testing mit echten Daten
```

### **Nächster Monat:**
```
⏳ Analysis Dashboard
   └─ HR Zones, Pace, Charts
```

---

## 🎓 Lessons Learned (für später)

### **Von Phase 1 mitnehmen:**
- Domain Models (Python) → Swift portierbar halten
- API Design: RESTful, gut dokumentiert
- Algorithmen: Klar dokumentiert für Swift-Port
- Datenbank Schema: Migration-freundlich

### **Für Phase 2 vorbereiten:**
- Backend: Planned Workouts API ready
- Dokumentation: API Specs aktuell
- Testing: Gute Test-Coverage

### **Für Phase 3 im Hinterkopf:**
- Core Logic: Platform-agnostic dokumentieren
- Sync: Von Anfang an Conflict-Resolution denken
- Data Models: Schema-Evolution planen

---

## ✅ Zusammenfassung

**Dein Plan ist perfekt! 🎯**

### **Phase 1: Web App fertig machen**
- Fokus: **JETZT**
- Dauer: **2-3 Monate**
- Ziel: Feature-Complete Analysis Tool

### **Phase 2: iOS Companion**
- Fokus: **Später (Q2/Q3 2026)**
- Dauer: **1 Monat**
- Ziel: Apple Watch Integration

### **Phase 3: Full Native**
- Fokus: **Noch später (Q4 2026 / Q1 2027)**
- Dauer: **6-8 Monate**
- Ziel: Native-First, NAS optional

---

## 🤝 Wie ich helfe

### **Phase 1 (JETZT):**
- ✅ FIT Parsing Support
- ✅ Lap Classification Algorithmen
- ✅ Backend Implementation
- ✅ Testing & Debugging

### **Phase 2 (später):**
- ✅ Swift/SwiftUI Code schreiben
- ✅ WorkoutKit Integration
- ✅ API Design für iOS
- ✅ TestFlight & App Store

### **Phase 3 (viel später):**
- ✅ Python → Swift Migration
- ✅ iCloud Sync Implementation
- ✅ Full App Development
- ✅ Architecture & Best Practices

---

**Los geht's mit Phase 1! 🚀**

Was ist dein nächster konkreter Schritt für die Web App?

