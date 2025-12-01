from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SessionType(str, Enum):
    new_problem = "new_problem"
    follow_up = "follow_up"


class SessionStatus(str, Enum):
    draft = "draft"
    submitted = "submitted"
    vlm_processing = "vlm_processing"
    awaiting_doctor = "awaiting_doctor"
    doctor_reviewing = "doctor_reviewing"
    completed = "completed"
    pending_tests = "pending_tests"
    vlm_failed = "vlm_failed"


class FileType(str, Enum):
    xray = "xray"
    ct = "ct"
    lab_result = "lab_result"
    ecg = "ecg"
    report = "report"
    other = "other"


class UploadedFile(BaseModel):
    file_id: str
    file_name: str
    file_type: FileType
    file_path: str
    mime_type: str
    file_size_mb: float
    upload_timestamp: datetime
    uploaded_by: str
    can_delete: bool = True


class VLMInitialInput(BaseModel):
    patient_context: Dict[str, Any]
    last_session_summary: Optional[str] = None
    chief_complaint: str
    current_state: str
    files_count: int


class VLMInitialOutput(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    findings: str
    key_observations: List[str]
    technical_assessment: str
    suggested_considerations: List[str]
    differential_patterns: List[str]
    model_version: str
    processing_time_seconds: int


class VLMChatMessage(BaseModel):
    message_id: str
    timestamp: datetime
    sender: str  # "doctor" or "vlm"
    content: str
    vlm_response: Optional[Dict[str, Any]] = None


class Medication(BaseModel):
    name: str
    dosage: str
    duration: str
    instructions: str


class Diagnosis(BaseModel):
    primary_diagnosis: str
    severity: str  # "mild", "moderate", "severe"
    medications: List[Medication] = []
    recommendations: str
    follow_up_required: bool = False
    follow_up_reason: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    doctor_notes: str


class PendingTests(BaseModel):
    required: bool = False
    tests_requested: List[str] = []
    instructions_to_patient: str = ""


class StatusHistoryEntry(BaseModel):
    status: SessionStatus
    timestamp: datetime
    user_id: str


class EditHistoryEntry(BaseModel):
    timestamp: datetime
    edited_by: str
    field: str
    old_value: Any
    new_value: Any


class SessionBase(BaseModel):
    patient_id: str
    session_type: SessionType
    assigned_doctor_id: str
    chief_complaint: str = Field(..., min_length=5, max_length=1000)
    current_state_description: str = Field(..., min_length=10)


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    chief_complaint: Optional[str] = Field(None, min_length=5, max_length=1000)
    current_state_description: Optional[str] = Field(None, min_length=10)
    assigned_doctor_id: Optional[str] = None


class Session(SessionBase):
    session_id: str
    patient_name: str
    assigned_doctor_name: str
    nurse_id: str
    nurse_name: str
    session_date: datetime
    session_status: SessionStatus
    
    # Session linkage
    parent_session_id: Optional[str] = None
    child_session_id: Optional[str] = None
    
    # Uploaded files
    uploaded_files: List[UploadedFile] = []
    
    # VLM Processing
    vlm_initial_status: str = "pending"
    vlm_initial_triggered_at: Optional[datetime] = None
    vlm_initial_completed_at: Optional[datetime] = None
    vlm_initial_input: Optional[VLMInitialInput] = None
    vlm_initial_output: Optional[VLMInitialOutput] = None
    
    # Doctor-VLM Chat
    vlm_chat_history: List[VLMChatMessage] = []
    
    # Doctor review
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_opened_at: Optional[datetime] = None
    diagnosis: Optional[Diagnosis] = None
    pending_tests: Optional[PendingTests] = None
    
    # Closure
    session_closed_at: Optional[datetime] = None
    session_closed_by: Optional[str] = None
    
    # Audit trail
    created_at: datetime
    created_by: str
    last_updated: datetime
    last_updated_by: str
    edit_history: List[EditHistoryEntry] = []
    status_history: List[StatusHistoryEntry] = []
    
    class Config:
        from_attributes = True


class SessionSummary(BaseModel):
    session_id: str
    patient_id: str
    patient_name: str
    session_date: datetime
    session_type: SessionType
    session_status: SessionStatus
    chief_complaint: str
    assigned_doctor_name: str

