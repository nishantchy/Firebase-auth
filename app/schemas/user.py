from sqlmodel import SQLModel
from datetime import datetime
from typing import Optional
from app.models.user import AuthProvider
from pydantic import EmailStr

class UserCreate(SQLModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None

class UserCreateWithFirebase(SQLModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None
    firebase_uid: str  # Firebase UID from frontend

class UserLogin(SQLModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(SQLModel):
    id_token: str

class UserLoginResponse(SQLModel):
    email: EmailStr
    display_name: Optional[str]
    photo_url: Optional[str]
    auth_provider: AuthProvider
    is_email_verified: bool

class UserResponse(SQLModel):
    id: int
    firebase_uid: str
    email: EmailStr
    display_name: Optional[str]
    photo_url: Optional[str]
    auth_provider: AuthProvider
    is_email_verified: bool
    is_active: bool
    created_at: datetime

class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
    user: UserLoginResponse


class HiddenResponse(SQLModel):
    email: EmailStr
    display_name: Optional[str]
    photo_url: Optional[str]
