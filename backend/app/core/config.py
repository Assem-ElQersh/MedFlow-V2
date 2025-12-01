from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "medflow"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Google Cloud Storage
    GCS_BUCKET_NAME: str = "medflow-files"
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    
    # Application
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "MedFlow"
    DEBUG: bool = True
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

