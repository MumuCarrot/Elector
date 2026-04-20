from datetime import date, datetime
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, field_validator


class UserProfileBase(BaseModel):
    """Base schema for UserProfile with common fields."""

    birth_date: Optional[date] = None
    avatar_url: Optional[str] = None
    address: Optional[str] = None

    @field_validator("birth_date")
    @classmethod
    def birth_date_not_in_future(cls, v: Optional[date]) -> Optional[date]:
        """Disallow future dates (cannot be later than today)."""
        if v is not None and v > date.today():
            raise ValueError("Birth date cannot be later than today")
        return v

    @field_validator("avatar_url")
    @classmethod
    def avatar_url_http_only(cls, v: Optional[str]) -> Optional[str]:
        """Require http(s) when set; empty string becomes None."""
        if v is not None and str(v).strip() == "":
            return None
        if v is not None:
            parsed = urlparse(v)
            if parsed.scheme not in ("http", "https"):
                raise ValueError("Avatar URL must use http or https")
        return v


class UserProfileCreate(UserProfileBase):
    """Schema for creating a new user profile."""

    user_id: str


class UserProfileUpdate(UserProfileBase):
    """Schema for updating user profile (partial fields, all optional)."""

    pass


class UserProfileResponse(UserProfileBase):
    """Schema for user profile response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    created_at: Optional[datetime] = None

