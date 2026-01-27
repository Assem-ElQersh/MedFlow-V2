# MedFlow - Running Successfully! ✓

## Container Status
All 5 containers are running:
- ✓ `medflow-mongodb` (MongoDB Database)
- ✓ `medflow-redis` (Redis Cache)
- ✓ `medflow-backend` (FastAPI Backend)
- ✓ `medflow-celery-worker` (Background Tasks)
- ✓ `medflow-frontend` (React Frontend)

## Access URLs
- **Frontend Application**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/api/v1/docs
- **API Documentation (ReDoc)**: http://localhost:8000/api/v1/redoc
- **MongoDB**: mongodb://localhost:27017
- **Redis**: redis://localhost:6379

## Default Login Credentials

| Role   | Username | Password   |
|--------|----------|------------|
| Admin  | admin    | admin123   |
| Doctor | doctor1  | doctor123  |
| Doctor | doctor2  | doctor123  |
| Nurse  | nurse1   | nurse123   |

## Quick Commands

```bash
# View logs (all services)
docker compose logs -f

# View logs (specific service)
docker compose logs -f backend
docker compose logs -f frontend

# Stop all services
docker compose down

# Stop and remove all data
docker compose down -v

# Restart services
docker compose restart

# Rebuild and restart
docker compose up -d --build

# Check container status
docker compose ps

# Execute command in backend container
docker compose exec backend python scripts/init_db.py
```

## Troubleshooting

### Port Conflicts
If you see "address already in use" errors:
```bash
# Kill orphaned docker-proxy processes
sudo pkill -9 docker-proxy

# Remove all containers
docker compose down --remove-orphans
docker rm -f $(docker ps -aq) 2>/dev/null || true

# Restart Docker
sudo systemctl restart docker

# Start services
docker compose up -d
```

### Container Won't Start
```bash
# Check logs for errors
docker compose logs [service-name]

# Rebuild specific service
docker compose up -d --build [service-name]
```

### Database Connection Issues
```bash
# Check MongoDB is running
docker compose ps mongodb

# Reinitialize database
docker compose exec backend python scripts/init_db.py
```

## System Architecture

### Backend (FastAPI)
- Port: 8000
- Auto-reload: Enabled (development mode)
- Database: MongoDB (motor async driver)
- Cache: Redis
- Background tasks: Celery

### Frontend (React + Vite)
- Port: 5173
- Hot reload: Enabled
- Build tool: Vite
- UI Framework: Material-UI v5

### Database (MongoDB)
- Port: 27017
- Version: 7.0
- Database name: medflow
- Persistent storage: Docker volume `medflow-v2_mongodb_data`

### Cache/Queue (Redis)
- Port: 6379
- Version: 7-alpine
- Used for: Celery task queue

### Background Worker (Celery)
- Tasks: VLM processing, async operations
- Broker: Redis
- Backend: Redis

## Project Structure
```
MedFlow-V2/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/v1/      # API endpoints
│   │   ├── core/        # Config, database, security
│   │   ├── models/      # Pydantic models
│   │   ├── services/    # Business logic
│   │   └── tasks/       # Celery tasks
│   ├── scripts/         # Utility scripts
│   └── requirements.txt
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/ # Reusable components
│   │   ├── pages/      # Page components
│   │   ├── services/   # API services
│   │   └── types/      # TypeScript types
│   └── package.json
├── docker-compose.yml   # Container orchestration
└── start.sh            # Startup script
```

## Features Overview

### Patient Management
- Complete CRUD operations
- Medical history tracking
- Search by name, phone, or national ID
- Patient portfolio view with all sessions

### Session Management
- Create medical sessions
- Upload files (X-rays, CT scans, lab results)
- VLM-powered initial analysis
- Doctor review workflow
- Diagnosis and prescription management

### Role-Based Access
- **Nurse**: Create patients, create sessions, upload files
- **Doctor**: Review sessions, chat with VLM, submit diagnoses
- **Admin**: Full system access, user management

### AI Integration
- MedGemma VLM for medical analysis
- Initial session processing
- Doctor-VLM chat interface
- Automated findings and recommendations

## Development Workflow

### Making Changes to Backend
1. Edit files in `./backend/`
2. Backend auto-reloads (Uvicorn watch mode)
3. Check logs: `docker compose logs -f backend`

### Making Changes to Frontend
1. Edit files in `./frontend/src/`
2. Vite hot-reloads changes automatically
3. Check logs: `docker compose logs -f frontend`

### Adding Python Dependencies
1. Add package to `backend/requirements.txt`
2. Rebuild: `docker compose up -d --build backend celery-worker`

### Adding NPM Dependencies
1. Add package to `frontend/package.json`
2. Rebuild: `docker compose up -d --build frontend`

## Next Steps
1. Open http://localhost:5173 in your browser
2. Login with one of the default credentials
3. Explore the application features
4. Review the API documentation at http://localhost:8000/api/v1/docs

## Notes
- All containers use Docker volumes for persistence
- MongoDB data persists in `medflow-v2_mongodb_data` volume
- Backend and frontend code is mounted for live development
- The system is configured for development (DEBUG=True)
- For production deployment, see README.md security checklist
