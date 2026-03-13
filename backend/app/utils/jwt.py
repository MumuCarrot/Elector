from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional, Union
from uuid import uuid4

import jwt
from fastapi import Request
from jwt import InvalidTokenError

from app.core.logging_config import get_logger
from app.core.settings import settings
from app.db.redis_client import get_cache, set_cache
from app.exceptions.user import TokenNotFoundError

logger = get_logger("jwt_utils")


class JwtScenario(Enum):
    """JWT authentication scenarios."""
    AUTH_LOCAL = "auth_local"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _create_token(
    subject: int,
    expires_delta: timedelta,
    token_type: str = "access",
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    now = _utcnow()
    expire_at = now + expires_delta

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "exp": int(expire_at.timestamp()),
        "iss": f"https://{settings.app_settings.APP_HOST}",
        "aud": f"https://{settings.app_settings.APP_HOST}/api",
    }
    if additional_claims:
        payload.update(additional_claims)

    token = jwt.encode(
        payload,
        settings.auth_settings.AUTH_PRIVATE_KEY,
        algorithm=settings.auth_settings.AUTH_ALGORITHM,
    )
    return token


def create_access_token(
    subject: int,
    expires_minutes: Optional[int] = None,
    claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a signed JWT access token for the given subject.
    """

    minutes = (
        expires_minutes
        if expires_minutes is not None
        else settings.auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return _create_token(
        subject=subject,
        expires_delta=timedelta(minutes=minutes),
        token_type="access",
        additional_claims=claims,
    )


def create_refresh_token(
    subject: Union[str, int],
    expires_days: Optional[int] = None,
    claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a signed JWT refresh token for the given subject.
    """

    days = (
        expires_days
        if expires_days is not None
        else settings.auth_settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    extra_claims: Dict[str, Any] = dict(claims) if claims else {}
    if "jti" not in extra_claims:
        extra_claims["jti"] = str(uuid4())

    return _create_token(
        subject=subject,
        expires_delta=timedelta(days=days),
        token_type="refresh",
        additional_claims=extra_claims,
    )


def create_pair_tokens(
    subject: int, claims: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """
    Create a pair of access and refresh tokens.
    """

    access_token = create_access_token(subject=subject, claims=claims)
    refresh_token = create_refresh_token(subject=subject, claims=claims)
    return {"access_token": access_token, "refresh_token": refresh_token}


def _decode_local_jwt(token: str, verify_exp: bool = True):
    """
    Decode a locally signed JWT token.
    """

    options = {"verify_aud": False, "verify_exp": verify_exp}
    payload = jwt.decode(
        token,
        settings.auth_settings.AUTH_PUBLIC_KEY,
        algorithms=[settings.auth_settings.AUTH_ALGORITHM],
        options=options,
    )
    return payload


def decode_jwt(
    scenario: JwtScenario, token: str, verify_exp: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Decode a JWT token based on the scenario.
    """

    if scenario == JwtScenario.AUTH_LOCAL:
        return _decode_local_jwt(token, verify_exp=verify_exp)
    # Alternative variants: Auth0 scenario
    # elif scenario == JwtScenario.AUTH0:
    #     return _decode_auth0_jwt(token)
    else:
        raise InvalidTokenError("Unknown token method")


def get_token_subject(token: str) -> str:
    """
    Return the subject (sub) claim from token. Raises if token is invalid.
    """

    payload = decode_jwt(JwtScenario.AUTH_LOCAL, token)
    if payload is None:
        raise InvalidTokenError("Invalid or expired token")
    subject = payload.get("sub")
    if subject is None:
        raise InvalidTokenError("Missing 'sub' in token")
    return str(subject)


def is_token_type(token: str, expected_type: str) -> bool:
    """
    Check token 'type' claim equals expected_type.
    """

    try:
        payload = decode_jwt(JwtScenario.AUTH_LOCAL, token)
        if payload is None:
            return False
        return payload.get("type") == expected_type
    except (InvalidTokenError, AttributeError):
        return False


async def blacklist_token(token: str) -> None:
    """
    Blacklist a JWT token.
    """
    logger.info("blacklist_token: Adding token to blacklist")

    await set_cache(
        f"blacklist:{token}",
        "1",
        settings.auth_settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


async def is_token_blacklisted(token: str) -> bool:
    """
    Check if a JWT token is blacklisted.
    """

    return await get_cache(f"blacklist:{token}") == "1"


def get_bearer_token(request: Request) -> dict:
    """
    Get token from request cookies.
    """
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        logger.info(
            f"Token from cookie (length={len(cookie_token)}): {cookie_token[:50] if len(cookie_token) > 50 else cookie_token}"
        )
        return {"method": JwtScenario.AUTH_LOCAL, "token": cookie_token}

    logger.warning(f"No token found. Cookies available: {list(request.cookies.keys())}")
    raise TokenNotFoundError("Missing token (no access_token cookie found)")