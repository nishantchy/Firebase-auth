from sqlmodel import SQLModel, Field, Column
from sqlalchemy import String, DateTime, Boolean
from datetime import datetime
from typing import Optional
from enum import Enum

class AuthProvider(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    firebase_uid: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    password: Optional[str] = None  # For email/password auth, Not needed for Google auth
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    auth_provider: AuthProvider = Field(default=AuthProvider.EMAIL)
    is_email_verified: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


