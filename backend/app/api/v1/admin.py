from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.log import LogEntry, LogLevel, LogCategory
from app.services.log_service import log_service
from app.core.database import get_database
from app.core.security import require_role
from app.core.config import settings
import httpx

router = APIRouter()


@router.get("/logs", response_model=List[LogEntry])
async def get_system_logs(
    category: Optional[LogCategory] = None,
    level: Optional[LogLevel] = None,
    limit: int = Query(100, le=500),
    skip: int = 0,
    current_user: Dict = Depends(require_role(["admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get system logs (Admin only)"""
    return await log_service.get_logs(
        db=db,
        category=category,
        level=level,
        limit=limit,
        skip=skip
    )


@router.get("/logs/stats")
async def get_logs_stats(
    current_user: Dict = Depends(require_role(["admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get log statistics (Admin only)"""
    
    stats = {
        "total": await log_service.get_logs_count(db),
        "by_category": {},
        "by_level": {}
    }
    
    # Count by category
    for category in LogCategory:
        count = await log_service.get_logs_count(db, category=category)
        stats["by_category"][category.value] = count
    
    # Count by level
    for level in LogLevel:
        count = await log_service.get_logs_count(db, level=level)
        stats["by_level"][level.value] = count
    
    return stats


@router.get("/system/status")
async def get_system_status(
    current_user: Dict = Depends(require_role(["admin"])),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get system status including VLM connection (Admin only)"""
    
    status = {
        "mongodb": "disconnected",
        "vlm_service": "disconnected",
        "vlm_model": None,
        "timestamp": None
    }
    
    # Check MongoDB
    try:
        await db.command("ping")
        status["mongodb"] = "connected"
    except Exception:
        status["mongodb"] = "disconnected"
    
    # Check VLM service
    if settings.MEDGEMMA_REMOTE_URL:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.MEDGEMMA_REMOTE_URL}/health")
                if response.status_code == 200:
                    data = response.json()
                    status["vlm_service"] = "connected"
                    status["vlm_model"] = data.get("model", "Unknown")
                    status["vlm_device"] = data.get("device", "Unknown")
                    status["timestamp"] = data.get("timestamp")
        except Exception as e:
            status["vlm_service"] = "disconnected"
            status["vlm_error"] = str(e)
    else:
        status["vlm_service"] = "not_configured"
    
    return status
