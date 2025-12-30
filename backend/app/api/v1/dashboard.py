from fastapi import APIRouter, Depends
from typing import Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.security import get_current_user
from app.models.session import SessionStatus
from datetime import datetime, timedelta

router = APIRouter()


@router.get("/stats", response_model=Dict)
async def get_dashboard_stats(
    current_user: Dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get dashboard statistics based on user role"""
    user_role = current_user.get("role")
    user_id = current_user.get("user_id")
    
    stats = {}
    
    # Common stats for all roles
    total_patients = await db.patients.count_documents({})
    stats["total_patients"] = total_patients
    
    # Calculate today's start time
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if user_role == "nurse":
        # Nurse-specific stats
        # Active sessions (draft or submitted)
        active_sessions = await db.sessions.count_documents({
            "session_status": {"$in": [
                SessionStatus.draft.value,
                SessionStatus.submitted.value,
                SessionStatus.vlm_processing.value
            ]}
        })
        stats["active_sessions"] = active_sessions
        
        # Sessions created today by this nurse
        created_today = await db.sessions.count_documents({
            "created_by": user_id,
            "created_at": {"$gte": today_start}
        })
        stats["created_today"] = created_today
        
        # Sessions awaiting VLM or doctor
        pending_review = await db.sessions.count_documents({
            "session_status": {"$in": [
                SessionStatus.vlm_processing.value,
                SessionStatus.awaiting_doctor.value,
                SessionStatus.vlm_failed.value
            ]}
        })
        stats["pending_review"] = pending_review
        
    elif user_role == "doctor":
        # Doctor-specific stats
        # Sessions assigned to this doctor awaiting review
        assigned_to_me = await db.sessions.count_documents({
            "assigned_doctor_id": user_id,
            "session_status": {"$in": [
                SessionStatus.awaiting_doctor.value,
                SessionStatus.vlm_failed.value
            ]}
        })
        stats["assigned_to_me"] = assigned_to_me
        
        # Sessions currently being reviewed by this doctor
        currently_reviewing = await db.sessions.count_documents({
            "doctor_id": user_id,
            "session_status": SessionStatus.doctor_reviewing.value
        })
        stats["currently_reviewing"] = currently_reviewing
        
        # Sessions completed today by this doctor
        completed_today = await db.sessions.count_documents({
            "doctor_id": user_id,
            "session_status": {"$in": [
                SessionStatus.completed.value,
                SessionStatus.pending_tests.value
            ]},
            "session_closed_at": {"$gte": today_start}
        })
        stats["completed_today"] = completed_today
        
        # Total sessions assigned to this doctor (all time)
        total_assigned = await db.sessions.count_documents({
            "assigned_doctor_id": user_id
        })
        stats["total_assigned"] = total_assigned
        
    elif user_role == "admin":
        # Admin-specific stats
        # All active sessions
        active_sessions = await db.sessions.count_documents({
            "session_status": {"$in": [
                SessionStatus.draft.value,
                SessionStatus.submitted.value,
                SessionStatus.vlm_processing.value,
                SessionStatus.awaiting_doctor.value,
                SessionStatus.vlm_failed.value,
                SessionStatus.doctor_reviewing.value
            ]}
        })
        stats["active_sessions"] = active_sessions
        
        # Completed sessions today
        completed_today = await db.sessions.count_documents({
            "session_status": {"$in": [
                SessionStatus.completed.value,
                SessionStatus.pending_tests.value
            ]},
            "session_closed_at": {"$gte": today_start}
        })
        stats["completed_today"] = completed_today
        
        # Total users
        total_users = await db.users.count_documents({})
        stats["total_users"] = total_users
        
        # Total sessions
        total_sessions = await db.sessions.count_documents({})
        stats["total_sessions"] = total_sessions
    
    return stats

