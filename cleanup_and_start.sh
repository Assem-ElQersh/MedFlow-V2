#!/bin/bash
# MedFlow Docker Cleanup and Startup Script

echo "=== MedFlow Docker Cleanup and Startup ==="
echo ""

# Stop all containers
echo "1. Stopping all Docker Compose services..."
docker compose down --remove-orphans 2>/dev/null || true

# Remove all containers
echo "2. Removing all containers..."
docker rm -f $(docker ps -aq) 2>/dev/null || true

# Kill orphaned docker-proxy processes
echo "3. Killing orphaned docker-proxy processes..."
sudo pkill -9 docker-proxy 2>/dev/null || true

# Wait a moment for ports to be released
echo "4. Waiting for ports to be released..."
sleep 2

# Restart Docker to ensure clean state
echo "5. Restarting Docker daemon..."
sudo systemctl restart docker

# Wait for Docker to be ready
echo "6. Waiting for Docker to be ready..."
sleep 3

# Start Docker Compose services
echo "7. Starting Docker Compose services..."
docker compose up -d

# Check status
echo ""
echo "=== Container Status ==="
docker compose ps

echo ""
echo "=== Checking logs for any errors ==="
sleep 2
docker compose logs --tail=20

echo ""
echo "=== Done! ==="
echo "Services should be running at:"
echo "  - Frontend: http://localhost:5173"
echo "  - Backend API: http://localhost:8000"
echo "  - MongoDB: localhost:27017"
echo "  - Redis: localhost:6379"
