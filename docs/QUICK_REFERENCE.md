# 🚀 Quick Reference - For Claude AI Sessions

**Zweck:** Schneller Einstieg für neue Claude-Sessions  
**Wenn Chat weg ist:** Lies DIESE Datei zuerst!

---

## 📁 Wichtigste Dokumente (Lesereihenfolge)

1. **START_HERE.md** - Projekt-Übersicht (falls vorhanden)
2. **docs/IMPLEMENTATION_STATUS.md** ⭐ - **Was funktioniert, was nicht**
3. **docs/TRAINING_CONTEXT.md** - Nils-Christians Training (Ziele, Constraints)
4. **docs/DOMAIN_MODEL.md** - Technische Architektur (15 Entities)
5. **docs/USER_STORIES.md** - Requirements & Prioritäten
6. **docs/CSV_FORMAT_EXAMPLES.md** - Datenformat-Details

---

## 🎯 Projekt-Zusammenfassung (30 Sekunden)

**Was:** Training Analyzer für Halbmarathon-Vorbereitung  
**Für:** Nils-Christian (Runner, Sub-2h Ziel Ende März 2026)  
**Stack:** FastAPI (Backend) + React/TypeScript (Frontend) + PostgreSQL (geplant)  
**Deployed:** Synology NAS (192.168.68.52)  

**Aktueller Stand:**
- ✅ CSV Upload funktioniert
- ✅ Lap Classification mit User Override
- ✅ HF-Zonen (Gesamt + Arbeits-Laps)
- ❌ KEINE Datenbank-Persistenz (noch!)

**Nächstes Ziel:** PostgreSQL Schema + Sessions speichern

---

## 🔑 Wichtigste Fakten

### Training
- **Ziel:** Sub-2h Halbmarathon = 5:41 min/km
- **Bisherige Bestzeit:** 1:55:20 (Sep 2024)
- **Ruhetage:** Montag & Sonntag (FEST!)
- **Trainingsplan:** 3 Phasen (Aufbau/Spezifisch/Tapering)
- **Problem KW06:** Longrun zu intensiv (167 bpm statt <160)

### Technologie
- **Backend:** Python FastAPI, CSV Parser, Lap Classification
- **Frontend:** React + Vite + TypeScript, Tailwind CSS
- **Deployment:** Docker Compose, Gitea Webhook
- **Datenbank:** Noch nicht implementiert (Phase 1)

### Wichtige Entscheidungen
- 3-Zonen HF-System (nicht 5-Zonen)
- Lap-Klassifizierung basierend auf Training Subtype
- Flexible Target-System (keine Schema-Änderungen für neue Metriken)
- Progressive Enhancement (alle Felder optional)

---

## 🚨 Kritische Dateien

### Backend
```
backend/app/services/csv_parser.py    # Lap Classification Logic ⭐
backend/app/routers/training.py       # Upload Endpoint
backend/app/main.py                   # FastAPI Entry
```

### Frontend
```
frontend/src/pages/Upload.tsx         # Main UI ⭐
frontend/package.json                 # Dependencies (lucide-react!)
frontend/postcss.config.js            # Tailwind Config
```

### Docs
```
docs/IMPLEMENTATION_STATUS.md         # Status Tracking ⭐
docs/TRAINING_CONTEXT.md              # Nils' Training Context
docs/DOMAIN_MODEL.md                  # Architecture
```

---

## 📝 Typische Aufgaben & wo Code ist

### "Lap-Klassifizierung ändern"
→ `backend/app/services/csv_parser.py` → `_classify_laps()` Methode

### "HF-Zonen Berechnung anpassen"
→ `backend/app/services/csv_parser.py` → `_calculate_hr_zones()` Methode

### "Frontend UI ändern"
→ `frontend/src/pages/Upload.tsx` → React Components

### "Neue API Route"
→ `backend/app/routers/training.py` → @router.post/get/put

### "Datenbank Schema"
→ Noch nicht vorhanden, aber geplant in `backend/app/models/`

---

## 🐛 Bekannte Issues

1. **Keine Persistenz:** Sessions werden nicht gespeichert
2. **Keine Auth:** Jeder mit NAS-Zugriff kann uploaden
3. **Kein Error Handling:** CSV-Fehler crashen Parser manchmal
4. **Keine Charts:** Nur Tabellen, keine Visualisierungen

---

## 🎯 Nächste Schritte (Phase 1 MVP)

### Priorität 1
1. PostgreSQL Setup (Docker Compose)
2. SQLAlchemy Models (Athlete, TrainingSession, TrainingLap)
3. Alembic Migrations
4. POST /sessions Endpoint (DB Insert)
5. GET /sessions Endpoint (List)

### Priorität 2
6. Frontend: Session List Page
7. Frontend: Session Detail Page
8. CSV Parser → DB Integration
9. Testing
10. Deployment

**Zeitschätzung:** 2-3 Wochen

---

## 💡 Wichtige Konzepte

### Lap Types
- `warmup` - Aufwärmen
- `interval` - Intensiver Block
- `recovery` - Aktive Erholung / Trab
- `tempo` - Tempodauerlauf
- `cooldown` - Auslaufen
- `work` - Generische Arbeitsphase
- `unclassified` - Unbekannt

### HF-Zonen (3-Zonen System)
- **Zone 1 (<150 bpm):** Recovery
- **Zone 2 (150-160 bpm):** Base
- **Zone 3 (>160 bpm):** Tempo/Intense

### Training Subtypes
- `interval` - Intervall-Training
- `tempo` - Tempodauerlauf
- `longrun` - Langer Lauf
- `recovery` - Regenerationslauf

---

## 🔧 Häufige Commands

### Development
```bash
# Backend starten
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend starten
cd frontend
npm run dev

# Docker Build
docker compose build
docker compose up -d
```

### Deployment (NAS)
```bash
# SSH zum NAS
ssh root@192.168.68.52

# Logs checken
cd /volume1/docker/training-analyzer
docker compose logs -f frontend
docker compose logs -f backend

# Rebuild
docker compose build --no-cache
docker compose up -d
```

### Git
```bash
# Docs updaten nach Session
git add docs/
git commit -m "docs: update after session YYYY-MM-DD"
git push
# → Webhook deployed automatisch
```

---

## 📞 Wenn Claude verwirrt ist

### Checkliste:
1. ✅ Hast du `IMPLEMENTATION_STATUS.md` gelesen?
2. ✅ Ist die Aufgabe in `USER_STORIES.md` dokumentiert?
3. ✅ Ist der Kontext in `TRAINING_CONTEXT.md` klar?
4. ✅ Brauchst du technische Details? → `DOMAIN_MODEL.md`
5. ✅ Brauchst du Datenformat-Infos? → `CSV_FORMAT_EXAMPLES.md`

### Wenn immer noch unklar:
- **ASK!** Frage Nils-Christian nach Klarstellung
- **Don't guess!** Lieber 2x fragen als falsch implementieren
- **Document!** Neue Entscheidungen in `IMPLEMENTATION_STATUS.md`

---

## 🎓 Lern-Ressourcen

### Trainingswissenschaft
- 10%-Regel: Max. 10% Steigerung pro Woche
- 80/20-Regel: 80% locker, 20% intensiv
- Periodisierung: Aufbau → Spezifisch → Tapering
- GA1: Grundlagenausdauer Zone 1-2
- RPE: Rate of Perceived Exertion (1-10)

### Tech Stack
- FastAPI Docs: https://fastapi.tiangolo.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- Alembic: https://alembic.sqlalchemy.org/
- React: https://react.dev/
- Tailwind: https://tailwindcss.com/

---

## 🎯 Quick Wins (wenn Zeit ist)

### Easy Improvements
- [ ] Loading States im Frontend
- [ ] Better Error Messages
- [ ] CSV Download (exportieren)
- [ ] Dark Mode
- [ ] Keyboard Shortcuts

### Medium Effort
- [ ] Charts (HR/Pace over time)
- [ ] Elevation Profile Chart
- [ ] Session Comparison
- [ ] Export to PDF

---

## 💾 Backup & Recovery

### Wichtige Dateien sichern
- `docs/*.md` - Dokumentation
- `backend/app/` - Backend Code
- `frontend/src/` - Frontend Code
- `docker-compose.yml` - Deployment Config

### Bei Datenverlust
1. Git History checken: `git log --oneline`
2. NAS Backups: `/volume1/docker/training-analyzer/`
3. Transcripts: `/mnt/transcripts/` (wenn verfügbar)

---

## 🏁 Session Start Checklist

Neue Claude-Session? Mache das:

1. ✅ Lese `docs/IMPLEMENTATION_STATUS.md` (aktueller Stand)
2. ✅ Checke letzte Änderungen: `git log -5 --oneline`
3. ✅ Frage Nils-Christian: "Was sollen wir heute machen?"
4. ✅ Lies relevante Docs (TRAINING_CONTEXT, USER_STORIES, etc.)
5. ✅ Start coding! 🚀

## 🏁 Session End Checklist

Session beenden? Mache das:

1. ✅ Update `docs/IMPLEMENTATION_STATUS.md` (Was wurde gemacht?)
2. ✅ Commit & Push Änderungen
3. ✅ Test auf NAS (funktioniert Deployment?)
4. ✅ Dokumentiere offene TODOs
5. ✅ Sage Nils-Christian was next steps sind

---

**🎉 Ready to code! Los geht's!**
