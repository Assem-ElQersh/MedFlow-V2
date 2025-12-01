from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from typing import Optional

class Database:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


db = Database()


async def get_database() -> AsyncIOMotorDatabase:
    return db.db


async def connect_to_mongo():
    """Connect to MongoDB on application startup"""
    db.client = AsyncIOMotorClient(settings.MONGODB_URL)
    db.db = db.client[settings.MONGODB_DB_NAME]
    
    # Create indexes
    await create_indexes()
    
    print(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")


async def close_mongo_connection():
    """Close MongoDB connection on application shutdown"""
    if db.client:
        db.client.close()
        print("Closed MongoDB connection")


async def create_indexes():
    """Create database indexes for optimal performance"""
    
    # Patients collection indexes
    await db.db.patients.create_index("patient_id", unique=True)
    await db.db.patients.create_index("national_id", unique=True)
    await db.db.patients.create_index("phone_primary")
    await db.db.patients.create_index([("name", "text")])
    
    # Sessions collection indexes
    await db.db.sessions.create_index("session_id", unique=True)
    await db.db.sessions.create_index("patient_id")
    await db.db.sessions.create_index("session_date")
    await db.db.sessions.create_index("session_status")
    await db.db.sessions.create_index("assigned_doctor_id")
    
    # Users collection indexes
    await db.db.users.create_index("user_id", unique=True)
    await db.db.users.create_index("username", unique=True)
    await db.db.users.create_index("email", unique=True, sparse=True)
    
    # Note: _id is automatically indexed by MongoDB, no need to create it
    
    print("Database indexes created")


async def get_next_sequence(sequence_name: str) -> int:
    """Get next value for auto-incrementing sequences"""
    result = await db.db.counters.find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"sequence_value": 1}},
        upsert=True,
        return_document=True
    )
    return result["sequence_value"]

