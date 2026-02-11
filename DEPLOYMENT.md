# 🚀 Deployment Workflow

## Automatisches Deployment

Bei jedem `git push` auf `main`:
1. Gitea Webhook triggert → `http://192.168.68.52:9000/deploy`
2. Webhook Server führt aus → `/volume1/docker/training-analyzer/webhook-deploy.sh`
3. Script macht:
   - Git pull
   - Docker rebuild (backend + frontend)
   - Containers neu starten

## Manuelles Deployment
```bash
/volume1/docker/training-analyzer/webhook-deploy.sh
```

## Webhook Server

- **Port:** 9000
- **Script:** `/volume1/docker/training-analyzer/webhook-server.py`
- **Logs:** `/volume1/docker/training-analyzer/webhook.log`

### Webhook Server neustarten:
```bash
pkill -f webhook-server.py
nohup python3 /volume1/docker/training-analyzer/webhook-server.py > /volume1/docker/training-analyzer/webhook.log 2>&1 &
```

## Gitea Actions (deaktiviert)

Gitea Actions wurde durch Webhook ersetzt (zu komplex mit Docker Socket).
