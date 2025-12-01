from google.cloud import storage
from datetime import timedelta
from typing import Optional
from app.core.config import settings
import os


class StorageService:
    def __init__(self):
        self.bucket_name = settings.GCS_BUCKET_NAME
        self.client = None
        self.bucket = None
        
        # Initialize GCS client if credentials are provided
        if settings.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS):
            self.client = storage.Client()
            self.bucket = self.client.bucket(self.bucket_name)
    
    async def upload_file(
        self,
        file_content: bytes,
        destination_path: str,
        content_type: str
    ) -> str:
        """Upload file to Google Cloud Storage"""
        if not self.client:
            # Mock mode for development without GCS
            return f"mock://storage/{destination_path}"
        
        blob = self.bucket.blob(destination_path)
        blob.upload_from_string(file_content, content_type=content_type)
        
        return f"gs://{self.bucket_name}/{destination_path}"
    
    async def get_signed_url(self, file_path: str, expiration_minutes: int = 30) -> str:
        """Generate a signed URL for file access"""
        if file_path.startswith("mock://"):
            # Return mock URL for development
            return file_path
        
        if not self.client:
            return file_path
        
        # Extract blob name from gs:// path
        blob_name = file_path.replace(f"gs://{self.bucket_name}/", "")
        blob = self.bucket.blob(blob_name)
        
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET"
        )
        
        return url
    
    async def delete_file(self, file_path: str) -> bool:
        """Delete file from Google Cloud Storage"""
        if file_path.startswith("mock://"):
            # Mock deletion for development
            return True
        
        if not self.client:
            return True
        
        try:
            blob_name = file_path.replace(f"gs://{self.bucket_name}/", "")
            blob = self.bucket.blob(blob_name)
            blob.delete()
            return True
        except Exception:
            return False


# Singleton instance
storage_service = StorageService()

