from datetime import datetime, timezone
from typing import Optional

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.exceptions.user import UserNotFoundError, UserAlreadyExistsError
from app.models.user import User
from app.models.user_profile import UserProfile
from app.repository.user_repository import UserRepository
from app.repository.user_profile_repository import UserProfileRepository
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.utils.jwt import get_bearer_token, get_token_subject, JwtScenario
from app.utils.password import hash_password

logger = get_logger("user_service")


class UserService:
    """Creates and queries users; resolves ORM user from JWT cookie."""

    @staticmethod
    async def create_user(
        session: AsyncSession, user_data: UserCreate
    ) -> UserResponse:
        """Persists user and empty profile row.

        Args:
            session: DB session.
            user_data: Registration fields including plaintext password.

        Returns:
            UserResponse: Serialized created user.

        Raises:
            UserAlreadyExistsError: Duplicate email.

        """
        logger.info(f"Creating user with email: {user_data.email}")

        repository = UserRepository(session)
        existing_user = await repository.read_one(
            condition=User.email == user_data.email
        )

        if existing_user:
            logger.warning(f"User with email {user_data.email} already exists")
            raise UserAlreadyExistsError(
                f"User with email {user_data.email} already exists"
            )

        password_hash = hash_password(user_data.password)

        new_user = User(
            email=user_data.email,
            phone=user_data.phone,
            password_hash=password_hash,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )

        created_user = await repository.create(new_user)
        logger.info(f"User created successfully with id: {created_user.id}")

        profile_repo = UserProfileRepository(session)
        new_profile = UserProfile(
            user_id=created_user.id,
            birth_date=None,
            avatar_url=None,
            address=None,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        await profile_repo.create(new_profile)
        logger.info(f"User profile created automatically for user: {created_user.id}")

        return UserResponse.model_validate(created_user)

    @staticmethod
    async def get_user_by_id(
        session: AsyncSession, user_id: str
    ) -> Optional[UserResponse]:
        """Loads user by primary key.

        Args:
            session: DB session.
            user_id: UUID string.

        Returns:
            UserResponse | None: Missing users return None.

        """
        logger.info(f"Getting user by id: {user_id}")

        repository = UserRepository(session)
        user = await repository.read_one(condition=User.id == user_id)

        if not user:
            logger.warning(f"User with id {user_id} not found")
            return None

        return UserResponse.model_validate(user)

    @staticmethod
    async def get_user_by_email(
        session: AsyncSession, email: str
    ) -> Optional[User]:
        """Fetches ORM user by unique email (login path).

        Args:
            session: DB session.
            email: Login email.

        Returns:
            User | None: ORM instance or None.

        """
        logger.debug(f"Getting user by email: {email}")

        repository = UserRepository(session)
        user = await repository.read_one(condition=User.email == email)

        return user

    @staticmethod
    async def get_user_by_token(
        request: Request, session: AsyncSession
    ) -> User:
        """Decodes ``access_token`` cookie and loads ``User`` ORM row.

        Args:
            request: HTTP request with cookies.
            session: DB session.

        Returns:
            User: ORM model (not Pydantic).

        Raises:
            TokenNotFoundError: Missing cookie.
            UserNotFoundError: Unknown user or unsupported auth mode.

        """
        logger.debug("Getting user by token")

        token_data = get_bearer_token(request)

        if token_data["method"] == JwtScenario.AUTH_LOCAL:
            subject = get_token_subject(token_data["token"])
            user = await UserService.get_user_by_id(session, subject)
            if not user:
                raise UserNotFoundError("User not found")

            repository = UserRepository(session)
            user_model = await repository.read_one(condition=User.id == subject)
            if not user_model:
                raise UserNotFoundError("User not found")
            return user_model
        raise UserNotFoundError("Unsupported authentication method")

    @staticmethod
    async def update_user(
        session: AsyncSession, user_id: str, user_data: UserUpdate
    ) -> UserResponse:
        """Partial update with optional password re-hash and email uniqueness check.

        Args:
            session: DB session.
            user_id: Target user id.
            user_data: Fields to change.

        Returns:
            UserResponse: Updated user.

        Raises:
            UserNotFoundError: User missing.
            UserAlreadyExistsError: Email taken by another user.

        """
        logger.info(f"Updating user with id: {user_id}")

        repository = UserRepository(session)
        user = await repository.read_one(condition=User.id == user_id)

        if not user:
            logger.warning(f"User with id {user_id} not found")
            raise UserNotFoundError(f"User with id {user_id} not found")

        if user_data.email and user_data.email != user.email:
            existing_user = await repository.read_one(
                condition=User.email == user_data.email
            )
            if existing_user:
                logger.warning(
                    f"Email {user_data.email} is already taken by another user"
                )
                raise UserAlreadyExistsError(
                    f"Email {user_data.email} is already taken"
                )

        update_dict = user_data.model_dump(exclude_unset=True)

        if "password" in update_dict:
            update_dict["password_hash"] = hash_password(update_dict.pop("password"))

        updated_user = await repository.update(
            data=update_dict, condition=User.id == user_id
        )

        logger.info(f"User with id {user_id} updated successfully")

        return UserResponse.model_validate(updated_user)

    @staticmethod
    async def delete_user(session: AsyncSession, user_id: str) -> bool:
        """Deletes user row by id.

        Args:
            session: DB session.
            user_id: User id.

        Returns:
            bool: True when a row was removed.

        Raises:
            UserNotFoundError: No row deleted.

        """
        logger.info(f"Deleting user with id: {user_id}")

        repository = UserRepository(session)
        deleted = await repository.delete(condition=User.id == user_id)

        if not deleted:
            logger.warning(f"User with id {user_id} not found for deletion")
            raise UserNotFoundError(f"User with id {user_id} not found")

        logger.info(f"User with id {user_id} deleted successfully")
        return True

    @staticmethod
    async def get_all_users(
        session: AsyncSession, page: int = 1, page_size: int = 10
    ) -> list[UserResponse]:
        """Paginated list of users.

        Args:
            session: DB session.
            page: 1-based page.
            page_size: Page length.

        Returns:
            list[UserResponse]: Page of users (empty list if none).

        """
        logger.info(f"Getting all users - page: {page}, page_size: {page_size}")

        repository = UserRepository(session)
        users = await repository.read_paginated(
            condition=True, page=page, page_size=page_size
        )

        if not users:
            return []

        return [UserResponse.model_validate(user) for user in users]


user_service = UserService()
