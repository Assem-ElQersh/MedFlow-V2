# MedFlow Quick Start Guide

## 🚀 Starting the System

### One Command to Start Everything:
```bash
cd ~/Desktop/MedFlow/MedFlow-V2
docker compose up -d
```

This replaces all your previous manual steps:
- ~~Terminal 1: `docker start medflow-mongodb`~~
- ~~Terminal 2: `python -m uvicorn app.main:app --reload --port 8000`~~
- ~~Terminal 3: `celery -A celery_app worker --loglevel=info --pool=solo`~~
- ~~Terminal 4: `npm run dev`~~

**All of these now run automatically in containers!**

---

## 📊 Checking Status

```bash
# Quick status check
docker compose ps

# Expected output: All containers should show "Up"
# NAME                    STATUS
# medflow-mongodb         Up
# medflow-redis           Up
# medflow-backend         Up
# medflow-celery-worker   Up
# medflow-frontend        Up
```

---

## 🔍 Viewing Logs (Equivalent to watching your terminals)

### View All Logs (like having all 4 terminals open):
```bash
docker compose logs -f
```

### View Specific Service Logs:
```bash
# Backend logs (Terminal 2 equivalent)
docker compose logs -f backend

# Celery worker logs (Terminal 3 equivalent)
docker compose logs -f celery-worker

# Frontend logs (Terminal 4 equivalent)
docker compose logs -f frontend

# MongoDB logs (Terminal 1 equivalent)
docker compose logs -f mongodb
```

Press `Ctrl+C` to stop following logs

---

## 🧪 Testing the System

### 1. Check Backend Health
```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","project":"MedFlow"}
```

### 2. Check Backend API Documentation
Open in browser: http://localhost:8000/api/v1/docs

### 3. Check Frontend
Open in browser: http://localhost:5173

### 4. Test Login
1. Go to http://localhost:5173
2. Login with:
   - Username: `admin`
   - Password: `admin123`

---

## 🛑 Stopping the System

```bash
# Stop all services (keeps data)
docker compose down

# Stop and remove all data (fresh start)
docker compose down -v
```

---

## 🔄 Restarting Services

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart backend
docker compose restart frontend
```

---

## 🐛 Troubleshooting

### "Port already in use" Error
```bash
# Kill orphaned processes
sudo pkill -9 docker-proxy

# Clean up and restart
docker compose down --remove-orphans
docker rm -f $(docker ps -aq) 2>/dev/null || true
sudo systemctl restart docker
docker compose up -d
```

### Service Not Starting
```bash
# Check logs for errors
docker compose logs [service-name]

# Rebuild and restart
docker compose up -d --build [service-name]
```

### Database Issues
```bash
# Reinitialize database
docker compose exec backend python scripts/init_db.py
```

---

## 📝 Making Code Changes

### Backend Changes (Python):
1. Edit files in `backend/`
2. Backend auto-reloads (like `--reload` flag in uvicorn)
3. Watch logs: `docker compose logs -f backend`

### Frontend Changes (React/TypeScript):
1. Edit files in `frontend/src/`
2. Frontend auto-reloads (like `npm run dev`)
3. Watch logs: `docker compose logs -f frontend`

### Need to Install New Dependencies?

**Backend (Python):**
```bash
# 1. Add package to backend/requirements.txt
# 2. Rebuild backend containers
docker compose up -d --build backend celery-worker
```

**Frontend (NPM):**
```bash
# 1. Add package to frontend/package.json
# 2. Rebuild frontend container
docker compose up -d --build frontend
```

---

## 🎯 Quick Reference

| Task | Old Way (Manual) | New Way (Docker Compose) |
|------|------------------|--------------------------|
| Start all services | 4 separate terminal commands | `docker compose up -d` |
| View logs | Look at each terminal | `docker compose logs -f` |
| Stop services | Ctrl+C in each terminal + stop MongoDB | `docker compose down` |
| Restart backend | Kill python process, restart | `docker compose restart backend` |
| Check status | Look at each terminal | `docker compose ps` |
| Activate conda env | `conda activate medflow` | Not needed (runs in containers) |

---

## 🌟 Benefits of Docker Compose

✅ **One command** to start everything  
✅ **No conda environments** needed  
✅ **Consistent** across different machines  
✅ **Isolated** - doesn't affect your system  
✅ **Easy cleanup** - remove everything with one command  
✅ **Production-ready** - same setup works in production  

---

## 🚦 Daily Workflow

### Morning - Start Work
```bash
cd ~/Desktop/MedFlow/MedFlow-V2
docker compose up -d
```

### During Development
- Edit code in `backend/` or `frontend/src/`
- Changes auto-reload
- View logs: `docker compose logs -f`

### End of Day - Stop Services (Optional)
```bash
docker compose down
```

**Note:** You can leave services running if you want. They use minimal resources when idle.

---

## 📱 Access Points

- **Frontend**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/api/v1/docs
- **Backend Health**: http://localhost:8000/health

## 🔑 Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | admin123 |
| Doctor | doctor1 | doctor123 |
| Nurse | nurse1 | nurse123 |

---

## Need the Old Manual Way?

If you ever need to run services manually (not recommended), you can still do it:

1. **Stop Docker containers**: `docker compose down`
2. **Start MongoDB**: `docker start medflow-mongodb` (or use Docker Compose for just MongoDB)
3. **Backend**: Use your conda environment as before
4. **Frontend**: Use npm as before

But Docker Compose is **much easier** and the recommended approach! 🎉
