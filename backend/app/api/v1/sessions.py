from fastapi import APIRouter, Depends, UploadFile, File, Form
from typing import List, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.session import (
    SessionCreate,
    SessionUpdate,
    Session,
    SessionSummary,
    UploadedFile,
    FileType
)
from app.services import session_service
from app.core.database import get_database
from app.core.security import get_current_user, require_role

router = APIRouter()


@router.post("", response_model=Session, status_code=201)
async def create_session(
    session_create: SessionCreate,
    current_user: Dict = Depends(require_role(["nurse", "admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create a new session (nurse, admin)"""
    # Get user full name
    user_doc = await db.users.find_one({"user_id": current_user["user_id"]})
    user_name = user_doc.get("full_name", "Unknown")
    
    return await session_service.create_session(
        db,
        session_create,
        current_user["user_id"],
        user_name
    )


@router.get("/{session_id}", response_model=Session)
async def get_session(
    session_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get session by session_id"""
    return await session_service.get_session(db, session_id)


@router.put("/{session_id}", response_model=Session)
async def update_session(
    session_id: str,
    session_update: SessionUpdate,
    current_user: Dict = Depends(require_role(["nurse", "admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update session (nurse, admin - only draft status)"""
    return await session_service.update_session(
        db,
        session_id,
        session_update,
        current_user["user_id"]
    )


@router.post("/{session_id}/files", response_model=UploadedFile)
async def upload_file(
    session_id: str,
    file: UploadFile = File(...),
    file_type: FileType = Form(...),
    current_user: Dict = Depends(require_role(["nurse", "admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Upload file to session (nurse, admin - only draft status)"""
    return await session_service.upload_session_file(
        db,
        session_id,
        file,
        file_type,
        current_user["user_id"]
    )


@router.delete("/{session_id}/files/{file_id}")
async def delete_file(
    session_id: str,
    file_id: str,
    current_user: Dict = Depends(require_role(["nurse", "admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Delete file from session (nurse, admin - only draft status)"""
    success = await session_service.delete_session_file(db, session_id, file_id)
    return {"success": success, "message": "File deleted successfully"}


@router.get("/{session_id}/files/{file_id}/url")
async def get_file_url(
    session_id: str,
    file_id: str,
    current_user: Dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get signed URL for file access"""
    url = await session_service.get_file_signed_url(db, session_id, file_id)
    return {"url": url}


@router.post("/{session_id}/submit", response_model=Session)
async def submit_session(
    session_id: str,
    current_user: Dict = Depends(require_role(["nurse", "admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Submit session for VLM processing (nurse, admin)"""
    return await session_service.submit_session(db, session_id, current_user["user_id"])

