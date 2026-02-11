# 🏠 NAS Setup Guide - Mit deinem bestehenden Ollama

## ✅ Was du schon hast

- ✅ Ollama läuft auf **192.168.68.66:11434**
- ✅ Docling läuft auf **192.168.68.66:5001**
- ✅ NAS ist bereit für Docker

---

## 🚀 Quick Setup (5 Minuten)

### Schritt 1: Projekt auf NAS kopieren

```bash
# Von deinem Computer
scp -r training-analyzer/ admin@192.168.68.66:/volume1/docker/

# Oder: Lade training-analyzer.tar.gz hoch und entpacke auf dem NAS
```

### Schritt 2: SSH auf NAS

```bash
ssh admin@192.168.68.66
cd /volume1/docker/training-analyzer
```

### Schritt 3: Environment konfigurieren

```bash
# Nutze die NAS-spezifische Konfiguration
cp .env.nas.example .env

# Bearbeite die .env
nano .env
```

**Wichtige Einstellungen in .env:**

```bash
# Nutze dein bestehendes Ollama (kostenlos!)
AI_PRIMARY_PROVIDER=ollama
OLLAMA_BASE_URL=http://192.168.68.66:11434

# Dein bestehendes Docling
DOCLING_SERVER_URL=http://192.168.68.66:5001

# Secret Key generieren
SECRET_KEY=$(openssl rand -hex 32)

# NAS IP für CORS
ALLOWED_ORIGINS=http://192.168.68.66:3000
```

**Optional:** Falls du auch Claude als Fallback haben willst:
```bash
AI_FALLBACK_PROVIDERS=claude
CLAUDE_API_KEY=sk-ant-dein-key-hier
```

### Schritt 4: Starten

```bash
# Nutze die NAS-spezifische Compose-Datei (OHNE Ollama Container)
docker-compose -f docker-compose.nas.yml up -d --build

# Das dauert beim ersten Mal 2-5 Minuten
```

### Schritt 5: Testen

```bash
# Health Check
curl http://localhost:8000/health

# AI Provider Check (sollte dein Ollama finden)
curl http://localhost:8000/api/v1/ai/providers
```

**Erwartete Antwort:**
```json
{
  "primary": "Ollama (llama3.1:8b)",
  "status": {
    "Ollama (llama3.1:8b)": {
      "available": true,
      "is_primary": true
    }
  }
}
```

### Schritt 6: Frontend öffnen

```
http://192.168.68.66:3000
```

---

## ✅ Vorteile deines Setups

- ✅ **Kostenlos:** Ollama läuft lokal, keine API-Kosten
- ✅ **Privat:** Alle Daten bleiben auf deinem NAS
- ✅ **Schnell:** Kein Internet nötig für AI-Analysen
- ✅ **Einfach:** Nur 3 Container (DB, Backend, Frontend)

---

## 🧪 AI Provider testen

### Test dein Ollama

```bash
# Direkt auf deinem bestehenden Ollama
curl http://192.168.68.66:11434/api/tags

# Via Backend API
curl http://192.168.68.66:8000/api/v1/ai/providers/test/ollama
```

### Welches Modell läuft bei dir?

```bash
# Prüfe verfügbare Modelle
curl http://192.168.68.66:11434/api/tags

# Falls du llama3.1:8b noch nicht hast
docker exec -it <dein-ollama-container> ollama pull llama3.1:8b
```

---

## 📊 Ressourcen-Nutzung

Da Ollama extern läuft, braucht Training Analyzer nur:

- **CPU:** 5-10% im Leerlauf
- **RAM:** ~500 MB
- **Festplatte:** ~1 GB (Images + Datenbank)

---

## 🔧 Troubleshooting

### Backend kann Ollama nicht erreichen

```bash
# Prüfe ob Ollama läuft
curl http://192.168.68.66:11434/api/tags

# Prüfe Backend-Logs
docker-compose -f docker-compose.nas.yml logs backend | grep -i ollama

# Prüfe .env
cat .env | grep OLLAMA
```

**Häufiger Fehler:** Docker Container kann externe IP nicht erreichen

**Lösung:** Docker muss auf Host-Netzwerk zugreifen können:

```bash
# In .env überprüfen:
OLLAMA_BASE_URL=http://192.168.68.66:11434  # ✓ Richtig
# NICHT: http://localhost:11434  # ✗ Falsch (nur innerhalb Container)
```

### Docling nicht erreichbar

```bash
# Teste Docling
curl http://192.168.68.66:5001/health

# Falls nicht erreichbar, prüfe Docling Container
# (wie auch immer du Docling gestartet hast)
```

---

## 🎯 Empfohlene Konfiguration

**Für beste Performance & keine Kosten:**

```bash
# .env
AI_PRIMARY_PROVIDER=ollama
AI_FALLBACK_PROVIDERS=
OLLAMA_BASE_URL=http://192.168.68.66:11434
OLLAMA_MODEL=llama3.1:8b  # oder was bei dir läuft
```

**Für beste Qualität (mit geringen Kosten):**

```bash
# .env
AI_PRIMARY_PROVIDER=claude
AI_FALLBACK_PROVIDERS=ollama
CLAUDE_API_KEY=sk-ant-xxx
OLLAMA_BASE_URL=http://192.168.68.66:11434
```

So hast du Premium-Qualität mit kostenlosem Fallback!

---

## 📝 Container-Übersicht

Dein Setup läuft mit nur **3 Containern**:

```
training-analyzer-db       → PostgreSQL
training-analyzer-backend  → FastAPI API
training-analyzer-frontend → React App

Extern (bereits vorhanden):
- Ollama auf 192.168.68.66:11434
- Docling auf 192.168.68.66:5001
```

---

## 🚀 Nächste Schritte

1. ✅ Projekt auf NAS kopieren
2. ✅ `.env` aus `.env.nas.example` erstellen
3. ✅ `docker-compose.nas.yml` verwenden (ohne Ollama)
4. ✅ Starten mit `docker-compose -f docker-compose.nas.yml up -d`
5. ✅ Testen auf http://192.168.68.66:3000

**Ready to go! 🎉**
