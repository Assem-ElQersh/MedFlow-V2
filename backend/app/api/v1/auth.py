from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from app.models.user import UserCreate, User, Token, LoginRequest, UserInDB
from app.core.database import get_database, get_next_sequence
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user
)
from motor.motor_asyncio import AsyncIOMotorDatabase

router = APIRouter()


async def get_user_by_username(db: AsyncIOMotorDatabase, username: str):
    """Get user by username"""
    user = await db.users.find_one({"username": username})
    return user


async def create_user_in_db(db: AsyncIOMotorDatabase, user_create: UserCreate) -> User:
    """Create a new user in database"""
    # Check if username already exists
    existing_user = await get_user_by_username(db, user_create.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Generate user_id
    sequence = await get_next_sequence("user_id")
    user_id = f"{user_create.role[0].upper()}-{sequence:05d}"
    
    # Hash password
    hashed_password = get_password_hash(user_create.password)
    
    # Create user document
    user_dict = {
        "user_id": user_id,
        "username": user_create.username,
        "email": user_create.email,
        "full_name": user_create.full_name,
        "role": user_create.role,
        "hashed_password": hashed_password,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    }
    
    await db.users.insert_one(user_dict)
    
    return User(**{k: v for k, v in user_dict.items() if k != "hashed_password"})


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Register a new user (admin only in production)"""
    user = await create_user_in_db(db, user_create)
    return user


@router.post("/login", response_model=Token)
async def login(
    login_request: LoginRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Login with username and password"""
    # Get user from database
    user_doc = await get_user_by_username(db, login_request.username)
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Verify password
    if not verify_password(login_request.password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Check if user is active
    if not user_doc.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Update last login
    await db.users.update_one(
        {"username": login_request.username},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": user_doc["user_id"],
            "username": user_doc["username"],
            "role": user_doc["role"]
        }
    )
    
    # Prepare user object
    user = User(**{k: v for k, v in user_doc.items() if k not in ["_id", "hashed_password"]})
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        user=user
    )


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get current logged in user information"""
    user_doc = await db.users.find_one({"user_id": current_user["user_id"]})
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return User(**{k: v for k, v in user_doc.items() if k not in ["_id", "hashed_password"]})


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout current user (client should remove token)"""
    return {"message": "Successfully logged out"}

