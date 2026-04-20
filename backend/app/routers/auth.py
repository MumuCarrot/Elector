from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.dependencies.database import get_db
from app.dependencies.token import (
    get_access_token_from_cookie,
    get_current_user,
    validate_refresh_token,
)
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
)
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.services.auth import auth_service
from app.services.user import user_service

router = APIRouter(tags=["auth"])
logger = get_logger("auth_router")


@router.post("/register", status_code=201)
async def register(
    request: Request,
    register_data: RegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Creates a user and returns JSON user plus sets httpOnly auth cookies.

    Args:
        request: HTTP request (unused; reserved).
        register_data: Email, password, and profile fields.
        session: DB session.

    Returns:
        JSONResponse: 201 with ``user`` object; cookies carry tokens.

    """
    logger.info(f"Registration request for email: {register_data.email}")

    user, tokens = await auth_service.register(request, session, register_data)

    logger.info(f"User registered successfully: {user.id}")

    response_data = {
        "user": UserResponse.model_validate(user).model_dump(mode="json"),
    }

    json_response = JSONResponse(content=response_data, status_code=201)
    auth_service.set_tokens_in_cookies(json_response, tokens)

    return json_response


@router.post("/login")
async def login(
    request: Request,
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Authenticates credentials and sets token cookies.

    Args:
        request: HTTP request.
        login_data: Email and password.
        session: DB session.

    Returns:
        JSONResponse: ``user`` payload and cookies.

    Raises:
        InvalidCredentialsError: Bad email/password.

    """
    logger.info(f"Login request for email: {login_data.email}")

    user, tokens = await auth_service.login(request, session, login_data)

    logger.info(f"User logged in successfully: {user.id}")

    response_data = {
        "user": user.model_dump(mode="json"),
    }

    json_response = JSONResponse(content=response_data)
    auth_service.set_tokens_in_cookies(json_response, tokens)

    return json_response


@router.post("/refresh")
async def refresh(
    request: Request,
    refresh_token: str = Depends(validate_refresh_token),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Rotates JWT pair; old refresh is blacklisted.

    Args:
        request: HTTP request.
        refresh_token: Validated refresh cookie string.
        session: DB session.

    Returns:
        JSONResponse: Success message and new cookies.

    """
    logger.info("Token refresh request")

    tokens = await auth_service.refresh_token(session, refresh_token)

    logger.info("Token refreshed successfully")

    json_response = JSONResponse(content={"detail": "Tokens refreshed successfully"})
    auth_service.set_tokens_in_cookies(json_response, tokens)

    return json_response


@router.post("/logout")
async def logout(
    request: Request,
    access_token: str = Depends(get_access_token_from_cookie),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Blacklists tokens and clears cookies.

    Args:
        request: For reading ``refresh_token`` cookie.
        access_token: Access JWT from cookie dependency.
        session: DB session (passed through for symmetry).

    Returns:
        JSONResponse: Logout confirmation JSON.

    """
    logger.info("Logout request")

    await auth_service.logout(request, session, access_token)

    logger.info("User logged out successfully")

    json_response = JSONResponse(content={"detail": "Logged out successfully"})
    auth_service.clear_tokens_in_cookies(json_response)

    return json_response


@router.get("/me")
async def get_me(
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    """Returns the authenticated user's public fields.

    Args:
        current_user: From JWT cookie validation.

    Returns:
        JSONResponse: Serialized ``UserResponse``.

    """
    logger.info(f"Getting current user info for user: {current_user.id}")

    user_response = UserResponse.model_validate(current_user)

    return JSONResponse(content=user_response.model_dump(mode="json"))


@router.put("/me")
async def update_me(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Updates the authenticated user's account fields (email, phone, names, optional password).

    Args:
        user_data: Partial ``UserUpdate`` payload.
        current_user: Authenticated user from JWT.
        session: DB session.

    Returns:
        JSONResponse: Updated ``UserResponse``.

    """
    logger.info(f"Updating current user: {current_user.id}")

    updated = await user_service.update_user(session, current_user.id, user_data)

    return JSONResponse(content=updated.model_dump(mode="json"))
