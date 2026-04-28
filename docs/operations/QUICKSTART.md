# ⚡ Quick Start Guide

## 🎯 Get Running in 5 Minutes

### Step 1: Prerequisites Check

```bash
# Check Docker
docker --version
docker-compose --version

# If not installed: https://docs.docker.com/get-docker/
```

### Step 2: Configure Environment

```bash
cd training-analyzer

# Copy example config
cp .env.example .env

# Edit with your settings
nano .env  # or use any text editor
```

**Minimum required:**
```bash
# For Claude AI (recommended)
CLAUDE_API_KEY=sk-ant-your-key-here

# OR for free self-hosted AI
OLLAMA_BASE_URL=http://localhost:11434
AI_PRIMARY_PROVIDER=ollama
```

### Step 3: Start Application

```bash
# Start everything
docker-compose up -d

# Wait ~30 seconds for services to start

# Check status
docker-compose ps
```

### Step 4: Setup Ollama (Optional - Free AI)

```bash
# Pull AI model
docker exec -it training-analyzer-ollama ollama pull llama3.1:8b

# Test it
curl http://localhost:11434/api/tags
```

### Step 5: Access Application

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## 🧪 Test the Setup

### 1. Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# Check AI providers
curl http://localhost:8000/api/v1/ai/providers
```

**Expected response:**
```json
{
  "primary": "Claude (claude-sonnet-4-20250514)",
  "available": ["claude", "ollama"],
  "status": {
    "Claude (...)": {"available": true, "is_primary": true},
    "Ollama (...)": {"available": true, "is_primary": false}
  }
}
```

### 2. Test AI Chat

```bash
curl -X POST http://localhost:8000/api/v1/ai/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hallo, kannst du mich hören?",
    "context": {}
  }'
```

### 3. Test Workout Upload

Open http://localhost:8000/docs and try the `/workouts/upload` endpoint with a CSV file.

---

## 🔧 Common Issues

### Issue: "Cannot connect to database"

**Solution:**
```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
# Wait 10 seconds
docker-compose up -d backend
```

### Issue: "Claude API key invalid"

**Solution:**
1. Check your API key at https://console.anthropic.com/
2. Update `.env` file
3. Restart: `docker-compose restart backend`

### Issue: "Ollama model not found"

**Solution:**
```bash
# Pull the model
docker exec -it training-analyzer-ollama ollama pull llama3.1:8b

# List available models
docker exec -it training-analyzer-ollama ollama list
```

### Issue: "Port 3000 already in use"

**Solution:**
```bash
# Change port in docker-compose.yml
# frontend:
#   ports:
#     - "3001:3000"  # Changed from 3000

docker-compose up -d
```

---

## 📱 First Steps After Setup

### 1. Upload Your First Workout

1. Export CSV from Apple Watch
2. Go to http://localhost:3000
3. Click "Upload Workout"
4. Select CSV file
5. View AI analysis

### 2. Configure Your Training Plan

1. Navigate to "Training Plan"
2. Paste your current plan (Markdown format)
3. Save

### 3. Chat with AI Trainer

1. Go to "AI Chat"
2. Ask: "Was sollte ich diese Woche trainieren?"
3. Get personalized advice

---

## 🎨 Customize Settings

### Change Primary AI Provider

Edit `.env`:
```bash
# Use Ollama (free) instead of Claude
AI_PRIMARY_PROVIDER=ollama
AI_FALLBACK_PROVIDERS=claude
```

Restart:
```bash
docker-compose restart backend
```

### Use Your Own Docling Server

Edit `.env`:
```bash
DOCLING_SERVER_URL=http://your-docling-server:5001
```

---

## 📊 View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100
```

---

## 🛑 Stop Application

```bash
# Stop (keep data)
docker-compose down

# Stop and remove all data
docker-compose down -v

# Stop specific service
docker-compose stop backend
```

---

## 🔄 Update Application

```bash
# Pull latest changes
git pull

# Rebuild containers
docker-compose down
docker-compose build
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head
```

---

## 🆘 Get Help

### Check Documentation
- Main README: [../README.md](../README.md)
- Development Guide: [DEVELOPMENT.md](./DEVELOPMENT.md)
- API Docs: http://localhost:8000/docs

### Debug Checklist

- [ ] All containers running? `docker-compose ps`
- [ ] Environment variables set? `cat .env`
- [ ] Database accessible? `docker-compose logs postgres`
- [ ] API responding? `curl http://localhost:8000/health`
- [ ] AI providers available? `curl http://localhost:8000/api/v1/ai/providers`

### Common Commands

```bash
# Restart everything
docker-compose restart

# View container status
docker-compose ps

# Execute command in container
docker-compose exec backend bash
docker-compose exec backend python

# Check resource usage
docker stats
```

---

## ✅ Next Steps

Once everything works:

1. **Read the Development Guide** - [DEVELOPMENT.md](./DEVELOPMENT.md)
2. **Explore API Documentation** - http://localhost:8000/docs
3. **Upload Real Workouts** - Start analyzing your training
4. **Customize** - Adapt to your needs
5. **Contribute** - Improve and extend

---

**🎉 You're all set! Happy training!**
