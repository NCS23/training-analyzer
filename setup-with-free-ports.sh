#!/bin/bash
# Find free ports and setup Training Analyzer

echo "🔍 Suche freie Ports..."
echo ""

# Funktion um zu prüfen ob Port frei ist
check_port() {
    local port=$1
    if sudo netstat -tulpn | grep -q ":$port "; then
        return 1  # Port belegt
    else
        return 0  # Port frei
    fi
}

# Suche freie Ports
echo "Prüfe Ports..."

# Frontend Port (ab 3000)
FRONTEND_PORT=""
for port in {3000..3010}; do
    if check_port $port; then
        FRONTEND_PORT=$port
        echo "✅ Frontend Port gefunden: $port"
        break
    fi
done

# Backend Port (ab 8000)
BACKEND_PORT=""
for port in {8000..8010}; do
    if check_port $port; then
        BACKEND_PORT=$port
        echo "✅ Backend Port gefunden: $port"
        break
    fi
done

# PostgreSQL Port (ab 5432)
POSTGRES_PORT=""
for port in {5432..5442}; do
    if check_port $port; then
        POSTGRES_PORT=$port
        echo "✅ PostgreSQL Port gefunden: $port"
        break
    fi
done

echo ""

# Prüfe ob alle Ports gefunden wurden
if [ -z "$FRONTEND_PORT" ] || [ -z "$BACKEND_PORT" ] || [ -z "$POSTGRES_PORT" ]; then
    echo "❌ Konnte nicht genug freie Ports finden!"
    echo ""
    echo "Gefundene Ports:"
    echo "  Frontend:  ${FRONTEND_PORT:-NICHT GEFUNDEN}"
    echo "  Backend:   ${BACKEND_PORT:-NICHT GEFUNDEN}"
    echo "  PostgreSQL: ${POSTGRES_PORT:-NICHT GEFUNDEN}"
    echo ""
    echo "Bitte wähle manuell freie Ports zwischen 3000-9999"
    exit 1
fi

echo "=========================================="
echo "Gefundene freie Ports:"
echo "  Frontend:   $FRONTEND_PORT"
echo "  Backend:    $BACKEND_PORT"
echo "  PostgreSQL: $POSTGRES_PORT"
echo "=========================================="
echo ""

# Stoppe alte Container
echo "Stoppe alte Container..."
docker-compose down 2>/dev/null || true
docker-compose -f docker-compose.nas.yml down 2>/dev/null || true

# Erstelle docker-compose.yml mit freien Ports
echo "Erstelle docker-compose.yml..."
cat > docker-compose.yml << EOF
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: training-analyzer-db
    environment:
      POSTGRES_USER: training_user
      POSTGRES_PASSWORD: training_pass
      POSTGRES_DB: training_analyzer
    ports:
      - "$POSTGRES_PORT:5432"
    volumes:
      - /volume1/docker/training-analyzer/postgres-data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U training_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: training-analyzer-backend
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgresql://training_user:training_pass@postgres:5432/training_analyzer
    ports:
      - "$BACKEND_PORT:8000"
    volumes:
      - /volume1/docker/training-analyzer/backend-data:/app/data
    depends_on:
      postgres:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: training-analyzer-frontend
    environment:
      - VITE_API_URL=http://192.168.68.52:$BACKEND_PORT
    ports:
      - "$FRONTEND_PORT:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    restart: unless-stopped

networks:
  default:
    name: training-analyzer-network
EOF

echo "✅ docker-compose.yml erstellt"
echo ""

# Update .env
if [ -f .env ]; then
    echo "Aktualisiere .env..."
    sed -i "s|ALLOWED_ORIGINS=.*|ALLOWED_ORIGINS=http://192.168.68.52:$FRONTEND_PORT,http://localhost:$FRONTEND_PORT|" .env
    echo "✅ .env aktualisiert"
else
    echo "⚠️  .env nicht gefunden - wird beim ersten Start erstellt"
fi

# Speichere Ports für Referenz
cat > PORTS.txt << EOF
Training Analyzer - Verwendete Ports
=====================================

Frontend:   http://192.168.68.52:$FRONTEND_PORT
Backend:    http://192.168.68.52:$BACKEND_PORT
API Docs:   http://192.168.68.52:$BACKEND_PORT/docs
PostgreSQL: localhost:$POSTGRES_PORT (nur intern)

Generiert: $(date)
EOF

echo ""
echo "Starte Container..."
docker-compose up -d --build

echo ""
echo "⏳ Warte auf Services..."
sleep 20

# Test Backend
echo "Teste Backend..."
if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
    echo "✅ Backend ist bereit!"
else
    echo "⚠️  Backend startet noch..."
    echo "   Prüfe später: curl http://localhost:$BACKEND_PORT/health"
fi

echo ""
echo "=========================================="
echo "✅ Setup abgeschlossen!"
echo "=========================================="
echo ""
echo "📱 Deine URLs:"
echo "   Frontend:  http://192.168.68.52:$FRONTEND_PORT"
echo "   Backend:   http://192.168.68.52:$BACKEND_PORT"
echo "   API Docs:  http://192.168.68.52:$BACKEND_PORT/docs"
echo ""
echo "💾 Ports gespeichert in: PORTS.txt"
echo ""
echo "🔧 Container-Status:"
docker-compose ps
echo ""
echo "📋 Logs ansehen:"
echo "   docker-compose logs -f"
echo ""
echo "🌐 Öffne jetzt im Browser:"
echo "   http://192.168.68.52:$FRONTEND_PORT"
echo ""
