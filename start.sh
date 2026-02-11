#!/bin/bash
# Training Analyzer - Smart Startup Script
# Checks prerequisites and starts the application

set -e

echo "🏃‍♂️ Training Analyzer - Smart Startup"
echo "======================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker found"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found${NC}"
    echo "Please install Docker Compose"
    exit 1
fi
echo -e "${GREEN}✓${NC} Docker Compose found"

# Check .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  No .env file found${NC}"
    echo "Creating from template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env with your API keys!${NC}"
    echo "Edit: nano .env"
    echo ""
    read -p "Press Enter after editing .env file..."
fi
echo -e "${GREEN}✓${NC} .env file exists"

# Check if services are already running
if docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}⚠️  Services already running${NC}"
    read -p "Restart services? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping services..."
        docker-compose down
    else
        echo "Keeping existing services running"
        exit 0
    fi
fi

# Start services
echo ""
echo "🚀 Starting services..."
echo ""

docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
echo ""

# Wait for backend
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Backend is healthy"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for backend... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo -e "${RED}❌ Backend failed to start${NC}"
    echo "Check logs: docker-compose logs backend"
    exit 1
fi

# Check AI providers
echo ""
echo "🤖 Checking AI providers..."
PROVIDERS=$(curl -s http://localhost:8000/api/v1/ai/providers)

if echo "$PROVIDERS" | grep -q "available"; then
    ACTIVE=$(echo "$PROVIDERS" | grep -o '"primary":"[^"]*' | cut -d'"' -f4)
    if [ ! -z "$ACTIVE" ]; then
        echo -e "${GREEN}✓${NC} Active AI provider: $ACTIVE"
    else
        echo -e "${YELLOW}⚠️  No AI provider available${NC}"
        echo "Configure AI in .env file"
    fi
else
    echo -e "${YELLOW}⚠️  Could not check AI providers${NC}"
fi

# Print status
echo ""
echo "======================================"
echo -e "${GREEN}✅ Training Analyzer is running!${NC}"
echo "======================================"
echo ""
echo "📱 Access Points:"
echo "   Frontend:  http://localhost:3000"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Health:    http://localhost:8000/health"
echo ""
echo "📋 Useful Commands:"
echo "   View logs:   docker-compose logs -f"
echo "   Stop:        docker-compose down"
echo "   Restart:     docker-compose restart"
echo ""
echo "📚 Documentation:"
echo "   Quick Start: docs/QUICKSTART.md"
echo "   Development: docs/DEVELOPMENT.md"
echo ""

# Optional: Setup Ollama if not configured
if [ -z "$CLAUDE_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}💡 Tip: No cloud AI configured${NC}"
    echo "   Want to use free self-hosted AI?"
    echo "   Run: docker exec -it training-analyzer-ollama ollama pull llama3.1:8b"
    echo ""
fi

echo "🎉 Ready to analyze your training!"
echo ""
