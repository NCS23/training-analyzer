# 🌐 Deine Netzwerk-Topologie

## IP-Adressen Übersicht

```
┌─────────────────────────────────────────┐
│  Dein Netzwerk                          │
│                                         │
│  ┌──────────────────┐                  │
│  │ NAS              │                  │
│  │ 192.168.68.52    │ ◄─── Training Analyzer App (Docker)
│  │                  │      - Frontend: Port 3002
│  │ - PostgreSQL     │      - Backend:  Port 8001
│  │ - Backend API    │      - Database: Port 5433
│  │ - React Frontend │                  │
│  └──────────────────┘                  │
│           │                            │
│           │ Netzwerk                   │
│           │                            │
│  ┌──────────────────┐                  │
│  │ Mac              │                  │
│  │ 192.168.68.66    │ ◄─── Externe Services
│  │                  │      - Ollama:  Port 11434
│  │ - Ollama LLM     │      - Docling: Port 5001
│  │ - Docling OCR    │                  │
│  └──────────────────┘                  │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🔌 Verbindungen

### Backend (auf NAS) → Ollama (auf Mac)
```
http://192.168.68.66:11434
```

### Backend (auf NAS) → Docling (auf Mac)
```
http://192.168.68.66:5001
```

### Frontend (Browser) → Backend (auf NAS)
```
http://192.168.68.52:8001
```

---

## ✅ Korrekte Konfiguration

### .env Datei auf dem NAS

```bash
# Database (intern im Docker-Netzwerk)
DATABASE_URL=postgresql://training_user:training_pass@postgres:5432/training_analyzer

# AI Provider
AI_PRIMARY_PROVIDER=ollama
AI_FALLBACK_PROVIDERS=

# Ollama auf Mac
OLLAMA_BASE_URL=http://192.168.68.66:11434
OLLAMA_MODEL=llama3.1:8b

# Docling auf Mac  
DOCLING_SERVER_URL=http://192.168.68.66:5001

# CORS - Frontend auf NAS
ALLOWED_ORIGINS=http://192.168.68.52:3002,http://localhost:3000

# Security
SECRET_KEY=dein-generierter-key
```

---

## 🚀 Setup auf NAS (192.168.68.52)

```bash
# 1. SSH zum NAS (Port 47)
ssh -p 47 admin@192.168.68.52

# 2. Ins Projektverzeichnis
cd /volume1/docker/training-analyzer

# 3. Setup-Script ausführen
./setup-nas.sh

# Das Script konfiguriert automatisch:
# - Ollama auf 192.168.68.66:11434
# - Docling auf 192.168.68.66:5001
# - Frontend/Backend auf 192.168.68.52
```

---

## 🧪 Testen

### Vom NAS aus testen

```bash
# Backend Health
curl http://localhost:8000/health

# Ollama erreichbar?
curl http://192.168.68.66:11434/api/tags

# Docling erreichbar?
curl http://192.168.68.66:5001/health
```

### Von deinem Computer aus testen

```bash
# Frontend öffnen (NAS)
open http://192.168.68.52:3002

# API Docs (NAS)
open http://192.168.68.52:8001/docs

# Ollama testen (Mac)
curl http://192.168.68.66:11434/api/tags

# Docling testen (Mac)
curl http://192.168.68.66:5001/health
```

---

## 🔧 Wichtige URLs

### Auf dem NAS (192.168.68.52)
- **Frontend:** http://192.168.68.52:3002
- **Backend API:** http://192.168.68.52:8001
- **API Docs:** http://192.168.68.52:8001/docs
- **Health Check:** http://192.168.68.52:8001/health

### Auf dem Mac (192.168.68.66)
- **Ollama API:** http://192.168.68.66:11434
- **Docling API:** http://192.168.68.66:5001

---

## ⚠️ Firewall Hinweise

### Auf dem NAS (192.168.68.52)

Stelle sicher dass diese Ports offen sind:
- **3002** - Frontend (für Browser-Zugriff)
- **8001** - Backend API (für Frontend)
- **5433** - PostgreSQL (extern, intern 5432)

### Auf dem Mac (192.168.68.66)

Stelle sicher dass diese Ports erreichbar sind:
- **11434** - Ollama (für Backend auf NAS)
- **5001** - Docling (für Backend auf NAS)

---

## 🔍 Troubleshooting

### Backend kann Ollama nicht erreichen

```bash
# Vom NAS aus testen
ssh -p 47 admin@192.168.68.52
curl http://192.168.68.66:11434/api/tags

# Wenn das nicht funktioniert:
# 1. Prüfe ob Ollama auf dem Mac läuft
# 2. Prüfe Firewall auf dem Mac (Port 11434)
# 3. Prüfe ob NAS und Mac im gleichen Netzwerk sind
```

### Backend kann Docling nicht erreichen

```bash
# Vom NAS aus testen
ssh -p 47 admin@192.168.68.52
curl http://192.168.68.66:5001/health

# Wenn das nicht funktioniert:
# 1. Prüfe ob Docling auf dem Mac läuft
# 2. Prüfe Firewall auf dem Mac (Port 5001)
```

### Frontend kann Backend nicht erreichen

```bash
# Browser öffnen und Console prüfen (F12)
# Sollte keine CORS-Fehler zeigen

# Falls CORS-Fehler:
# Prüfe .env auf NAS:
cat /volume1/docker/training-analyzer/.env | grep ALLOWED_ORIGINS
# Sollte enthalten: http://192.168.68.52:3002
```

---

## 📊 Netzwerk-Tests

### Kompletter Connectivity-Test

```bash
# Auf dem NAS
ssh -p 47 admin@192.168.68.52

# 1. Backend läuft?
curl http://localhost:8000/health

# 2. Ollama erreichbar?
curl http://192.168.68.66:11434/api/tags

# 3. Docling erreichbar?
curl http://192.168.68.66:5001/health

# 4. AI Provider Check
curl http://localhost:8000/api/v1/ai/providers

# Sollte zeigen:
# {"primary": "Ollama (llama3.1:8b)", "status": {...}}
```

---

## 🎯 Setup-Zusammenfassung

### Was läuft wo?

| Service | Host | IP | Port |
|---------|------|----|----- |
| PostgreSQL | NAS | 192.168.68.52 | 5433 |
| Backend API | NAS | 192.168.68.52 | 8001 |
| Frontend | NAS | 192.168.68.52 | 3002 |
| Ollama | Mac | 192.168.68.66 | 11434 |
| Docling | Mac | 192.168.68.66 | 5001 |

### Netzwerk-Flows

```
Browser → Frontend (192.168.68.52:3002)
Frontend → Backend (192.168.68.52:8001)
Backend → PostgreSQL (localhost:5432 intern / 5433 extern)
Backend → Ollama (192.168.68.66:11434)
Backend → Docling (192.168.68.66:5001)
```

---

## ✅ Quick Start

```bash
# 1. SSH zum NAS
ssh -p 47 admin@192.168.68.52

# 2. Setup ausführen
cd /volume1/docker/training-analyzer
./setup-nas.sh

# 3. Frontend öffnen
open http://192.168.68.52:3002
```

**Fertig! 🎉**

---

## 📚 Weitere Hilfe

- **Setup-Script:** `setup-nas.sh` (automatisch konfiguriert)
- **vi Editor Hilfe:** `docs/VI_QUICK_REFERENCE.md`
- **NAS Setup:** `docs/NAS_SETUP.md`
- **Allgemeine Doku:** `README.md`
