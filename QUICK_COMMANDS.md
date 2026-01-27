# MedFlow - Quick Command Reference

## 🚀 Starting & Stopping

```bash
# START the system
cd ~/Desktop/MedFlow/MedFlow-V2
docker compose up -d

# STOP the system (keeps data)
docker compose down

# STOP and remove ALL data (fresh start)
docker compose down -v
```

---

## 📊 Status & Monitoring

```bash
# Check if services are running
docker compose ps

# View all logs (like your 4 terminals combined)
docker compose logs -f

# View specific service logs
docker compose logs -f backend      # Backend API
docker compose logs -f frontend     # React app
docker compose logs -f celery-worker # Background tasks
docker compose logs -f mongodb      # Database
docker compose logs -f redis        # Cache/Queue

# See last 50 lines of logs
docker compose logs --tail=50 backend
```

---

## 🔄 Restarting Services

```bash
# Restart ALL services
docker compose restart

# Restart ONE service
docker compose restart backend
docker compose restart frontend
docker compose restart celery-worker

# Rebuild and restart (after code changes)
docker compose up -d --build backend
```

---

## 🧪 Testing

```bash
# Test backend health
curl http://localhost:8000/health

# Access URLs
# Frontend:    http://localhost:5173
# API Docs:    http://localhost:8000/api/v1/docs
# Backend:     http://localhost:8000
```

---

## 🔧 Maintenance

```bash
# Initialize database with sample users
docker compose exec backend python scripts/init_db.py

# Access backend container shell
docker compose exec backend bash

# Access frontend container shell
docker compose exec frontend sh

# Access MongoDB shell
docker compose exec mongodb mongosh medflow
```

---

## 🐛 Troubleshooting

```bash
# If "port already in use" error:
sudo pkill -9 docker-proxy
docker compose down --remove-orphans
docker rm -f $(docker ps -aq) 2>/dev/null || true
sudo systemctl restart docker
docker compose up -d

# View container resource usage
docker stats

# Remove all stopped containers
docker container prune -f

# Remove unused networks
docker network prune -f

# Remove unused images
docker image prune -f
```

---

## 📦 Complete Cleanup (Nuclear Option)

```bash
# WARNING: This removes EVERYTHING including data!
docker compose down -v           # Stop and remove volumes
docker system prune -a --volumes # Remove all Docker data

# Then rebuild from scratch:
docker compose up -d --build
docker compose exec backend python scripts/init_db.py
```

---

## 🔑 Login Credentials

| Role   | Username | Password  |
|--------|----------|-----------|
| Admin  | admin    | admin123  |
| Doctor | doctor1  | doctor123 |
| Nurse  | nurse1   | nurse123  |

---

## 📁 File Locations

- **Project**: `~/Desktop/MedFlow/MedFlow-V2/`
- **Backend Code**: `~/Desktop/MedFlow/MedFlow-V2/backend/`
- **Frontend Code**: `~/Desktop/MedFlow/MedFlow-V2/frontend/`
- **Docker Config**: `~/Desktop/MedFlow/MedFlow-V2/docker-compose.yml`

---

## 💡 Daily Workflow

### Morning (Start Work)
```bash
cd ~/Desktop/MedFlow/MedFlow-V2
docker compose up -d
```

### During Development
- Edit code in `backend/` or `frontend/src/`
- Changes reload automatically
- View logs: `docker compose logs -f`

### Evening (Optional - can leave running)
```bash
docker compose down
```

---

## ⚡ Keyboard Shortcuts

When viewing logs with `docker compose logs -f`:
- **Ctrl + C** = Stop viewing logs (services keep running)
- **Ctrl + Z** = Pause (not recommended)

---

## 🆘 Emergency Commands

```bash
# If everything is broken:
docker compose down -v
sudo systemctl restart docker
docker compose up -d --build
docker compose exec backend python scripts/init_db.py

# Check what ports are in use:
sudo lsof -i :5173  # Frontend
sudo lsof -i :8000  # Backend
sudo lsof -i :27017 # MongoDB
sudo lsof -i :6379  # Redis

# Kill process on specific port:
sudo fuser -k 8000/tcp
```

---

## 📊 System Requirements

- **Docker**: v20.10+
- **Docker Compose**: v2.0+ (built into Docker)
- **Disk Space**: ~2GB for images
- **RAM**: 2GB minimum, 4GB recommended
- **Ports Required**: 5173, 8000, 27017, 6379

---

## 🎯 Performance Tips

```bash
# View resource usage
docker stats

# Limit container resources (in docker-compose.yml)
# Example:
# deploy:
#   resources:
#     limits:
#       cpus: '0.5'
#       memory: 512M

# Clean up unused resources
docker system prune -f
```

---

## 📝 Notes

- Services run in **background** (detached mode with `-d`)
- **Data persists** between restarts (MongoDB volume)
- **Hot reload** enabled for development
- **Logs** are preserved until containers are removed
- Containers auto-restart unless you stop them with `docker compose down`

---

## 🔗 Useful Links

- Docker Compose Docs: https://docs.docker.com/compose/
- FastAPI Docs: https://fastapi.tiangolo.com/
- React Docs: https://react.dev/
- MongoDB Docs: https://www.mongodb.com/docs/
