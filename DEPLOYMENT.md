# Deployment Workflow

## Automatisches Deployment via GitHub Actions

Bei jedem `git push` auf `main`:
1. CI Pipeline laeuft (Lint, Tests, Build)
2. Nach Erfolg: Deploy-Job synct Code nach `/volume1/docker/training-analyzer/`
3. `docker-compose up -d --build backend frontend` startet die Container neu

## Manuelles Deployment

```bash
ssh -p 47 admin@192.168.68.52
cd /volume1/docker/training-analyzer
git pull origin main
docker-compose up -d --build backend frontend
```

## Runner-Konfiguration (Voraussetzung)

> **Hinweis:** Die CI/CD wurde von Gitea Actions nach GitHub Actions migriert.
> Die folgende Runner-Konfiguration bezieht sich auf das fruehere Self-Hosted-Setup auf dem NAS.

Der act_runner auf dem NAS braucht Docker Socket + Projektverzeichnis-Zugriff.
In der Runner-Config (`config.yaml`) muessen diese Volumes gemountet sein:

```yaml
container:
  options: >-
    -v /var/run/docker.sock:/var/run/docker.sock
    -v /volume1/docker/training-analyzer:/volume1/docker/training-analyzer
  valid_volumes:
    - /var/run/docker.sock
    - /volume1/docker
```

Nach Aenderung: Runner neu starten.

## Ports

| Service    | Port |
|------------|------|
| Frontend   | 3002 |
| Backend    | 8001 |
| PostgreSQL | 5433 |

## URLs

- **Frontend:** http://192.168.68.52:3002
- **Backend API:** http://192.168.68.52:8001
- **API Docs:** http://192.168.68.52:8001/docs
