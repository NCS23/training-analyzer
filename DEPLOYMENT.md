# Deployment Workflow

## Infrastruktur

| Service | Hosting | URL |
|---------|---------|-----|
| Training Analyzer | Hetzner VPS via Coolify | http://training.89.167.78.223.sslip.io |
| Backend API | Hetzner VPS via Coolify | http://training.89.167.78.223.sslip.io/api |
| API Docs | Hetzner VPS via Coolify | http://training.89.167.78.223.sslip.io/docs |

## Automatisches Deployment

Coolify ueberwacht den `main` Branch auf GitHub und deployed automatisch bei jedem Push:

1. Push auf `main`
2. GitHub Actions CI laeuft (Lint, Tests, Build)
3. Coolify erkennt neuen Commit und baut Docker-Container neu
4. Zero-Downtime Deployment

## Manuelles Deployment

Falls noetig, kann ein Deployment manuell ueber die Coolify API getriggert werden:

```bash
curl -s -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  "http://89.167.78.223:8000/api/v1/deploy?uuid=cc4w4kos8wkwg4c0cgkoow0c&force=false"
```

## CI/CD

- **CI Pipeline:** GitHub Actions (`.github/workflows/ci.yml`)
- **Jobs:** frontend-lint, frontend-test, frontend-build, backend-lint, backend-test
- **Runner:** GitHub Hosted (ubuntu-latest)

## Docker

Die App laeuft als Docker Compose Stack mit:
- **Frontend:** React + Nginx
- **Backend:** FastAPI + Uvicorn
- **Database:** PostgreSQL 15
