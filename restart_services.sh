#!/bin/bash
# MedFlow Service Restart Script
# This script exports environment variables from .env and restarts services

set -e

echo "🔄 Restarting MedFlow services with environment variables..."
echo ""

# Export environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ Loaded environment variables from .env"
    echo "   MEDGEMMA_REMOTE_URL: $MEDGEMMA_REMOTE_URL"
else
    echo "⚠️  Warning: .env file not found"
fi

echo ""
echo "🛑 Stopping services..."
docker compose down

echo ""
echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

echo ""
echo "📊 Service Status:"
docker compose ps

echo ""
echo "✅ Services restarted successfully!"
echo ""
echo "Access points:"
echo "  - Frontend:  http://localhost:5173"
echo "  - Backend:   http://localhost:8000"
echo "  - API Docs:  http://localhost:8000/api/v1/docs"
echo ""
