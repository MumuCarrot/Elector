from typing import Optional

from fastapi import Cookie, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.dependencies.database import get_db
from app.exceptions.user import (
    InvalidTokenTypeError,
    TokenBlacklistedError,
    TokenNotFoundError,
)
from app.models import User
from app.services.user import user_service
from app.utils.jwt import is_token_blacklisted, is_token_type

logger = get_logger("token_dependency")


async def get_access_token_from_cookie(
    access_token: Optional[str] = Cookie(None),
) -> str:
    """
    Extract access token from cookies.
    """
    if not access_token:
        logger.warning("No access token found in cookies")
        raise TokenNotFoundError("No access token found in cookies")
    return access_token


async def get_refresh_token_from_cookie(
    request: Request,
) -> str | None:
    """
    Extract refresh token from cookies.
    """
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        return None
    return refresh_token


async def validate_refresh_token(
    refresh_token: str = Depends(get_refresh_token_from_cookie),
) -> str:
    """
    Validate refresh token (not blacklisted and correct type).
    """

    if not is_token_type(refresh_token, "refresh"):
        logger.warning("validate_refresh_token: Invalid refresh token type")
        raise InvalidTokenTypeError("Invalid token type")

    is_blacklisted = await is_token_blacklisted(refresh_token)

    if is_blacklisted:
        logger.warning(
            "validate_refresh_token: Attempted to use blacklisted refresh token"
        )
        raise TokenBlacklistedError("Token is blacklisted")

    logger.info("validate_refresh_token: Token validation successful")
    return refresh_token


async def validate_access_token(
    access_token: str = Depends(get_access_token_from_cookie),
) -> str:
    """
    Validate access token (correct type).
    """
    if not is_token_type(access_token, "access"):
        logger.warning("Invalid access token type")
        raise InvalidTokenTypeError("Invalid token type")

    return access_token


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> User:
    """
    Get current authenticated user from token.
    """
    return await user_service.get_user_by_token(request, session)


async def get_optional_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Get current authenticated user from token if available, otherwise return None.
    """
    try:
        return await user_service.get_user_by_token(request, session)
    except Exception:
        return None