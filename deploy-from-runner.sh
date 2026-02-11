#!/bin/bash
set -e

echo "🚀 Starting deployment from runner..."

# Git safe directory
git config --global --add safe.directory /workspace/training-analyzer

# Git pull on host via docker exec
docker exec training-analyzer-backend bash -c "
  su - NCSNASadmin -c 'cd /volume1/docker/training-analyzer && git pull origin main 2>&1 | grep -v postgres-data' || true
"

# Docker compose rebuild
docker -H unix:///var/run/docker.sock exec training-analyzer-backend bash -c "
  cd /volume1/docker/training-analyzer && docker-compose up -d --build backend frontend
"

echo "✅ Deployment complete!"
docker ps | grep training-analyzer
