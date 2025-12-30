# MedFlow - Medical Patient Management System

A comprehensive medical patient management system with AI-powered diagnostic assistance using Vision Language Models (VLM).

## Overview

MedFlow is a web-based hospital management system designed for chest disease diagnosis and patient care. It features patient registration, session-based visit tracking, AI-assisted diagnosis, and comprehensive medical record management with complete audit trails.

## Key Features

- **Patient Management**: Complete CRUD operations with comprehensive medical history
- **Session Workflow**: Create and manage medical sessions with file uploads (X-rays, CT scans, lab results)
- **AI Integration**: Mock VLM service for intelligent medical analysis and findings
- **Doctor-VLM Chat**: Interactive consultation interface for additional diagnostic insights
- **Role-Based Access**: Nurse, Doctor, and Admin roles with specific permissions
- **Audit Trail**: Complete tracking of all changes with immutable medical records
- **Follow-up System**: Automatic follow-up session creation for pending tests
- **File Management**: Upload and manage medical files with Google Cloud Storage support

## Technology Stack

**Backend:**
- FastAPI (Python async web framework)
- MongoDB with Motor (async driver)
- Celery + Redis (background task processing)
- Pydantic v2 (data validation)
- JWT authentication
- Google Cloud Storage (file storage)

**Frontend:**
- React 18 with TypeScript
- Vite (build tool)
- Material-UI v5 (component library)
- React Router v6 (routing)
- React Query (data fetching/caching)
- Axios (HTTP client)

**Infrastructure:**
- Docker & Docker Compose
- MongoDB 7.0
- Redis 7

## Database Schema

### Patients Collection

```javascript
{
  _id: ObjectId,
  patient_id: "P-00001",  // Auto-generated, unique
  
  // Personal Information
  name: "string",
  national_id: "string",  // Unique, indexed
  date_of_birth: "YYYY-MM-DD",
  age: 35,  // Auto-calculated
  phone_primary: "string",  // Indexed
  phone_secondary: "string" (optional),
  email: "string" (optional),
  address: "string" (optional),
  
  // Medical Profile
  sex: "male" | "female",
  chronic_diseases: ["Type 2 Diabetes", "Hypertension"],
  allergies: ["Penicillin", "Aspirin"],
  current_medications: [
    {
      name: "Metformin",
      dosage: "500mg",
      frequency: "twice daily",
      start_date: "2023-01-10",
      instructions: "Take with meals"
    }
  ],
  surgical_history: [
    {
      procedure: "Appendectomy",
      date: "2015-08-20",
      notes: "Uncomplicated"
    }
  ],
  smoking_status: "never" | "former" | "current" | "unknown",
  smoking_details: {
    pack_years: 10,
    quit_date: "2020-01-01"
  },
  
  // System Metadata
  registration_date: ISODate,
  last_updated: ISODate,
  last_updated_by: "N-00001",
  total_sessions: 5,
  last_session_id: "S-00005",
  last_session_date: ISODate
}
```

### Sessions Collection

```javascript
{
  _id: ObjectId,
  session_id: "S-00001",  // Auto-generated, unique
  patient_id: "P-00001",
  patient_name: "Ahmed Mohamed",
  
  // Session Metadata
  session_date: ISODate,
  session_type: "new_problem" | "follow_up",
  session_status: "draft" | "submitted" | "vlm_processing" | 
                  "awaiting_doctor" | "doctor_reviewing" | 
                  "completed" | "pending_tests",
  
  // Session Linkage
  parent_session_id: "S-00000" (null if new),
  child_session_id: "S-00002" (null if not created),
  
  // Nurse Input
  nurse_id: "N-00001",
  nurse_name: "Fatma Hassan",
  assigned_doctor_id: "D-00001",
  assigned_doctor_name: "Dr. Mona Samir",
  chief_complaint: "Persistent dry cough for 3 weeks",
  current_state_description: "Patient reports worsening at night...",
  
  // Uploaded Files
  uploaded_files: [
    {
      file_id: "F-00001",
      file_name: "chest_xray.dcm",
      file_type: "xray" | "ct" | "lab_result" | "ecg" | "report" | "other",
      file_path: "gs://bucket/path/to/file",
      mime_type: "application/dicom",
      file_size_mb: 12.5,
      upload_timestamp: ISODate,
      uploaded_by: "N-00001",
      can_delete: true
    }
  ],
  
  // VLM Processing
  vlm_initial_status: "pending" | "processing" | "completed" | "failed",
  vlm_initial_input: { /* patient context, symptoms, files */ },
  vlm_initial_output: {
    findings: "Chest X-ray shows...",
    key_observations: [...],
    technical_assessment: "...",
    suggested_considerations: [...],
    differential_patterns: [...],
    model_version: "medgemma-v2.1-mock",
    processing_time_seconds: 87
  },
  
  // Doctor-VLM Chat
  vlm_chat_history: [
    {
      message_id: "M-00001",
      timestamp: ISODate,
      sender: "doctor" | "vlm",
      content: "Patient also mentions shoulder pain...",
      vlm_response: { /* VLM analysis */ }
    }
  ],
  
  // Doctor Review
  doctor_id: "D-00001",
  doctor_name: "Dr. Mona Samir",
  doctor_opened_at: ISODate,
  diagnosis: {
    primary_diagnosis: "Viral bronchitis",
    severity: "mild" | "moderate" | "severe",
    medications: [
      {
        name: "Dextromethorphan syrup",
        dosage: "10ml",
        duration: "7 days",
        instructions: "Take after meals"
      }
    ],
    recommendations: "Continue diabetes management...",
    follow_up_required: true,
    follow_up_date: ISODate,
    doctor_notes: "Patient educated about symptoms..."
  },
  
  // Pending Tests
  pending_tests: {
    required: true | false,
    tests_requested: ["CT Scan chest"],
    instructions_to_patient: "Return with results..."
  },
  
  // Closure & Audit
  session_closed_at: ISODate,
  session_closed_by: "D-00001",
  created_at: ISODate,
  created_by: "N-00001",
  last_updated: ISODate,
  last_updated_by: "D-00001",
  edit_history: [ /* all changes tracked */ ],
  status_history: [ /* status transitions */ ]
}
```

### Users Collection

```javascript
{
  _id: ObjectId,
  user_id: "N-00001" | "D-00001" | "A-00001",
  username: "string",
  email: "string",
  full_name: "string",
  role: "nurse" | "doctor" | "admin",
  hashed_password: "bcrypt_hash",
  is_active: true,
  created_at: ISODate,
  last_login: ISODate
}
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/Assem-ElQersh/MedFlow-V2.git
cd MedFlow-V2
```

2. Start services with Docker Compose:
```bash
docker-compose up -d
```

3. Initialize database with sample users:
```bash
docker-compose exec backend python scripts/init_db.py
```

4. Access the application:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/v1/docs

### Default Credentials

After initialization, use these credentials:

- **Admin**: username: `admin`, password: `admin123`
- **Doctor**: username: `doctor1`, password: `doctor123`
- **Nurse**: username: `nurse1`, password: `nurse123`

## Manual Setup (Development)

### Backend

```bash
# Create conda environment
conda create -n Medflow python=3.11 -y
conda activate Medflow

# Install dependencies
cd backend
pip install -r requirements.txt

# Create .env file (copy from .env.example)
cp .env.example .env

# Start MongoDB and Redis (Docker)
docker-compose up -d mongodb redis

# Initialize database
python scripts/init_db.py

# Start backend server
python -m uvicorn app.main:app --reload --port 8000

# Start Celery worker (new terminal)
celery -A celery_app worker --loglevel=info --pool=solo
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## System Workflow

### Nurse Workflow
1. Search or create patient
2. View patient portfolio (demographics + medical history)
3. Create new session
4. Upload medical files (optional)
5. Submit session for VLM processing

### VLM Processing (Automatic)
1. Session submitted by nurse
2. Background Celery task triggered
3. VLM analyzes patient context + symptoms + files
4. Generates medical findings and observations
5. Session moves to doctor queue

### Doctor Workflow
1. View session queue
2. Open session for review (4 tabs):
   - Patient History
   - Current Session
   - Uploaded Files
   - VLM Analysis & Chat
3. Chat with VLM for additional insights
4. Fill diagnosis form
5. Set pending tests (optional)
6. Complete session

## API Documentation

Once running, access interactive API documentation:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc

## Project Structure

```
MedFlow/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Config, database, security
│   │   ├── models/          # Pydantic models
│   │   ├── services/        # Business logic
│   │   └── tasks/           # Celery tasks
│   ├── scripts/             # Utility scripts
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   └── types/           # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Key Features Detail

### Access Control Matrix

| Action | Nurse | Doctor | Admin |
|--------|:-----:|:------:|:-----:|
| Create patient | ✓ | ✓ | ✓ |
| Edit patient | ✓ | ✓ | ✓ |
| Create session | ✓ | ✗ | ✓ |
| Upload files | ✓ | ✗ | ✓ |
| View VLM output | ✓ | ✓ | ✓ |
| Chat with VLM | ✗ | ✓ | ✓ |
| Submit diagnosis | ✗ | ✓ | ✓ |
| Close session | ✗ | ✓ | ✓ |

### Session Immutability
- Closed sessions are read-only
- Complete audit trail maintained
- Medical-legal compliance
- Historical accuracy preserved

### Session Linkage
- Parent-child relationships for follow-ups
- Automatic follow-up creation when tests pending
- Seamless continuity of care

## Production Deployment

### Security Checklist
- Change SECRET_KEY in environment variables
- Set DEBUG=False
- Configure proper CORS origins
- Use strong passwords for all default users
- Set up SSL/TLS certificates
- Configure MongoDB authentication
- Set up Redis password
- Configure Google Cloud Storage credentials
- Implement backup strategy

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
