from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.exceptions.user import UserNotFoundError, ValidationError
from app.models.user import User
from app.models.user_profile import UserProfile
from app.repository.user_profile_repository import UserProfileRepository
from app.repository.user_repository import UserRepository
from app.schemas.user_profile import (
    UserProfileCreate,
    UserProfileUpdate,
    UserProfileResponse,
)

logger = get_logger("user_profile_service")


class UserProfileService:
    """Service for user profile CRUD operations."""

    @staticmethod
    async def create_user_profile(
        session: AsyncSession, profile_data: UserProfileCreate
    ) -> UserProfileResponse:
        """Create a new user profile."""
        logger.info(f"Creating user profile for user: {profile_data.user_id}")

        user_repo = UserRepository(session)
        user = await user_repo.read_one(condition=User.id == profile_data.user_id)

        if not user:
            logger.warning(f"User with id {profile_data.user_id} not found")
            raise UserNotFoundError(f"User with id {profile_data.user_id} not found")

        repository = UserProfileRepository(session)
        existing_profile = await repository.read_one(
            condition=UserProfile.user_id == profile_data.user_id
        )

        if existing_profile:
            logger.warning(
                f"User profile for user {profile_data.user_id} already exists"
            )
            raise ValidationError(
                f"User profile for user {profile_data.user_id} already exists"
            )

        new_profile = UserProfile(
            user_id=profile_data.user_id,
            birth_date=profile_data.birth_date,
            avatar_url=profile_data.avatar_url,
            address=profile_data.address,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )

        created_profile = await repository.create(new_profile)
        logger.info(
            f"User profile created successfully with id: {created_profile.id}"
        )

        return UserProfileResponse.model_validate(created_profile)

    @staticmethod
    async def get_user_profile_by_id(
        session: AsyncSession, profile_id: str
    ) -> Optional[UserProfileResponse]:
        """Get user profile by ID."""
        logger.info(f"Getting user profile by id: {profile_id}")

        repository = UserProfileRepository(session)
        profile = await repository.read_one(
            condition=UserProfile.id == profile_id
        )

        if not profile:
            logger.warning(f"User profile with id {profile_id} not found")
            return None

        return UserProfileResponse.model_validate(profile)

    @staticmethod
    async def get_user_profile_by_user_id(
        session: AsyncSession, user_id: str
    ) -> Optional[UserProfileResponse]:
        """Get user profile by user ID."""
        logger.info(f"Getting user profile by user id: {user_id}")

        repository = UserProfileRepository(session)
        profile = await repository.read_one(
            condition=UserProfile.user_id == user_id
        )

        if not profile:
            logger.warning(f"User profile for user {user_id} not found")
            return None

        return UserProfileResponse.model_validate(profile)

    @staticmethod
    async def update_user_profile(
        session: AsyncSession, profile_id: str, profile_data: UserProfileUpdate
    ) -> UserProfileResponse:
        """Update user profile information."""
        logger.info(f"Updating user profile with id: {profile_id}")

        repository = UserProfileRepository(session)
        profile = await repository.read_one(
            condition=UserProfile.id == profile_id
        )

        if not profile:
            logger.warning(f"User profile with id {profile_id} not found")
            raise UserNotFoundError(f"User profile with id {profile_id} not found")

        update_dict = profile_data.model_dump(exclude_unset=True)

        updated_profile = await repository.update(
            data=update_dict, condition=UserProfile.id == profile_id
        )

        logger.info(f"User profile with id {profile_id} updated successfully")

        return UserProfileResponse.model_validate(updated_profile)

    @staticmethod
    async def update_user_profile_by_user_id(
        session: AsyncSession, user_id: str, profile_data: UserProfileUpdate
    ) -> UserProfileResponse:
        """Update user profile by user ID."""
        logger.info(f"Updating user profile for user: {user_id}")

        repository = UserProfileRepository(session)
        profile = await repository.read_one(
            condition=UserProfile.user_id == user_id
        )

        if not profile:
            logger.warning(f"User profile for user {user_id} not found")
            raise UserNotFoundError(
                f"User profile for user {user_id} not found"
            )

        update_dict = profile_data.model_dump(exclude_unset=True)

        updated_profile = await repository.update(
            data=update_dict, condition=UserProfile.user_id == user_id
        )

        logger.info(f"User profile for user {user_id} updated successfully")

        return UserProfileResponse.model_validate(updated_profile)

    @staticmethod
    async def delete_user_profile(
        session: AsyncSession, profile_id: str
    ) -> bool:
        """Delete user profile by ID."""
        logger.info(f"Deleting user profile with id: {profile_id}")

        repository = UserProfileRepository(session)
        deleted = await repository.delete(condition=UserProfile.id == profile_id)

        if not deleted:
            logger.warning(
                f"User profile with id {profile_id} not found for deletion"
            )
            raise UserNotFoundError(
                f"User profile with id {profile_id} not found"
            )

        logger.info(f"User profile with id {profile_id} deleted successfully")
        return True

    @staticmethod
    async def delete_user_profile_by_user_id(
        session: AsyncSession, user_id: str
    ) -> bool:
        """Delete user profile by user ID."""
        logger.info(f"Deleting user profile for user: {user_id}")

        repository = UserProfileRepository(session)
        deleted = await repository.delete(
            condition=UserProfile.user_id == user_id
        )

        if not deleted:
            logger.warning(
                f"User profile for user {user_id} not found for deletion"
            )
            raise UserNotFoundError(
                f"User profile for user {user_id} not found"
            )

        logger.info(f"User profile for user {user_id} deleted successfully")
        return True

    @staticmethod
    async def get_all_user_profiles(
        session: AsyncSession, page: int = 1, page_size: int = 10
    ) -> list[UserProfileResponse]:
        """Get all user profiles with pagination."""
        logger.info(
            f"Getting all user profiles - page: {page}, page_size: {page_size}"
        )

        repository = UserProfileRepository(session)
        profiles = await repository.read_paginated(
            condition=True, page=page, page_size=page_size
        )

        if not profiles:
            return []

        return [
            UserProfileResponse.model_validate(profile) for profile in profiles
        ]


user_profile_service = UserProfileService()