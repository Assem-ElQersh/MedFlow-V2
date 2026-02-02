from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
from typing import Optional, Dict, Any, List
import uuid
from app.models.log import LogEntry, LogLevel, LogCategory


class LogService:
    """Service for logging system events"""
    
    async def create_log(
        self,
        db: AsyncIOMotorDatabase,
        level: LogLevel,
        category: LogCategory,
        message: str,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None,
        user_role: Optional[str] = None,
        session_id: Optional[str] = None,
        patient_id: Optional[str] = None,
        patient_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> str:
        """Create a new log entry"""
        log_id = f"LOG-{uuid.uuid4().hex[:12].upper()}"
        
        log_doc = {
            "log_id": log_id,
            "timestamp": datetime.utcnow(),
            "level": level,
            "category": category,
            "message": message,
            "user_id": user_id,
            "user_name": user_name,
            "user_role": user_role,
            "session_id": session_id,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "details": details or {},
            "ip_address": ip_address
        }
        
        await db.logs.insert_one(log_doc)
        return log_id
    
    async def get_logs(
        self,
        db: AsyncIOMotorDatabase,
        category: Optional[LogCategory] = None,
        level: Optional[LogLevel] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[LogEntry]:
        """Get logs with optional filters"""
        query = {}
        
        if category:
            query["category"] = category
        if level:
            query["level"] = level
        if user_id:
            query["user_id"] = user_id
        
        cursor = db.logs.find(query).sort("timestamp", -1).skip(skip).limit(limit)
        logs = await cursor.to_list(length=limit)
        
        return [LogEntry(**log) for log in logs]
    
    async def get_logs_count(
        self,
        db: AsyncIOMotorDatabase,
        category: Optional[LogCategory] = None,
        level: Optional[LogLevel] = None
    ) -> int:
        """Get total count of logs"""
        query = {}
        if category:
            query["category"] = category
        if level:
            query["level"] = level
        
        return await db.logs.count_documents(query)
    
    async def get_recent_logs(
        self,
        db: AsyncIOMotorDatabase,
        limit: int = 50
    ) -> List[LogEntry]:
        """Get most recent logs"""
        cursor = db.logs.find().sort("timestamp", -1).limit(limit)
        logs = await cursor.to_list(length=limit)
        return [LogEntry(**log) for log in logs]


log_service = LogService()
