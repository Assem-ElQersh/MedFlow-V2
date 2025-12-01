from datetime import datetime, date
from typing import List, Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status
from app.models.patient import PatientCreate, PatientUpdate, Patient, PatientSearchResult
from app.core.database import get_next_sequence


def calculate_age(birth_date: date) -> int:
    """Calculate age from birth date"""
    today = datetime.now().date()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age


async def create_patient(
    db: AsyncIOMotorDatabase,
    patient_create: PatientCreate,
    created_by: str
) -> Patient:
    """Create a new patient"""
    # Check if national_id already exists
    existing_patient = await db.patients.find_one({"national_id": patient_create.national_id})
    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Patient with this national ID already exists"
        )
    
    # Generate patient_id
    sequence = await get_next_sequence("patient_id")
    patient_id = f"P-{sequence:05d}"
    
    # Calculate age
    age = calculate_age(patient_create.date_of_birth)
    
    # Create patient document
    patient_dict = patient_create.model_dump()
    patient_dict.update({
        "patient_id": patient_id,
        "age": age,
        "registration_date": datetime.utcnow(),
        "last_updated": datetime.utcnow(),
        "last_updated_by": created_by,
        "total_sessions": 0,
        "last_session_id": None,
        "last_session_date": None
    })
    
    # Convert date objects to ISO format for MongoDB
    patient_dict["date_of_birth"] = patient_dict["date_of_birth"].isoformat()
    
    # Convert nested medication dates
    for med in patient_dict.get("current_medications", []):
        if med.get("start_date"):
            med["start_date"] = med["start_date"].isoformat()
    
    # Convert surgical history dates
    for surgery in patient_dict.get("surgical_history", []):
        if surgery.get("date"):
            surgery["date"] = surgery["date"].isoformat()
    
    # Convert smoking details quit date
    if patient_dict.get("smoking_details") and patient_dict["smoking_details"].get("quit_date"):
        patient_dict["smoking_details"]["quit_date"] = patient_dict["smoking_details"]["quit_date"].isoformat()
    
    await db.patients.insert_one(patient_dict)
    
    return await get_patient(db, patient_id)


async def get_patient(db: AsyncIOMotorDatabase, patient_id: str) -> Patient:
    """Get patient by patient_id"""
    patient_doc = await db.patients.find_one({"patient_id": patient_id})
    
    if not patient_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Remove MongoDB _id
    patient_doc.pop("_id", None)
    
    return Patient(**patient_doc)


async def update_patient(
    db: AsyncIOMotorDatabase,
    patient_id: str,
    patient_update: PatientUpdate,
    updated_by: str
) -> Patient:
    """Update patient information"""
    # Check if patient exists
    existing_patient = await db.patients.find_one({"patient_id": patient_id})
    if not existing_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Prepare update data
    update_data = patient_update.model_dump(exclude_unset=True)
    
    if update_data:
        # Update age if date_of_birth changed
        if "date_of_birth" in update_data:
            update_data["age"] = calculate_age(update_data["date_of_birth"])
            update_data["date_of_birth"] = update_data["date_of_birth"].isoformat()
        
        # Convert nested dates
        if "current_medications" in update_data:
            for med in update_data["current_medications"]:
                if med.get("start_date"):
                    med["start_date"] = med["start_date"].isoformat()
        
        if "surgical_history" in update_data:
            for surgery in update_data["surgical_history"]:
                if surgery.get("date"):
                    surgery["date"] = surgery["date"].isoformat()
        
        if "smoking_details" in update_data and update_data["smoking_details"]:
            if update_data["smoking_details"].get("quit_date"):
                update_data["smoking_details"]["quit_date"] = update_data["smoking_details"]["quit_date"].isoformat()
        
        update_data["last_updated"] = datetime.utcnow()
        update_data["last_updated_by"] = updated_by
        
        await db.patients.update_one(
            {"patient_id": patient_id},
            {"$set": update_data}
        )
    
    return await get_patient(db, patient_id)


async def search_patients(
    db: AsyncIOMotorDatabase,
    query: str,
    limit: int = 20
) -> List[PatientSearchResult]:
    """Search patients by name, phone, or national_id"""
    # Create search filter
    search_filter = {
        "$or": [
            {"name": {"$regex": query, "$options": "i"}},
            {"phone_primary": {"$regex": query}},
            {"phone_secondary": {"$regex": query}},
            {"national_id": {"$regex": query}},
        ]
    }
    
    cursor = db.patients.find(search_filter).limit(limit)
    patients = await cursor.to_list(length=limit)
    
    results = []
    for patient in patients:
        results.append(PatientSearchResult(
            patient_id=patient["patient_id"],
            name=patient["name"],
            age=patient["age"],
            phone_primary=patient["phone_primary"],
            national_id=patient["national_id"],
            last_session_date=patient.get("last_session_date"),
            total_sessions=patient.get("total_sessions", 0)
        ))
    
    return results


async def get_patient_portfolio(
    db: AsyncIOMotorDatabase,
    patient_id: str
) -> Dict:
    """Get patient with all their sessions"""
    patient = await get_patient(db, patient_id)
    
    # Get all sessions for this patient
    sessions_cursor = db.sessions.find(
        {"patient_id": patient_id}
    ).sort("session_date", -1)
    
    sessions = await sessions_cursor.to_list(length=None)
    
    # Remove MongoDB _id from sessions
    for session in sessions:
        session.pop("_id", None)
    
    return {
        "patient": patient.model_dump(),
        "sessions": sessions
    }

