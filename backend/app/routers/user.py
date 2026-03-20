from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.dependencies.database import get_db
from app.schemas.user import UserCreate, UserUpdate
from app.services.user import user_service

router = APIRouter(tags=["users"])
logger = get_logger("user_router")


@router.post("", status_code=201)
async def create_user(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Creates a user and default profile (admin-style endpoint).

    Args:
        user_data: Registration payload.
        session: DB session.

    Returns:
        JSONResponse: 201 with user JSON.

    """
    logger.info(f"Creating user with email: {user_data.email}")

    user = await user_service.create_user(session, user_data)

    logger.info(f"User created successfully: {user.id}")

    return JSONResponse(
        content=user.model_dump(mode="json"), status_code=201
    )


@router.get("")
async def get_all_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page"),
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Paginated user listing.

    Args:
        page: Page index.
        page_size: Items per page.
        session: DB session.

    Returns:
        JSONResponse: Array of users.

    """
    logger.info(f"Getting all users - page: {page}, page_size: {page_size}")

    users = await user_service.get_all_users(session, page=page, page_size=page_size)

    response_data = [user.model_dump(mode="json") for user in users]

    return JSONResponse(content=response_data)


@router.get("/{user_id}")
async def get_user_by_id(
    user_id: str,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Fetches one user by id.

    Args:
        user_id: User primary key.
        session: DB session.

    Returns:
        JSONResponse: User JSON.

    Raises:
        UserNotFoundError: When id unknown.

    """
    logger.info(f"Getting user: {user_id}")

    user = await user_service.get_user_by_id(session, user_id)

    if not user:
        from app.exceptions.user import UserNotFoundError

        raise UserNotFoundError(f"User with id {user_id} not found")

    return JSONResponse(content=user.model_dump(mode="json"))


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Partial user update including optional password change.

    Args:
        user_id: Target user id.
        user_data: Fields to apply.
        session: DB session.

    Returns:
        JSONResponse: Updated user JSON.

    """
    logger.info(f"Updating user: {user_id}")

    user = await user_service.update_user(session, user_id, user_data)

    logger.info(f"User updated successfully: {user.id}")

    return JSONResponse(content=user.model_dump(mode="json"))


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Deletes user by id.

    Args:
        user_id: Target id.
        session: DB session.

    Returns:
        JSONResponse: Success detail.

    """
    logger.info(f"Deleting user: {user_id}")

    await user_service.delete_user(session, user_id)

    logger.info(f"User deleted successfully: {user_id}")

    return JSONResponse(
        content={"detail": f"User with id {user_id} deleted successfully"},
        status_code=200,
    )
