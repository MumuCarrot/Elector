from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Credentials payload for ``/auth/login``.

    Attributes:
        email: User email.
        password: Plaintext password (minimum length enforced).

    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")


class RegisterRequest(BaseModel):
    """Payload for ``/auth/register`` and admin user create.

    Attributes:
        email: Unique login email.
        password: Initial password.
        phone: Optional contact phone.
        first_name: Optional given name.
        last_name: Optional family name.

    """

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    phone: Optional[str] = Field(None, description="User phone number")
    first_name: Optional[str] = Field(None, description="User first name")
    last_name: Optional[str] = Field(None, description="User last name")


class TokenResponse(BaseModel):
    """Pair of JWT strings returned by auth service (also set as cookies).

    Attributes:
        access_token: Short-lived JWT.
        refresh_token: Long-lived JWT with ``jti``.

    """

    access_token: str
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    """Optional body-based refresh (cookies are primary in this API).

    Attributes:
        refresh_token: Refresh JWT if not using cookies.

    """

    refresh_token: Optional[str] = Field(None, description="Refresh token")