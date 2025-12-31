from celery import Task
from celery_app import celery_app
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.services.medgemma_service import medgemma_service
from app.models.session import SessionStatus
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database connection"""
    _db_client = None
    
    @property
    def db_client(self):
        if self._db_client is None:
            self._db_client = AsyncIOMotorClient(settings.MONGODB_URL)
        return self._db_client
    
    @property
    def db(self):
        return self.db_client[settings.MONGODB_DB_NAME]


@celery_app.task(bind=True, base=DatabaseTask, name='vlm_tasks.process_session')
def process_session_vlm(self, session_id: str):
    """Process session with VLM (mock implementation)"""
    
    async def _process():
        try:
            # Update status to vlm_processing
            now = datetime.utcnow()
            await self.db.sessions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "session_status": SessionStatus.vlm_processing,
                        "vlm_initial_status": "processing",
                        "vlm_initial_triggered_at": now,
                        "last_updated": now
                    },
                    "$push": {
                        "status_history": {
                            "status": SessionStatus.vlm_processing,
                            "timestamp": now,
                            "user_id": "system"
                        }
                    }
                }
            )
            
            # Get session data
            session = await self.db.sessions.find_one({"session_id": session_id})
            if not session:
                raise Exception(f"Session {session_id} not found")
            
            # Get patient data
            patient = await self.db.patients.find_one({"patient_id": session["patient_id"]})
            if not patient:
                raise Exception(f"Patient {session['patient_id']} not found")
            
            # Prepare patient context
            patient_context = {
                "age": patient.get("age"),
                "sex": patient.get("sex"),
                "chronic_diseases": patient.get("chronic_diseases", []),
                "current_medications": [m.get("name") for m in patient.get("current_medications", [])]
            }
            
            # Get last session summary if this is a follow-up
            last_session_summary = None
            if session.get("session_type") == "follow_up" and session.get("parent_session_id"):
                last_session = await self.db.sessions.find_one(
                    {"session_id": session["parent_session_id"]}
                )
                if last_session and last_session.get("diagnosis"):
                    diagnosis = last_session["diagnosis"]
                    last_session_summary = (
                        f"Previous diagnosis: {diagnosis.get('primary_diagnosis')}. "
                        f"Notes: {diagnosis.get('doctor_notes', 'N/A')}"
                    )
            
            # Check if HF_TOKEN is set - fail immediately if not
            if not settings.HF_TOKEN:
                raise Exception("HF_TOKEN not configured. VLM processing requires valid Hugging Face token.")
            
            # Process with real VLM only (MedGemma or BioGPT)
            logger.info(f"Processing session {session_id} with real VLM (MedGemma/BioGPT)")
            vlm_output = medgemma_service.process_initial_session(
                patient_context=patient_context,
                chief_complaint=session["chief_complaint"],
                current_state=session["current_state_description"],
                last_session_summary=last_session_summary,
                files_count=len(session.get("uploaded_files", []))
            )
            
            # Prepare VLM input for record
            vlm_input = {
                "patient_context": patient_context,
                "last_session_summary": last_session_summary,
                "chief_complaint": session["chief_complaint"],
                "current_state": session["current_state_description"],
                "files_count": len(session.get("uploaded_files", []))
            }
            
            # Update session with VLM results
            now = datetime.utcnow()
            await self.db.sessions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "session_status": SessionStatus.awaiting_doctor,
                        "vlm_initial_status": "completed",
                        "vlm_initial_completed_at": now,
                        "vlm_initial_input": vlm_input,
                        "vlm_initial_output": vlm_output,
                        "last_updated": now
                    },
                    "$push": {
                        "status_history": {
                            "status": SessionStatus.awaiting_doctor,
                            "timestamp": now,
                            "user_id": "system"
                        }
                    }
                }
            )
            
            return {"success": True, "session_id": session_id}
            
        except Exception as e:
            # Update status to vlm_failed with error details
            error_message = str(e)
            logger.error(f"VLM processing failed for session {session_id}: {error_message}")
            now = datetime.utcnow()
            await self.db.sessions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "session_status": SessionStatus.vlm_failed,
                        "vlm_initial_status": "failed",
                        "vlm_error_message": error_message,
                        "last_updated": now
                    },
                    "$push": {
                        "status_history": {
                            "status": SessionStatus.vlm_failed,
                            "timestamp": now,
                            "user_id": "system"
                        }
                    }
                }
            )
            # Don't re-raise - task succeeded in marking as failed
            return {"success": True, "session_id": session_id, "vlm_status": "failed"}
    
    # Run async function
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(_process())

