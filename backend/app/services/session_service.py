from datetime import datetime
from typing import List, Optional, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import HTTPException, status, UploadFile
from app.models.session import (
    SessionCreate,
    SessionUpdate,
    Session,
    SessionSummary,
    SessionStatus,
    UploadedFile,
    FileType,
    StatusHistoryEntry,
    EditHistoryEntry
)
from app.core.database import get_next_sequence
from app.services.storage_service import storage_service
import uuid


async def create_session(
    db: AsyncIOMotorDatabase,
    session_create: SessionCreate,
    created_by: str,
    created_by_name: str
) -> Session:
    """Create a new session"""
    # Verify patient exists
    patient = await db.patients.find_one({"patient_id": session_create.patient_id})
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
    
    # Verify doctor exists
    doctor = await db.users.find_one({"user_id": session_create.assigned_doctor_id})
    if not doctor or doctor["role"] != "doctor":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assigned doctor not found"
        )
    
    # Generate session_id
    sequence = await get_next_sequence("session_id")
    session_id = f"S-{sequence:05d}"
    
    now = datetime.utcnow()
    
    # Create session document
    session_dict = session_create.model_dump()
    session_dict.update({
        "session_id": session_id,
        "patient_name": patient["name"],
        "assigned_doctor_name": doctor["full_name"],
        "nurse_id": created_by,
        "nurse_name": created_by_name,
        "session_date": now,
        "session_status": SessionStatus.draft,
        "parent_session_id": None,
        "child_session_id": None,
        "uploaded_files": [],
        "vlm_initial_status": "pending",
        "vlm_initial_triggered_at": None,
        "vlm_initial_completed_at": None,
        "vlm_initial_input": None,
        "vlm_initial_output": None,
        "vlm_chat_history": [],
        "doctor_id": None,
        "doctor_name": None,
        "doctor_opened_at": None,
        "diagnosis": None,
        "pending_tests": None,
        "session_closed_at": None,
        "session_closed_by": None,
        "created_at": now,
        "created_by": created_by,
        "last_updated": now,
        "last_updated_by": created_by,
        "edit_history": [],
        "status_history": [
            {"status": SessionStatus.draft, "timestamp": now, "user_id": created_by}
        ]
    })
    
    await db.sessions.insert_one(session_dict)
    
    return await get_session(db, session_id)


async def get_session(db: AsyncIOMotorDatabase, session_id: str) -> Session:
    """Get session by session_id"""
    session_doc = await db.sessions.find_one({"session_id": session_id})
    
    if not session_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    session_doc.pop("_id", None)
    return Session(**session_doc)


async def update_session(
    db: AsyncIOMotorDatabase,
    session_id: str,
    session_update: SessionUpdate,
    updated_by: str
) -> Session:
    """Update session (only in draft status)"""
    session_doc = await db.sessions.find_one({"session_id": session_id})
    
    if not session_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session_doc["session_status"] != SessionStatus.draft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update sessions in draft status"
        )
    
    update_data = session_update.model_dump(exclude_unset=True)
    
    if update_data:
        # If doctor changed, update doctor name
        if "assigned_doctor_id" in update_data:
            doctor = await db.users.find_one({"user_id": update_data["assigned_doctor_id"]})
            if doctor:
                update_data["assigned_doctor_name"] = doctor["full_name"]
        
        update_data["last_updated"] = datetime.utcnow()
        update_data["last_updated_by"] = updated_by
        
        await db.sessions.update_one(
            {"session_id": session_id},
            {"$set": update_data}
        )
    
    return await get_session(db, session_id)


async def upload_session_file(
    db: AsyncIOMotorDatabase,
    session_id: str,
    file: UploadFile,
    file_type: FileType,
    uploaded_by: str
) -> UploadedFile:
    """Upload file for a session"""
    session_doc = await db.sessions.find_one({"session_id": session_id})
    
    if not session_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session_doc["session_status"] != SessionStatus.draft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only upload files to sessions in draft status"
        )
    
    # Generate file_id
    file_id = f"F-{uuid.uuid4().hex[:8]}"
    
    # Read file content
    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)
    
    # Upload to storage
    destination_path = f"sessions/{session_id}/{file_id}_{file.filename}"
    file_path = await storage_service.upload_file(
        file_content,
        destination_path,
        file.content_type or "application/octet-stream"
    )
    
    # Create file record
    uploaded_file = UploadedFile(
        file_id=file_id,
        file_name=file.filename or "unnamed",
        file_type=file_type,
        file_path=file_path,
        mime_type=file.content_type or "application/octet-stream",
        file_size_mb=round(file_size_mb, 2),
        upload_timestamp=datetime.utcnow(),
        uploaded_by=uploaded_by,
        can_delete=True
    )
    
    # Add to session
    await db.sessions.update_one(
        {"session_id": session_id},
        {"$push": {"uploaded_files": uploaded_file.model_dump()}}
    )
    
    return uploaded_file


async def delete_session_file(
    db: AsyncIOMotorDatabase,
    session_id: str,
    file_id: str
) -> bool:
    """Delete file from session (only in draft status)"""
    session_doc = await db.sessions.find_one({"session_id": session_id})
    
    if not session_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session_doc["session_status"] != SessionStatus.draft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only delete files from sessions in draft status"
        )
    
    # Find file
    file_to_delete = None
    for f in session_doc.get("uploaded_files", []):
        if f["file_id"] == file_id:
            file_to_delete = f
            break
    
    if not file_to_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Delete from storage
    await storage_service.delete_file(file_to_delete["file_path"])
    
    # Remove from session
    await db.sessions.update_one(
        {"session_id": session_id},
        {"$pull": {"uploaded_files": {"file_id": file_id}}}
    )
    
    return True


async def get_file_signed_url(
    db: AsyncIOMotorDatabase,
    session_id: str,
    file_id: str
) -> str:
    """Get signed URL for file access"""
    session_doc = await db.sessions.find_one({"session_id": session_id})
    
    if not session_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Find file
    for f in session_doc.get("uploaded_files", []):
        if f["file_id"] == file_id:
            return await storage_service.get_signed_url(f["file_path"])
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="File not found"
    )


async def submit_session(
    db: AsyncIOMotorDatabase,
    session_id: str,
    submitted_by: str
) -> Session:
    """Submit session for VLM processing"""
    session_doc = await db.sessions.find_one({"session_id": session_id})
    
    if not session_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if session_doc["session_status"] != SessionStatus.draft:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session already submitted"
        )
    
    now = datetime.utcnow()
    
    # Update status to submitted
    await db.sessions.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "session_status": SessionStatus.submitted,
                "last_updated": now,
                "last_updated_by": submitted_by
            },
            "$push": {
                "status_history": {
                    "status": SessionStatus.submitted,
                    "timestamp": now,
                    "user_id": submitted_by
                }
            }
        }
    )
    
    # Trigger VLM processing task
    from app.tasks.vlm_tasks import process_session_vlm
    process_session_vlm.delay(session_id)
    
    return await get_session(db, session_id)


async def get_sessions_for_doctor_queue(
    db: AsyncIOMotorDatabase,
    doctor_id: Optional[str] = None,
    status_filter: Optional[List[SessionStatus]] = None,
    current_doctor_id: Optional[str] = None
) -> List[SessionSummary]:
    """Get sessions for doctor queue
    
    Args:
        db: Database connection
        doctor_id: Optional doctor ID to filter by assigned doctor (for awaiting_doctor/vlm_failed)
        status_filter: Optional list of statuses to filter by. 
                      Defaults to [awaiting_doctor, vlm_failed]
        current_doctor_id: Current doctor's ID to include their doctor_reviewing sessions
    """
    if status_filter is None:
        status_filter = [SessionStatus.awaiting_doctor, SessionStatus.vlm_failed]
    
    # Build query for awaiting_doctor and vlm_failed sessions
    query_pending = {"session_status": {"$in": [s.value for s in status_filter]}}
    
    if doctor_id:
        query_pending["assigned_doctor_id"] = doctor_id
    
    # Build query for doctor_reviewing sessions (always show sessions being reviewed by current doctor)
    query_reviewing = {
        "session_status": SessionStatus.doctor_reviewing.value
    }
    if current_doctor_id:
        query_reviewing["doctor_id"] = current_doctor_id
    
    # Combine both queries using $or
    combined_query = {"$or": [query_pending, query_reviewing]}
    
    cursor = db.sessions.find(combined_query).sort("session_date", 1)
    sessions = await cursor.to_list(length=None)
    
    results = []
    for session in sessions:
        results.append(SessionSummary(
            session_id=session["session_id"],
            patient_id=session["patient_id"],
            patient_name=session["patient_name"],
            session_date=session["session_date"],
            session_type=session["session_type"],
            session_status=session["session_status"],
            chief_complaint=session["chief_complaint"],
            assigned_doctor_name=session["assigned_doctor_name"]
        ))
    
    return results
