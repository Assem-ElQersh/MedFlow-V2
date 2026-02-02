# MedFlow - AI-Powered Medical Patient Management System

A comprehensive medical patient management system with AI-powered diagnostic assistance using Google's MedGemma Vision Language Model.

## Overview

MedFlow is a web-based hospital management system designed for chest disease diagnosis and patient care. It features patient registration, session-based visit tracking, real AI-assisted diagnosis powered by MedGemma, and comprehensive medical record management with complete audit trails.

## Key Features

- **Patient Management**: Complete CRUD operations with comprehensive medical history
- **Session Workflow**: Create and manage medical sessions with file uploads (X-rays, CT scans, lab results)
- **Real AI Integration**: Google MedGemma for intelligent medical analysis and findings
- **Doctor-AI Chat**: Interactive consultation interface for additional diagnostic insights
- **Role-Based Access**: Nurse, Doctor, and Admin roles with specific permissions
- **Audit Trail**: Complete tracking of all changes with immutable medical records
- **Follow-up System**: Automatic follow-up session creation for pending tests

## Technology Stack

**Backend:**
- FastAPI (Python async web framework)
- MongoDB with Motor (async driver)
- Celery + Redis (background task processing)
- Pydantic v2 (data validation)
- JWT authentication

**Frontend:**
- React 18 with TypeScript
- Vite (build tool)
- Material-UI v5
- React Router v6
- React Query (data fetching/caching)

**AI Model:**
- Google MedGemma 1.5-4b-it (Medical Vision Language Model)
- Running on Google Colab with GPU
- Exposed via ngrok for remote access

**Infrastructure:**
- Docker & Docker Compose
- MongoDB 7.0
- Redis 7

---

## Quick Start (5 Minutes)

### Prerequisites
- Docker and Docker Compose installed
- Google Account (for Colab - optional for now)
- Hugging Face Account (for MedGemma access - optional for now)
- ngrok Account (free tier - optional for now)

### Option A: First-Time Setup (Recommended for New Users)

Run the automated setup script:

```bash
cd ~/Desktop/MedFlow/MedFlow-V2
./setup.sh
```

This script will:
- ✅ Check if Docker is installed
- ✅ Create .env file if needed
- ✅ Build and start all containers
- ✅ Initialize database with default users
- ✅ Show you next steps

**That's it!** The script handles everything automatically.

### Option B: Manual Setup

If you prefer manual control:

**1. Start MedFlow Services**

```bash
cd ~/Desktop/MedFlow/MedFlow-V2
docker compose up -d
```

This starts all services:
- MongoDB (database)
- Redis (task queue)
- Backend API
- Celery worker (background tasks)
- Frontend (React app)

**2. Initialize Database**

```bash
docker compose exec backend python scripts/init_db.py
```

### 3. Set Up MedGemma AI (Required for Real Analysis)

See [MedGemma Integration Setup](#medgemma-integration-setup) section below.

### 4. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/api/v1/docs
- **Backend Health**: http://localhost:8000/health

### 5. Login with Default Credentials

| Role   | Username | Password  |
|--------|----------|-----------|
| Admin  | admin    | admin123  |
| Doctor | doctor1  | doctor123 |
| Nurse  | nurse1   | nurse123  |

---

## MedGemma Integration Setup

The system uses Google's MedGemma AI model running on Google Colab for real medical analysis.

### Step 1: Get Required Tokens

#### 1.1 Hugging Face Token
1. Go to https://huggingface.co/ and sign up/login
2. Request access to MedGemma: https://huggingface.co/google/medgemma-1.5-4b-it
3. Wait for approval (usually instant)
4. Get your token: https://huggingface.co/settings/tokens
5. Click "New token" → Copy it: `hf_xxxxxxxxxxxxxxxxxxxxx`

#### 1.2 ngrok Auth Token
1. Go to https://ngrok.com/ and sign up/login
2. Get your token: https://dashboard.ngrok.com/get-started/your-authtoken
3. Copy it: `2xxxxxxxxxxxxx_xxxxxxxxxxxxxxxxxxx`

### Step 2: Set Up Google Colab

#### 2.1 Choose Your Notebook Version

**For Colab Pro+ Users:**
- Use `MedGemma_Colab_Service_Pro.ipynb` (optimized for 24h runtime)

**For Free/Pro Users:**
- Use `MedGemma_Colab_Service.ipynb` (standard version)

#### 2.2 Upload and Configure

1. Go to https://colab.research.google.com/
2. **File** → **Upload notebook** → Select the notebook file
3. **Runtime** → **Change runtime type**:
   - **Runtime type**: Python 3
   - **Hardware accelerator**: **T4 GPU** ✅
   - **High-RAM**: **OFF** ❌ (Not needed, saves compute units)
4. In the second cell, add your tokens:
   ```python
   HF_TOKEN = "hf_YOUR_HUGGINGFACE_TOKEN_HERE"
   NGROK_TOKEN = "YOUR_NGROK_TOKEN_HERE"
   ```

#### 2.3 Run the Notebook

1. **Runtime** → **Run all**
2. Wait 2-3 minutes for model to load
3. **Copy the ngrok URL** from the output:
   ```
   PUBLIC URL: https://xxxx-xx-xxx-xxx-xx.ngrok-free.app
   ```

### Step 3: Configure MedFlow

#### 3.1 Set Environment Variable

Create or edit `.env` file:

```bash
cd ~/Desktop/MedFlow/MedFlow-V2
nano .env
```

Add this line (replace with your actual ngrok URL):

```env
MEDGEMMA_REMOTE_URL=https://xxxx-xx-xxx-xxx-xx.ngrok-free.app
```

Save and exit (Ctrl+X, then Y, then Enter)

#### 3.2 Restart Services

```bash
./restart_services.sh
```

Or manually:

```bash
export MEDGEMMA_REMOTE_URL=https://xxxx-xx-xxx-xxx-xx.ngrok-free.app
docker compose restart backend celery-worker
```

#### 3.3 Test Connection

```bash
python test_medgemma_connection.py https://your-ngrok-url.app
```

You should see:
```
✅ Health check passed
✅ Text prediction test passed
🎉 MedGemma service is working perfectly!
```

### Colab Pro+ Optimization

If you have Colab Pro+:

**Recommended Settings:**
- **GPU**: T4 ✅ (Perfect for 4B model)
- **High-RAM**: OFF ❌ (Not needed, wastes compute units)
- **Runtime**: Up to 24 hours continuous
- **Keep-alive**: Built into Pro notebook version

**Benefits:**
- Longer runtime (24 hours vs 12 hours)
- Background execution (runs when tab closed)
- Better GPU availability
- More compute units

See `COLAB_PRO_OPTIMIZATION.md` for detailed optimization guide.

---

## Daily Workflow

### Morning - Start Everything (5 minutes)

1. **Start MedFlow Services:**
   ```bash
   cd ~/Desktop/MedFlow/MedFlow-V2
   docker compose up -d
   ```

2. **Start Colab (if not running):**
   - Open your Colab notebook
   - **Runtime** → **Run all**
   - Wait for model to load
   - Copy the new ngrok URL

3. **Update MedFlow (if URL changed):**
   ```bash
   nano .env  # Update MEDGEMMA_REMOTE_URL
   ./restart_services.sh
   ```

4. **Test Connection:**
   ```bash
   python test_medgemma_connection.py <url>
   ```

### During Development

- Edit code in `backend/` or `frontend/src/`
- Changes auto-reload automatically
- View logs: `docker compose logs -f`
- Colab keeps running in background (can minimize tab)

### Evening (Optional)

```bash
# Stop MedFlow (keeps data)
docker compose down

# Leave Colab running or close it
```

---

## System Workflow

### Nurse Workflow
1. Search or create patient
2. View patient portfolio (demographics + medical history)
3. Create new session with chief complaint and current state
4. Upload medical files (X-rays, CT scans, lab results) - optional
5. Submit session for AI processing

### AI Processing (Automatic)
1. Session submitted by nurse
2. Background Celery task triggered
3. **MedGemma AI analyzes** patient context + symptoms + history
4. Generates professional medical findings and observations
5. Session moves to doctor queue

### Doctor Workflow
1. View session queue
2. Open session for review (4 tabs):
   - Patient History
   - Current Session Details
   - Uploaded Files
   - AI Analysis & Chat
3. **Chat with MedGemma AI** for additional diagnostic insights
4. Fill diagnosis form with medications and recommendations
5. Set pending tests (optional) - creates follow-up session automatically
6. Complete session

---

## Quick Commands Reference

### Starting & Stopping

```bash
# START all services
docker compose up -d

# STOP services (keeps data)
docker compose down

# STOP and remove data (fresh start)
docker compose down -v

# RESTART all services
docker compose restart

# RESTART specific service
docker compose restart backend
```

### Monitoring

```bash
# Check service status
docker compose ps

# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f celery-worker
docker compose logs -f frontend

# Last 50 lines
docker compose logs --tail=50 backend
```

### Testing

```bash
# Test backend health
curl http://localhost:8000/health

# Test MedGemma connection
python test_medgemma_connection.py <ngrok-url>

# Initialize database
docker compose exec backend python scripts/init_db.py
```

### Troubleshooting

```bash
# Port conflicts - clean everything
sudo pkill -9 docker-proxy
docker compose down --remove-orphans
docker rm -f $(docker ps -aq) 2>/dev/null || true
sudo systemctl restart docker
docker compose up -d

# Check environment variables
docker compose exec backend env | grep MEDGEMMA

# Access container shell
docker compose exec backend bash

# View resource usage
docker stats

# Complete cleanup (removes all data!)
docker compose down -v
docker system prune -a --volumes
```

---

## Database Schema

### Patients Collection

```javascript
{
  patient_id: "P-00001",  // Auto-generated
  name: "string",
  national_id: "string",  // Unique
  date_of_birth: "YYYY-MM-DD",
  age: 35,
  phone_primary: "string",
  email: "string",
  sex: "male" | "female",
  chronic_diseases: ["Diabetes", "Hypertension"],
  allergies: ["Penicillin"],
  current_medications: [{...}],
  surgical_history: [{...}],
  smoking_status: "never" | "former" | "current",
  total_sessions: 5,
  last_session_id: "S-00005"
}
```

### Sessions Collection

```javascript
{
  session_id: "S-00001",  // Auto-generated
  patient_id: "P-00001",
  session_type: "new_problem" | "follow_up",
  session_status: "draft" | "submitted" | "vlm_processing" | 
                  "awaiting_doctor" | "completed" | "pending_tests",
  
  // Nurse input
  nurse_id: "N-00001",
  assigned_doctor_id: "D-00001",
  chief_complaint: "Persistent dry cough...",
  current_state_description: "Patient reports...",
  uploaded_files: [{...}],
  
  // AI processing (MedGemma)
  vlm_initial_output: {
    findings: "Analysis shows...",
    key_observations: [...],
    suggested_considerations: [...],
    differential_patterns: [...]
  },
  
  // Doctor-AI chat
  vlm_chat_history: [{
    sender: "doctor" | "vlm",
    content: "...",
    vlm_response: {...}
  }],
  
  // Doctor review
  diagnosis: {
    primary_diagnosis: "...",
    severity: "mild" | "moderate" | "severe",
    medications: [{...}],
    recommendations: "...",
    follow_up_required: true
  },
  
  // Audit trail
  edit_history: [...],
  status_history: [...]
}
```

---

## Access Control

| Action | Nurse | Doctor | Admin |
|--------|:-----:|:------:|:-----:|
| Create patient | ✓ | ✓ | ✓ |
| Edit patient | ✓ | ✓ | ✓ |
| Create session | ✓ | ✗ | ✓ |
| Upload files | ✓ | ✗ | ✓ |
| View AI output | ✓ | ✓ | ✓ |
| Chat with AI | ✗ | ✓ | ✓ |
| Submit diagnosis | ✗ | ✓ | ✓ |
| Close session | ✗ | ✓ | ✓ |

---

## Project Structure

```
MedFlow-V2/
├── backend/
│   ├── app/
│   │   ├── api/v1/              # API endpoints
│   │   │   ├── auth.py          # Authentication
│   │   │   ├── patients.py      # Patient management
│   │   │   ├── sessions.py      # Session management
│   │   │   ├── doctor.py        # Doctor operations
│   │   │   └── nurse.py         # Nurse operations
│   │   ├── core/
│   │   │   ├── config.py        # Settings & env vars
│   │   │   ├── database.py      # MongoDB connection
│   │   │   └── security.py      # JWT & password
│   │   ├── models/              # Pydantic models
│   │   ├── services/
│   │   │   └── medgemma_service.py  # AI integration
│   │   └── tasks/
│   │       └── vlm_tasks.py     # Celery background tasks
│   ├── scripts/
│   │   └── init_db.py           # Database initialization
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable components
│   │   ├── pages/               # Page components
│   │   │   ├── Login.tsx
│   │   │   ├── NurseDashboard.tsx
│   │   │   ├── DoctorDashboard.tsx
│   │   │   └── SessionReview.tsx
│   │   ├── services/            # API services
│   │   └── types/               # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml           # All services orchestration
├── .env                         # Environment variables
├── .env.example                 # Template
├── restart_services.sh          # Helper script
├── test_medgemma_connection.py  # Test AI connection
├── MedGemma_Colab_Service.ipynb      # Standard Colab notebook
├── MedGemma_Colab_Service_Pro.ipynb  # Optimized for Pro+
└── README.md                    # This file
```

---

## Troubleshooting

### MedGemma Connection Issues

**Error: "MEDGEMMA_REMOTE_URL not configured"**

Solution:
1. Create `.env` file with `MEDGEMMA_REMOTE_URL=<your-url>`
2. Restart services: `./restart_services.sh`
3. Verify: `docker compose exec backend env | grep MEDGEMMA`

**Error: "Cannot connect to remote MedGemma service"**

Solution:
1. Check if Colab notebook is still running
2. ngrok URLs expire when Colab restarts - get new URL
3. Update `.env` with new URL
4. Restart: `./restart_services.sh`

**Error: "Request timeout"**

Solution:
1. First request can take 30-60 seconds (model loading)
2. Colab free tier may be slow during peak times
3. Consider Colab Pro for faster GPU (A100/V100)

### Docker Issues

**Error: "Port already in use"**

Solution:
```bash
sudo pkill -9 docker-proxy
docker compose down --remove-orphans
docker rm -f $(docker ps -aq) 2>/dev/null || true
sudo systemctl restart docker
docker compose up -d
```

**Error: "Container not starting"**

Solution:
```bash
# Check logs
docker compose logs <service-name>

# Rebuild
docker compose up -d --build <service-name>
```

### Colab Issues

**Colab keeps disconnecting**

Solution:
1. Keep Colab tab open (can minimize window)
2. Free tier disconnects after ~90 minutes idle
3. Pro+ allows background execution (24 hours)
4. Use the Pro-optimized notebook: `MedGemma_Colab_Service_Pro.ipynb`

**Model loading failed**

Solution:
1. Verify Hugging Face token is correct
2. Ensure you have access to `google/medgemma-1.5-4b-it`
3. Wait for approval if pending
4. Check Colab output for specific errors

---

## Performance & Timing

### Expected Response Times

| Operation | Time | Notes |
|-----------|------|-------|
| First AI request | 30-60s | Model warm-up |
| Subsequent AI requests | 10-30s | Normal operation |
| VLM Chat message | 10-30s | Per message |
| Session reanalysis | 20-60s | Full re-analysis |
| File upload | 2-10s | Depends on size |

### Colab Runtime

| Tier | Runtime | GPU | Cost |
|------|---------|-----|------|
| Free | ~12 hours | T4 | Free |
| Pro | ~24 hours | T4/V100 | $10/month |
| Pro+ | ~24 hours | T4/A100 | $50/month |

**Recommendation:** T4 GPU with standard RAM is perfect for MedGemma 1.5-4b model.

---

## Production Deployment

### Security Checklist

- [ ] Change `SECRET_KEY` in environment variables
- [ ] Set `DEBUG=False`
- [ ] Configure proper CORS origins
- [ ] Use strong passwords for all users
- [ ] Set up SSL/TLS certificates
- [ ] Configure MongoDB authentication
- [ ] Set up Redis password
- [ ] Implement backup strategy
- [ ] Set up monitoring and logging

### Production AI Deployment

For production, consider:
1. **Colab Pro+** - More reliable, longer runtime
2. **ngrok Static URL** - Doesn't change on restart
3. **Cloud VM** (AWS/GCP/Azure) - Most stable, 24/7 operation
4. **Local GPU Server** - If hardware available

---

## API Documentation

Interactive API documentation available when backend is running:
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc

---

## What's New: Real AI Integration

### Before (Mock System)
- ❌ Fake AI responses
- ❌ Instant results (no real analysis)
- ❌ Generic medical text

### Now (Real MedGemma AI)
- ✅ Real medical AI model from Google
- ✅ Professional medical analysis
- ✅ Context-aware responses
- ✅ Doctor-AI interactive chat
- ✅ Reanalysis with additional context

### Minimal Code Changes
- ✅ Same frontend interface
- ✅ Same API endpoints
- ✅ Same database schema
- ✅ Same user experience
- ✅ Just add ngrok URL and restart!

---

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Create Pull Request

---

## Support & Contact

For issues or questions:
1. Check troubleshooting section above
2. Review Colab notebook output for errors
3. Check backend logs: `docker compose logs backend -f`
4. Check Celery logs: `docker compose logs celery-worker -f`

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

- **Google MedGemma** - Medical Vision Language Model
- **FastAPI** - Modern Python web framework
- **React** - Frontend library
- **MongoDB** - Database
- **Docker** - Containerization
- **Hugging Face** - Model hosting
- **ngrok** - Secure tunneling

---

## System Requirements

**Development:**
- Docker 20.10+
- Docker Compose v2.0+
- 2GB RAM minimum, 4GB recommended
- 2GB disk space for Docker images

**Colab (AI Service):**
- Google Account
- Hugging Face Account (for MedGemma access)
- ngrok Account (free tier works)
- GPU recommended: T4 or better

**Ports Required:**
- 5173 (Frontend)
- 8000 (Backend API)
- 27017 (MongoDB - internal only)
- 6379 (Redis - internal only)

---

🎉 **You're all set! Start building amazing medical AI applications with MedFlow!**
