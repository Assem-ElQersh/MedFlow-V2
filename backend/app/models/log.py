from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class LogLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class LogCategory(str, Enum):
    AUTH = "auth"
    SESSION = "session"
    SYSTEM = "system"
    VLM = "vlm"
    ADMIN = "admin"


class LogEntry(BaseModel):
    log_id: str
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    message: str
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    session_id: Optional[str] = None
    patient_id: Optional[str] = None
    patient_name: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True


class LogSummary(BaseModel):
    log_id: str
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    message: str
    user_name: Optional[str] = None
    session_id: Optional[str] = None
