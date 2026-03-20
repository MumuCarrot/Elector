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
    """Supported JWT verification strategies."""

    AUTH_LOCAL = "auth_local"


def _utcnow() -> datetime:
    """Returns current UTC time with timezone awareness."""
    return datetime.now(timezone.utc)


def _create_token(
    subject: int,
    expires_delta: timedelta,
    token_type: str = "access",
    additional_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Builds and signs a JWT with RS256.

    Args:
        subject: Numeric user id stored in ``sub`` (stringified).
        expires_delta: Lifetime from issuance.
        token_type: ``access`` or ``refresh`` claim.
        additional_claims: Merged into payload (e.g. ``jti`` for refresh).

    Returns:
        str: Encoded JWT.

    """
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
    """Creates a short-lived access JWT.

    Args:
        subject: User id.
        expires_minutes: Override default from settings if provided.
        claims: Optional extra payload fields.

    Returns:
        str: Signed access token.

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
    """Creates a long-lived refresh JWT with a random ``jti`` unless provided.

    Args:
        subject: User id (string or int, coerced in payload).
        expires_days: Override default refresh lifetime.
        claims: Optional extra claims.

    Returns:
        str: Signed refresh token.

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
    """Issues matching access and refresh tokens for login/register flows.

    Args:
        subject: User id.
        claims: Optional shared extra claims.

    Returns:
        dict: Keys ``access_token`` and ``refresh_token``.

    """
    access_token = create_access_token(subject=subject, claims=claims)
    refresh_token = create_refresh_token(subject=subject, claims=claims)
    return {"access_token": access_token, "refresh_token": refresh_token}


def _decode_local_jwt(token: str, verify_exp: bool = True) -> Dict[str, Any]:
    """Decodes a token signed with the app's RSA public key.

    Args:
        token: JWT string.
        verify_exp: Whether to enforce ``exp``.

    Returns:
        dict: JWT payload.

    Raises:
        jwt.InvalidTokenError: On bad signature, expiry, or format.

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
    """Dispatches decode by scenario (currently only local RSA).

    Args:
        scenario: Verification strategy enum value.
        token: JWT string.
        verify_exp: Passed to decoder.

    Returns:
        dict | None: Payload for ``AUTH_LOCAL``; None is not returned today.

    Raises:
        InvalidTokenError: Unknown scenario.

    """
    if scenario == JwtScenario.AUTH_LOCAL:
        return _decode_local_jwt(token, verify_exp=verify_exp)
    raise InvalidTokenError("Unknown token method")


def get_token_subject(token: str) -> str:
    """Reads string ``sub`` claim from a valid access/refresh token.

    Args:
        token: JWT string.

    Returns:
        str: Subject user id as string.

    Raises:
        InvalidTokenError: Invalid token or missing ``sub``.

    """
    payload = decode_jwt(JwtScenario.AUTH_LOCAL, token)
    if payload is None:
        raise InvalidTokenError("Invalid or expired token")
    subject = payload.get("sub")
    if subject is None:
        raise InvalidTokenError("Missing 'sub' in token")
    return str(subject)


def is_token_type(token: str, expected_type: str) -> bool:
    """Compares JWT ``type`` claim without raising on malformed tokens.

    Args:
        token: JWT string.
        expected_type: Expected ``type`` value (e.g. ``access``).

    Returns:
        bool: True if decode succeeds and types match.

    """
    try:
        payload = decode_jwt(JwtScenario.AUTH_LOCAL, token)
        if payload is None:
            return False
        return payload.get("type") == expected_type
    except (InvalidTokenError, AttributeError):
        return False


async def blacklist_token(token: str) -> None:
    """Stores a token id in Redis until refresh TTL elapses.

    Args:
        token: Full JWT string used as part of the Redis key.

    """
    logger.info("blacklist_token: Adding token to blacklist")

    await set_cache(
        f"blacklist:{token}",
        "1",
        settings.auth_settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


async def is_token_blacklisted(token: str) -> bool:
    """Checks Redis for a blacklist marker.

    Args:
        token: Full JWT string.

    Returns:
        bool: True if blacklisted.

    """
    return await get_cache(f"blacklist:{token}") == "1"


def get_bearer_token(request: Request) -> dict:
    """Extracts access JWT from cookies for local auth.

    Args:
        request: HTTP request.

    Returns:
        dict: ``{"method": JwtScenario.AUTH_LOCAL, "token": ...}``.

    Raises:
        TokenNotFoundError: No ``access_token`` cookie.

    """
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        logger.info(
            f"Token from cookie (length={len(cookie_token)}): {cookie_token[:50] if len(cookie_token) > 50 else cookie_token}"
        )
        return {"method": JwtScenario.AUTH_LOCAL, "token": cookie_token}

    logger.warning(f"No token found. Cookies available: {list(request.cookies.keys())}")
    raise TokenNotFoundError("Missing token (no access_token cookie found)")
