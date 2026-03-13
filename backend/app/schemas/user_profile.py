from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UserProfileBase(BaseModel):
    """Base schema for UserProfile with common fields."""

    birth_date: Optional[date] = None
    avatar_url: Optional[str] = None
    address: Optional[str] = None


class UserProfileCreate(UserProfileBase):
    """Schema for creating a new user profile."""

    user_id: str


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile."""

    birth_date: Optional[date] = None
    avatar_url: Optional[str] = None
    address: Optional[str] = None


class UserProfileResponse(UserProfileBase):
    """Schema for user profile response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    created_at: Optional[datetime] = None

