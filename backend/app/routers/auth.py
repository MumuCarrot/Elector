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
from app.schemas.user import UserResponse
from app.services.auth import auth_service

router = APIRouter(tags=["auth"])
logger = get_logger("auth_router")


@router.post("/register", status_code=201)
async def register(
    request: Request,
    register_data: RegisterRequest,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Register a new user. Tokens are set in httpOnly cookies.
    """
    logger.info(f"Registration request for email: {register_data.email}")

    user, tokens = await auth_service.register(request, session, register_data)

    logger.info(f"User registered successfully: {user.id}")
    
    response_data = {
        "user": UserResponse.model_validate(user).model_dump(mode='json'),
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
    """
    Authenticate user. Tokens are set in httpOnly cookies.
    """
    logger.info(f"Login request for email: {login_data.email}")

    user, tokens = await auth_service.login(request, session, login_data)

    logger.info(f"User logged in successfully: {user.id}")
    
    response_data = {
        "user": user.model_dump(mode='json'),
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
    """
    Refresh access token using refresh token. New tokens are set in httpOnly cookies.
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
    """
    Logout user by blacklisting tokens.
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
    """
    Get current authenticated user information.
    """
    logger.info(f"Getting current user info for user: {current_user.id}")
    
    user_response = UserResponse.model_validate(current_user)
    
    return JSONResponse(content=user_response.model_dump(mode='json'))