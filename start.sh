#!/bin/bash
# MedFlow Startup Script - Handles docker-proxy cleanup

set -e

echo "=========================================="
echo "  MedFlow Docker Startup Script"
echo "=========================================="
echo ""

# Function to kill docker-proxy processes
cleanup_docker_proxy() {
    echo "Cleaning up orphaned docker-proxy processes..."
    sudo pkill -9 docker-proxy 2>/dev/null || true
    sleep 1
}

# Function to check if port is in use
check_port() {
    local port=$1
    if ss -tlnp | grep -q ":$port "; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Step 1: Stop and clean up
echo "Step 1: Stopping and cleaning up containers..."
docker compose down --remove-orphans 2>/dev/null || true
docker container prune -f >/dev/null 2>&1
cleanup_docker_proxy

# Step 2: Restart Docker daemon
echo "Step 2: Restarting Docker daemon..."
sudo systemctl restart docker
sleep 3

# Step 3: Start services
echo "Step 3: Starting services..."
echo ""

# Start services
if docker compose up -d; then
    echo ""
    echo "✓ Services started successfully!"
else
    echo ""
    echo "✗ Failed to start services. Retrying after cleanup..."
    cleanup_docker_proxy
    sleep 2
    docker compose up -d
fi

# Step 4: Wait for services to be ready
echo ""
echo "Step 4: Waiting for services to be ready..."
sleep 5

# Step 5: Check status
echo ""
echo "=========================================="
echo "  Container Status"
echo "=========================================="
docker compose ps

# Step 6: Show service URLs
echo ""
echo "=========================================="
echo "  Service URLs"
echo "=========================================="
echo "  Frontend:    http://localhost:5173"
echo "  Backend API: http://localhost:8000/api/v1/docs"
echo "  MongoDB:     mongodb://localhost:27017"
echo "  Redis:       redis://localhost:6379"
echo ""
echo "=========================================="
echo ""

# Check if containers are running
running_count=$(docker compose ps --status running | grep -c "Up" || echo "0")

if [ "$running_count" -eq "5" ]; then
    echo "✓ All 5 containers are running!"
    echo ""
    echo "Next step: Initialize the database with sample users"
    echo "Run: docker compose exec backend python scripts/init_db.py"
else
    echo "⚠ Warning: Only $running_count/5 containers are running"
    echo ""
    echo "Check logs with: docker compose logs"
fi

echo ""
