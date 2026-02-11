#!/bin/bash
set -e

echo "🚀 Starting deployment..."
cd /volume1/docker/training-analyzer

echo "📥 Pulling latest code..."
su - NCSNASadmin -c "cd /volume1/docker/training-analyzer && git pull origin main 2>&1 | grep -v 'postgres-data'"

echo "🐳 Building and restarting containers..."
docker-compose up -d --build backend frontend

echo "✅ Deployment complete!"
docker-compose ps
