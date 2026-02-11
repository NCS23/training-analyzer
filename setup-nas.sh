#!/bin/bash
# Training Analyzer - Automatisches NAS Setup
# Für Synology/QNAP NAS mit SSH Port 47

set -e

echo "🏠 Training Analyzer - NAS Setup"
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Prüfe ob .env.nas.example existiert
if [ ! -f ".env.nas.example" ]; then
    echo -e "${RED}❌ .env.nas.example nicht gefunden${NC}"
    echo "Bitte stelle sicher dass du im training-analyzer/ Verzeichnis bist"
    exit 1
fi

echo "📝 Erstelle .env Datei..."

# Generiere Secret Key
SECRET_KEY=$(openssl rand -hex 32)

# Erstelle .env Datei
cat > .env << EOF
# ============================================
# Training Analyzer - NAS Configuration
# Automatisch generiert: $(date)
# ============================================

# ===== DATABASE =====
DATABASE_URL=postgresql://training_user:training_pass@postgres:5432/training_analyzer

# ===== AI PROVIDER CONFIGURATION =====
AI_PRIMARY_PROVIDER=ollama
AI_FALLBACK_PROVIDERS=

# ----- Ollama (Läuft auf Mac: 192.168.68.66) -----
OLLAMA_BASE_URL=http://192.168.68.66:11434
OLLAMA_MODEL=llama3.1:8b

# ----- Claude (Optional - für Premium-Qualität) -----
# Uncomment und füge deinen Key ein falls gewünscht:
# CLAUDE_API_KEY=sk-ant-dein-key-hier
# CLAUDE_MODEL=claude-sonnet-4-20250514

# ===== DOCLING OCR SERVER =====
# Docling auf Mac: 192.168.68.66
DOCLING_SERVER_URL=http://192.168.68.66:5001

# ===== SECURITY =====
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ===== CORS =====
# Frontend läuft auf NAS: 192.168.68.52
ALLOWED_ORIGINS=http://192.168.68.52:3000,http://localhost:3000

# ===== AI SETTINGS =====
AI_MAX_TOKENS_ANALYSIS=1000
AI_MAX_TOKENS_CHAT=2000
AI_MAX_TOKENS_REPORT=3000
AI_TEMPERATURE=0.3
AI_TIMEOUT=120

# ===== DEVELOPMENT =====
DEBUG=false
LOG_LEVEL=INFO
EOF

echo -e "${GREEN}✅ .env Datei erstellt${NC}"
echo ""

# Zeige wichtige Einstellungen
echo "📋 Konfiguration:"
echo "   NAS (App):      192.168.68.52"
echo "   Mac (Ollama):   192.168.68.66:11434"
echo "   Mac (Docling):  192.168.68.66:5001"
echo "   Secret Key:     [generiert]"
echo ""

# Frage nach Claude API Key
echo -e "${YELLOW}💡 Optional: Claude API Key${NC}"
echo "   Willst du Claude als Fallback nutzen? (Premium-Qualität, ~\$1-2/Monat)"
read -p "   Claude API Key eingeben (oder Enter überspringen): " CLAUDE_KEY

if [ ! -z "$CLAUDE_KEY" ]; then
    # Füge Claude Key hinzu
    sed -i "s|# CLAUDE_API_KEY=.*|CLAUDE_API_KEY=$CLAUDE_KEY|" .env
    sed -i "s|# CLAUDE_MODEL=.*|CLAUDE_MODEL=claude-sonnet-4-20250514|" .env
    sed -i "s|AI_FALLBACK_PROVIDERS=|AI_FALLBACK_PROVIDERS=claude|" .env
    echo -e "${GREEN}✅ Claude als Fallback aktiviert${NC}"
else
    echo -e "${YELLOW}⏭️  Nur Ollama wird genutzt (kostenlos)${NC}"
fi

echo ""
echo "🐳 Starte Docker Container..."
echo ""

# Starte Container
docker-compose -f docker-compose.nas.yml up -d --build

echo ""
echo "⏳ Warte auf Services..."
sleep 10

# Prüfe Backend Health
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Backend ist bereit${NC}"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "   Warte auf Backend... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Backend konnte nicht gestartet werden${NC}"
    echo "Logs prüfen: docker-compose -f docker-compose.nas.yml logs backend"
    exit 1
fi

# Prüfe AI Provider
echo ""
echo "🤖 Prüfe AI Provider..."
AI_STATUS=$(curl -s http://localhost:8000/api/v1/ai/providers)

if echo "$AI_STATUS" | grep -q "Ollama"; then
    echo -e "${GREEN}✅ Ollama verbunden${NC}"
else
    echo -e "${YELLOW}⚠️  Ollama nicht erreichbar${NC}"
    echo "   Prüfe ob Ollama auf 192.168.68.66:11434 läuft"
fi

echo ""
echo "======================================"
echo -e "${GREEN}🎉 Setup abgeschlossen!${NC}"
echo "======================================"
echo ""
echo "📱 Zugriff:"
echo "   Frontend:    http://192.168.68.52:3000"
echo "   API:         http://192.168.68.52:8000"
echo "   API Docs:    http://192.168.68.52:8000/docs"
echo ""
echo "   Ollama:      http://192.168.68.66:11434"
echo "   Docling:     http://192.168.68.66:5001"
echo ""
echo "📊 Status prüfen:"
echo "   docker-compose -f docker-compose.nas.yml ps"
echo ""
echo "📋 Logs ansehen:"
echo "   docker-compose -f docker-compose.nas.yml logs -f"
echo ""
echo "🛑 Stoppen:"
echo "   docker-compose -f docker-compose.nas.yml down"
echo ""
echo "✨ Viel Erfolg mit deinem Training Analyzer!"
echo ""
