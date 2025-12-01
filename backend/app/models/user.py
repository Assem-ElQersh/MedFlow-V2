from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    doctor = "doctor"
    nurse = "nurse"


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: str = Field(..., min_length=2, max_length=200)
    role: UserRole


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None


class User(UserBase):
    user_id: str
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: User


class LoginRequest(BaseModel):
    username: str
    password: str

