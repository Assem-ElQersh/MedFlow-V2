#!/bin/bash
# MedFlow First-Time Setup Script
# This script sets up MedFlow from scratch

set -e

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                    MedFlow - First Time Setup                                ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is installed
echo "🔍 Step 1: Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo "❌ ERROR: Docker is not installed!"
    echo ""
    echo "Please install Docker first:"
    echo "  https://docs.docker.com/engine/install/"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "❌ ERROR: Docker Compose is not available!"
    echo ""
    echo "Please install Docker Compose or update Docker to a version with Compose built-in"
    exit 1
fi

echo "✅ Docker is installed: $(docker --version)"
echo "✅ Docker Compose is available: $(docker compose version)"
echo ""

# Check if .env file exists, if not create from .env.example
echo "🔍 Step 2: Setting up environment variables..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "📝 Creating .env file from .env.example..."
        cp .env.example .env
        echo "✅ .env file created"
        echo ""
        echo "⚠️  IMPORTANT: You need to add your MedGemma service URL!"
        echo "   Edit .env file and set: MEDGEMMA_REMOTE_URL=https://your-ngrok-url"
        echo ""
        read -p "Press Enter to continue (you can add it later)..."
    else
        echo "📝 Creating .env file..."
        echo "MEDGEMMA_REMOTE_URL=" > .env
        echo "✅ .env file created"
        echo ""
        echo "⚠️  IMPORTANT: You need to add your MedGemma service URL later!"
        echo "   Edit .env file and set: MEDGEMMA_REMOTE_URL=https://your-ngrok-url"
        echo ""
    fi
else
    echo "✅ .env file already exists"
    
    # Check if MEDGEMMA_REMOTE_URL is set
    if grep -q "MEDGEMMA_REMOTE_URL=.*http" .env; then
        echo "✅ MEDGEMMA_REMOTE_URL is configured"
    else
        echo "⚠️  Warning: MEDGEMMA_REMOTE_URL is not set in .env"
        echo "   You'll need to set this up for AI features to work"
    fi
fi
echo ""

# Clean up any existing containers
echo "🧹 Step 3: Cleaning up any existing containers..."
docker compose down --remove-orphans 2>/dev/null || true
echo "✅ Cleanup complete"
echo ""

# Build and start services
echo "🚀 Step 4: Building and starting services (this may take 2-5 minutes)..."
echo "   This will download Docker images and build containers..."
echo ""

# Export env vars if .env exists
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs) 2>/dev/null || true
fi

if docker compose up -d --build; then
    echo ""
    echo "✅ Services started successfully!"
else
    echo ""
    echo "❌ ERROR: Failed to start services"
    echo "   Check the error messages above"
    exit 1
fi
echo ""

# Wait for services to be ready
echo "⏳ Step 5: Waiting for services to be ready..."
sleep 8
echo ""

# Check service status
echo "📊 Step 6: Checking service status..."
docker compose ps
echo ""

# Initialize database
echo "🗄️  Step 7: Initializing database with default users..."
echo "   This creates admin, doctor, and nurse accounts..."
echo ""

if docker compose exec -T backend python scripts/init_db.py; then
    echo ""
    echo "✅ Database initialized successfully!"
else
    echo ""
    echo "⚠️  Warning: Database initialization might have failed"
    echo "   You can try manually: docker compose exec backend python scripts/init_db.py"
fi
echo ""

# Final status
echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║                        🎉 Setup Complete!                                    ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📍 Access Points:"
echo "   • Frontend:  http://localhost:5173"
echo "   • Backend:   http://localhost:8000"
echo "   • API Docs:  http://localhost:8000/api/v1/docs"
echo ""
echo "🔑 Default Login Credentials:"
echo "   • Admin:   username: admin    password: admin123"
echo "   • Doctor:  username: doctor1  password: doctor123"
echo "   • Nurse:   username: nurse1   password: nurse123"
echo ""

# Check if MEDGEMMA_REMOTE_URL is set
if ! grep -q "MEDGEMMA_REMOTE_URL=.*http" .env 2>/dev/null; then
    echo "⚠️  Next Step: Set up MedGemma AI"
    echo "   1. Follow the setup guide in README.md (MedGemma Integration Setup)"
    echo "   2. Get your ngrok URL from Google Colab"
    echo "   3. Add it to .env: MEDGEMMA_REMOTE_URL=https://your-url"
    echo "   4. Restart services: ./restart_services.sh"
    echo ""
fi

echo "📖 Documentation:"
echo "   • Full guide: README.md"
echo "   • Test AI connection: python test_medgemma_connection.py <url>"
echo ""
echo "🛠️  Useful Commands:"
echo "   • View logs:     docker compose logs -f"
echo "   • Stop services: docker compose down"
echo "   • Restart:       ./restart_services.sh"
echo ""
echo "✨ You're all set! Open http://localhost:5173 to get started!"
echo ""
