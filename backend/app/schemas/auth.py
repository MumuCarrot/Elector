from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Schema for user login request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")


class RegisterRequest(BaseModel):
    """Schema for user registration request."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    phone: Optional[str] = Field(None, description="User phone number")
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: Optional[str] = Field(None, description="Refresh token")