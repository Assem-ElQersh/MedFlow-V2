from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class SexEnum(str, Enum):
    male = "male"
    female = "female"


class SmokingStatusEnum(str, Enum):
    never = "never"
    former = "former"
    current = "current"
    unknown = "unknown"


class Medication(BaseModel):
    name: str
    dosage: str
    frequency: str
    start_date: Optional[date] = None
    instructions: Optional[str] = None


class SurgicalProcedure(BaseModel):
    procedure: str
    date: date
    notes: Optional[str] = None


class SmokingDetails(BaseModel):
    pack_years: Optional[int] = None
    quit_date: Optional[date] = None


class PatientBase(BaseModel):
    # I. Personal Identification (Mandatory)
    name: str = Field(..., min_length=2, max_length=200)
    national_id: str = Field(..., min_length=10, max_length=20)
    date_of_birth: date
    phone_primary: str = Field(..., min_length=10, max_length=20)
    
    # II. Optional Contact Information
    phone_secondary: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    
    # III. Medical Background
    sex: SexEnum
    chronic_diseases: List[str] = []
    allergies: List[str] = []
    current_medications: List[Medication] = []
    surgical_history: List[SurgicalProcedure] = []
    smoking_status: SmokingStatusEnum = SmokingStatusEnum.unknown
    smoking_details: Optional[SmokingDetails] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    # All fields optional for updates
    name: Optional[str] = Field(None, min_length=2, max_length=200)
    date_of_birth: Optional[date] = None
    phone_primary: Optional[str] = Field(None, min_length=10, max_length=20)
    phone_secondary: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    sex: Optional[SexEnum] = None
    chronic_diseases: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    current_medications: Optional[List[Medication]] = None
    surgical_history: Optional[List[SurgicalProcedure]] = None
    smoking_status: Optional[SmokingStatusEnum] = None
    smoking_details: Optional[SmokingDetails] = None


class Patient(PatientBase):
    patient_id: str
    age: int
    registration_date: datetime
    last_updated: datetime
    last_updated_by: str
    total_sessions: int = 0
    last_session_id: Optional[str] = None
    last_session_date: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PatientSearchResult(BaseModel):
    patient_id: str
    name: str
    age: int
    phone_primary: str
    national_id: str
    last_session_date: Optional[datetime] = None
    total_sessions: int

