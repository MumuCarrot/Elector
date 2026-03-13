from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base schema for User with common fields."""

    email: EmailStr
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, description="User password")


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    password: Optional[str] = Field(
        None, min_length=8, description="User password"
    )


class UserResponse(UserBase):
    """Schema for user response (excluding sensitive data)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: Optional[datetime] = None


class UserInDB(UserBase):
    """Schema for user in database (includes password_hash)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    password_hash: str
    created_at: Optional[datetime] = None

