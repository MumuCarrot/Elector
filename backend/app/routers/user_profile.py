from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.dependencies.database import get_db
from app.dependencies.token import get_current_user
from app.models.user import User
from app.schemas.user_profile import (
    UserProfileCreate,
    UserProfileUpdate,
)
from app.services.user_profile import user_profile_service

router = APIRouter(tags=["user-profiles"])
logger = get_logger("user_profile_router")


@router.post("", status_code=201)
async def create_user_profile(
    profile_data: UserProfileCreate,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Create a new user profile.
    """
    logger.info(f"Creating user profile for user: {profile_data.user_id}")

    profile = await user_profile_service.create_user_profile(
        session, profile_data
    )

    logger.info(f"User profile created successfully: {profile.id}")

    return JSONResponse(
        content=profile.model_dump(mode="json"), status_code=201
    )


@router.get("")
async def get_all_user_profiles(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get all user profiles with pagination.
    """
    logger.info(
        f"Getting all user profiles - page: {page}, page_size: {page_size}"
    )

    profiles = await user_profile_service.get_all_user_profiles(
        session, page=page, page_size=page_size
    )

    response_data = [profile.model_dump(mode="json") for profile in profiles]

    return JSONResponse(content=response_data)


@router.get("/me/profile")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get current user's profile.
    """
    logger.info(f"Getting profile for current user: {current_user.id}")

    profile = await user_profile_service.get_user_profile_by_user_id(
        session, current_user.id
    )

    if not profile:
        from app.exceptions.user import UserNotFoundError

        raise UserNotFoundError(
            f"User profile for user {current_user.id} not found"
        )

    return JSONResponse(content=profile.model_dump(mode="json"))


@router.get("/user/{user_id}")
async def get_user_profile_by_user_id(
    user_id: str,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get user profile by user ID.
    """
    logger.info(f"Getting user profile for user: {user_id}")

    profile = await user_profile_service.get_user_profile_by_user_id(
        session, user_id
    )

    if not profile:
        from app.exceptions.user import UserNotFoundError

        raise UserNotFoundError(
            f"User profile for user {user_id} not found"
        )

    return JSONResponse(content=profile.model_dump(mode="json"))


@router.get("/{profile_id}")
async def get_user_profile_by_id(
    profile_id: str,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Get user profile by ID.
    """
    logger.info(f"Getting user profile: {profile_id}")

    profile = await user_profile_service.get_user_profile_by_id(
        session, profile_id
    )

    if not profile:
        from app.exceptions.user import UserNotFoundError

        raise UserNotFoundError(
            f"User profile with id {profile_id} not found"
        )

    return JSONResponse(content=profile.model_dump(mode="json"))


@router.put("/me/profile")
async def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update current user's profile.
    """
    logger.info(f"Updating profile for current user: {current_user.id}")

    profile = await user_profile_service.update_user_profile_by_user_id(
        session, current_user.id, profile_data
    )

    logger.info(f"User profile updated successfully: {profile.id}")

    return JSONResponse(content=profile.model_dump(mode="json"))


@router.put("/user/{user_id}")
async def update_user_profile_by_user_id(
    user_id: str,
    profile_data: UserProfileUpdate,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update user profile by user ID.
    """
    logger.info(f"Updating user profile for user: {user_id}")

    profile = await user_profile_service.update_user_profile_by_user_id(
        session, user_id, profile_data
    )

    logger.info(f"User profile updated successfully: {profile.id}")

    return JSONResponse(content=profile.model_dump(mode="json"))


@router.put("/{profile_id}")
async def update_user_profile(
    profile_id: str,
    profile_data: UserProfileUpdate,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Update user profile information.
    """
    logger.info(f"Updating user profile: {profile_id}")

    profile = await user_profile_service.update_user_profile(
        session, profile_id, profile_data
    )

    logger.info(f"User profile updated successfully: {profile.id}")

    return JSONResponse(content=profile.model_dump(mode="json"))


@router.delete("/me/profile")
async def delete_my_profile(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete current user's profile.
    """
    logger.info(f"Deleting profile for current user: {current_user.id}")

    await user_profile_service.delete_user_profile_by_user_id(
        session, current_user.id
    )

    logger.info(f"User profile deleted successfully for user: {current_user.id}")

    return JSONResponse(
        content={
            "detail": f"User profile for user {current_user.id} deleted successfully"
        },
        status_code=200,
    )


@router.delete("/user/{user_id}")
async def delete_user_profile_by_user_id(
    user_id: str,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete user profile by user ID.
    """
    logger.info(f"Deleting user profile for user: {user_id}")

    await user_profile_service.delete_user_profile_by_user_id(session, user_id)

    logger.info(f"User profile deleted successfully for user: {user_id}")

    return JSONResponse(
        content={
            "detail": f"User profile for user {user_id} deleted successfully"
        },
        status_code=200,
    )


@router.delete("/{profile_id}")
async def delete_user_profile(
    profile_id: str,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Delete user profile by ID.
    """
    logger.info(f"Deleting user profile: {profile_id}")

    await user_profile_service.delete_user_profile(session, profile_id)

    logger.info(f"User profile deleted successfully: {profile_id}")

    return JSONResponse(
        content={
            "detail": f"User profile with id {profile_id} deleted successfully"
        },
        status_code=200,
    )
