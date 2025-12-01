"""
Initialize database with sample users and data
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.security import get_password_hash
from datetime import datetime


async def create_sample_users():
    """Create sample users for testing"""
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]
    
    # Initialize counters
    await db.counters.update_one(
        {"_id": "user_id"},
        {"$setOnInsert": {"sequence_value": 0}},
        upsert=True
    )
    await db.counters.update_one(
        {"_id": "patient_id"},
        {"$setOnInsert": {"sequence_value": 0}},
        upsert=True
    )
    await db.counters.update_one(
        {"_id": "session_id"},
        {"$setOnInsert": {"sequence_value": 0}},
        upsert=True
    )
    
    # Sample users
    users = [
        {
            "user_id": "A-00001",
            "username": "admin",
            "email": "admin@medflow.com",
            "full_name": "System Administrator",
            "role": "admin",
            "hashed_password": get_password_hash("admin123"),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        },
        {
            "user_id": "D-00001",
            "username": "doctor1",
            "email": "doctor1@medflow.com",
            "full_name": "Dr. Sarah Johnson",
            "role": "doctor",
            "hashed_password": get_password_hash("doctor123"),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        },
        {
            "user_id": "D-00002",
            "username": "doctor2",
            "email": "doctor2@medflow.com",
            "full_name": "Dr. Ahmed Hassan",
            "role": "doctor",
            "hashed_password": get_password_hash("doctor123"),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        },
        {
            "user_id": "N-00001",
            "username": "nurse1",
            "email": "nurse1@medflow.com",
            "full_name": "Fatma Hassan",
            "role": "nurse",
            "hashed_password": get_password_hash("nurse123"),
            "is_active": True,
            "created_at": datetime.utcnow(),
            "last_login": None
        }
    ]
    
    # Insert users if they don't exist
    for user in users:
        existing = await db.users.find_one({"username": user["username"]})
        if not existing:
            await db.users.insert_one(user)
            print(f"Created user: {user['username']} ({user['role']})")
        else:
            print(f"User already exists: {user['username']}")
    
    # Update counter
    await db.counters.update_one(
        {"_id": "user_id"},
        {"$set": {"sequence_value": 4}}
    )
    
    print("\nDatabase initialized successfully!")
    print("\nDefault credentials:")
    print("Admin:  username=admin,   password=admin123")
    print("Doctor: username=doctor1, password=doctor123")
    print("Doctor: username=doctor2, password=doctor123")
    print("Nurse:  username=nurse1,  password=nurse123")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(create_sample_users())

