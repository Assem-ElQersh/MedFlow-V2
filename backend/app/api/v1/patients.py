from fastapi import APIRouter, Depends, Query
from typing import List, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.patient import PatientCreate, PatientUpdate, Patient, PatientSearchResult
from app.services import patient_service
from app.core.database import get_database
from app.core.security import get_current_user, require_role

router = APIRouter()


@router.post("", response_model=Patient, status_code=201)
async def create_patient(
    patient_create: PatientCreate,
    current_user: Dict = Depends(require_role(["nurse", "doctor", "admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create a new patient (nurse, doctor, admin)"""
    return await patient_service.create_patient(db, patient_create, current_user["user_id"])


@router.get("/search", response_model=List[PatientSearchResult])
async def search_patients(
    q: str = Query(..., min_length=1, description="Search query (name, phone, or national_id)"),
    limit: int = Query(20, ge=1, le=100),
    current_user: Dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Search patients by name, phone, or national_id"""
    return await patient_service.search_patients(db, q, limit)


@router.get("/{patient_id}", response_model=Patient)
async def get_patient(
    patient_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get patient by patient_id"""
    return await patient_service.get_patient(db, patient_id)


@router.put("/{patient_id}", response_model=Patient)
async def update_patient(
    patient_id: str,
    patient_update: PatientUpdate,
    current_user: Dict = Depends(require_role(["nurse", "doctor", "admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update patient information (nurse, doctor, admin)"""
    return await patient_service.update_patient(db, patient_id, patient_update, current_user["user_id"])


@router.get("/{patient_id}/portfolio", response_model=Dict)
async def get_patient_portfolio(
    patient_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get patient with all their sessions"""
    return await patient_service.get_patient_portfolio(db, patient_id)

