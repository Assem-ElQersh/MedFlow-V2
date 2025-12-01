from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.session import SessionSummary, Session, SessionStatus, Diagnosis, PendingTests
from app.services import session_service
from app.services.vlm_service import mock_vlm_service
from app.core.database import get_database
from app.core.security import get_current_user, require_role
from datetime import datetime
import uuid

router = APIRouter()


@router.get("/queue", response_model=List[SessionSummary])
async def get_doctor_queue(
    assigned_to_me: bool = Query(False, description="Filter by assigned doctor"),
    status: SessionStatus = Query(SessionStatus.awaiting_doctor),
    current_user: Dict = Depends(require_role(["doctor", "admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get sessions in doctor queue"""
    doctor_id = current_user["user_id"] if assigned_to_me else None
    return await session_service.get_sessions_for_doctor_queue(db, doctor_id, status)


@router.get("/sessions/{session_id}/review", response_model=Session)
async def get_session_for_review(
    session_id: str,
    current_user: Dict = Depends(require_role(["doctor", "admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get session for doctor review and lock it"""
    session_doc = await db.sessions.find_one({"session_id": session_id})
    
    if not session_doc:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # If status is awaiting_doctor, change to doctor_reviewing
    if session_doc["session_status"] == SessionStatus.awaiting_doctor:
        now = datetime.utcnow()
        await db.sessions.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "session_status": SessionStatus.doctor_reviewing,
                    "doctor_id": current_user["user_id"],
                    "doctor_name": current_user.get("username"),  # Should be full_name
                    "doctor_opened_at": now,
                    "last_updated": now
                },
                "$push": {
                    "status_history": {
                        "status": SessionStatus.doctor_reviewing,
                        "timestamp": now,
                        "user_id": current_user["user_id"]
                    }
                }
            }
        )
    
    return await session_service.get_session(db, session_id)


@router.post("/sessions/{session_id}/vlm-chat")
async def chat_with_vlm(
    session_id: str,
    message: Dict[str, str],
    current_user: Dict = Depends(require_role(["doctor", "admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Send a message to VLM and get response"""
    session_doc = await db.sessions.find_one({"session_id": session_id})
    
    if not session_doc:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Get patient context
    patient = await db.patients.find_one({"patient_id": session_doc["patient_id"]})
    patient_context = {
        "age": patient.get("age"),
        "sex": patient.get("sex"),
        "chronic_diseases": patient.get("chronic_diseases", [])
    }
    
    session_context = {
        "chief_complaint": session_doc.get("chief_complaint"),
        "current_state": session_doc.get("current_state_description"),
        "vlm_initial_output": session_doc.get("vlm_initial_output")
    }
    
    # Get VLM response
    vlm_response = mock_vlm_service.process_doctor_query(
        patient_context=patient_context,
        session_context=session_context,
        doctor_query=message.get("content", ""),
        previous_chat=session_doc.get("vlm_chat_history", [])
    )
    
    # Create chat message
    message_id = f"M-{uuid.uuid4().hex[:8]}"
    chat_message = {
        "message_id": message_id,
        "timestamp": datetime.utcnow(),
        "sender": "doctor",
        "content": message.get("content", ""),
        "vlm_response": vlm_response
    }
    
    # Add to chat history
    await db.sessions.update_one(
        {"session_id": session_id},
        {"$push": {"vlm_chat_history": chat_message}}
    )
    
    return chat_message


@router.put("/sessions/{session_id}/diagnosis")
async def submit_diagnosis(
    session_id: str,
    diagnosis: Diagnosis,
    current_user: Dict = Depends(require_role(["doctor", "admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Submit diagnosis for a session"""
    session_doc = await db.sessions.find_one({"session_id": session_id})
    
    if not session_doc:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    now = datetime.utcnow()
    await db.sessions.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "diagnosis": diagnosis.model_dump(),
                "last_updated": now,
                "last_updated_by": current_user["user_id"]
            }
        }
    )
    
    return {"success": True, "message": "Diagnosis saved successfully"}


@router.put("/sessions/{session_id}/pending-tests")
async def set_pending_tests(
    session_id: str,
    pending_tests: PendingTests,
    current_user: Dict = Depends(require_role(["doctor", "admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Set pending tests for a session"""
    now = datetime.utcnow()
    await db.sessions.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "pending_tests": pending_tests.model_dump(),
                "last_updated": now,
                "last_updated_by": current_user["user_id"]
            }
        }
    )
    
    return {"success": True, "message": "Pending tests saved successfully"}


@router.post("/sessions/{session_id}/close")
async def close_session(
    session_id: str,
    current_user: Dict = Depends(require_role(["doctor", "admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Close a session and optionally create follow-up"""
    session_doc = await db.sessions.find_one({"session_id": session_id})
    
    if not session_doc:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    if not session_doc.get("diagnosis"):
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot close session without diagnosis"
        )
    
    now = datetime.utcnow()
    pending_tests = session_doc.get("pending_tests", {})
    
    # Determine final status
    if pending_tests.get("required"):
        final_status = SessionStatus.pending_tests
    else:
        final_status = SessionStatus.completed
    
    # Close current session
    await db.sessions.update_one(
        {"session_id": session_id},
        {
            "$set": {
                "session_status": final_status,
                "session_closed_at": now,
                "session_closed_by": current_user["user_id"],
                "last_updated": now
            },
            "$push": {
                "status_history": {
                    "status": final_status,
                    "timestamp": now,
                    "user_id": current_user["user_id"]
                }
            }
        }
    )
    
    # Create follow-up session if pending tests
    follow_up_session_id = None
    if pending_tests.get("required"):
        from app.core.database import get_next_sequence
        
        # Generate new session_id
        sequence = await get_next_sequence("session_id")
        follow_up_session_id = f"S-{sequence:05d}"
        
        # Create follow-up session
        follow_up_doc = {
            "session_id": follow_up_session_id,
            "patient_id": session_doc["patient_id"],
            "patient_name": session_doc["patient_name"],
            "session_type": "follow_up",
            "session_date": now,
            "session_status": SessionStatus.draft,
            "parent_session_id": session_id,
            "child_session_id": None,
            "assigned_doctor_id": session_doc["assigned_doctor_id"],
            "assigned_doctor_name": session_doc["assigned_doctor_name"],
            "nurse_id": None,
            "nurse_name": None,
            "chief_complaint": f"Follow-up for: {session_doc['chief_complaint']}",
            "current_state_description": f"Pending tests: {', '.join(pending_tests.get('tests_requested', []))}",
            "uploaded_files": [],
            "vlm_initial_status": "pending",
            "vlm_chat_history": [],
            "created_at": now,
            "created_by": "system",
            "last_updated": now,
            "last_updated_by": "system",
            "status_history": [
                {"status": SessionStatus.draft, "timestamp": now, "user_id": "system"}
            ]
        }
        
        await db.sessions.insert_one(follow_up_doc)
        
        # Link sessions
        await db.sessions.update_one(
            {"session_id": session_id},
            {"$set": {"child_session_id": follow_up_session_id}}
        )
    
    # Update patient's last session info
    await db.patients.update_one(
        {"patient_id": session_doc["patient_id"]},
        {
            "$set": {
                "last_session_id": session_id,
                "last_session_date": now
            },
            "$inc": {"total_sessions": 1}
        }
    )
    
    return {
        "success": True,
        "message": "Session closed successfully",
        "session_id": session_id,
        "follow_up_session_id": follow_up_session_id
    }

