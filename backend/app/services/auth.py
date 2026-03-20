from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.core.settings import settings
from app.exceptions.user import (
    InvalidCredentialsError,
    UserNotFoundError,
)
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse
from app.services.user import UserService
from app.utils.jwt import (
    blacklist_token,
    create_pair_tokens,
    get_token_subject,
    is_token_blacklisted,
)
from app.utils.password import verify_password

logger = get_logger("auth_service")


class AuthService:
    """Registers users, issues JWT cookies, refresh rotation, and logout blacklist."""

    @staticmethod
    async def register(
        request: Request,
        session: AsyncSession,
        register_data: RegisterRequest,
    ) -> tuple[UserResponse, TokenResponse]:
        """Creates a user, profile shell, and token pair.

        Args:
            request: Unused today; reserved for request-scoped metadata.
            session: Database session.
            register_data: Registration payload.

        Returns:
            tuple: ``(UserResponse, TokenResponse)``.

        Raises:
            UserAlreadyExistsError: From user creation.
            UserNotFoundError: If post-create fetch fails unexpectedly.

        """
        logger.info(f"Registering new user with email: {register_data.email}")

        user = await UserService.create_user(session, register_data)

        user_model = await UserService.get_user_by_email(session, user.email)
        if not user_model:
            raise UserNotFoundError("Failed to retrieve created user")

        tokens = create_pair_tokens(subject=user_model.id)

        logger.info(f"User registered successfully with id: {user_model.id}")

        return user, TokenResponse(**tokens)

    @staticmethod
    async def login(
        request: Request,
        session: AsyncSession,
        login_data: LoginRequest,
    ) -> tuple[UserResponse, TokenResponse]:
        """Validates email/password and returns a new token pair.

        Args:
            request: Unused; reserved.
            session: Database session.
            login_data: Credentials.

        Returns:
            tuple: Serialized user and ``TokenResponse``.

        Raises:
            InvalidCredentialsError: Unknown user or bad password.

        """
        logger.info(f"Login attempt for email: {login_data.email}")

        user = await UserService.get_user_by_email(session, login_data.email)

        if not user:
            logger.warning(f"Login failed: User with email {login_data.email} not found")
            raise InvalidCredentialsError("Invalid email or password")

        if not verify_password(login_data.password, user.password_hash):
            logger.warning(f"Login failed: Invalid password for user {user.id}")
            raise InvalidCredentialsError("Invalid email or password")

        tokens = create_pair_tokens(subject=user.id)

        logger.info(f"User {user.id} logged in successfully")

        return UserResponse.model_validate(user), TokenResponse(**tokens)

    @staticmethod
    async def refresh_token(
        session: AsyncSession, refresh_token: str
    ) -> TokenResponse:
        """Rotates tokens: blacklists old refresh and issues a new pair.

        Args:
            session: Database session for user lookup.
            refresh_token: Valid refresh JWT string.

        Returns:
            TokenResponse: New access and refresh strings.

        Raises:
            InvalidCredentialsError: Blacklisted, bad subject, or missing user.

        """
        logger.info("Refreshing token")

        if await is_token_blacklisted(refresh_token):
            logger.warning("Attempt to use blacklisted refresh token")
            raise InvalidCredentialsError("Token is blacklisted")

        try:
            user_id = get_token_subject(refresh_token)
        except Exception as e:
            logger.warning(f"Invalid refresh token: {str(e)}")
            raise InvalidCredentialsError("Invalid refresh token")

        user = await UserService.get_user_by_id(session, user_id)
        if not user:
            logger.warning(f"User {user_id} not found for token refresh")
            raise InvalidCredentialsError("User not found")

        await blacklist_token(refresh_token)

        tokens = create_pair_tokens(subject=user_id)

        logger.info(f"Token refreshed successfully for user {user_id}")

        return TokenResponse(**tokens)

    @staticmethod
    async def logout(
        request: Request, session: AsyncSession, access_token: str
    ) -> bool:
        """Blacklists access and refresh cookies if present.

        Args:
            request: Source of ``refresh_token`` cookie.
            session: Unused; kept for API symmetry.
            access_token: Access JWT to revoke.

        Returns:
            bool: Always True on success.

        """
        logger.info("Logging out user")

        refresh_token = request.cookies.get("refresh_token")

        await blacklist_token(access_token)

        if refresh_token:
            await blacklist_token(refresh_token)

        logger.info("User logged out successfully")
        return True

    @staticmethod
    def set_tokens_in_cookies(
        response: Response, tokens: TokenResponse
    ) -> None:
        """Writes httpOnly cookies for access and refresh tokens.

        Args:
            response: Outgoing Starlette/FastAPI response.
            tokens: Token strings and metadata wrapper.

        """
        secure = settings.app_settings.APP_SECURE_COOKIES
        max_age_access = settings.auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        max_age_refresh = settings.auth_settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

        response.set_cookie(
            key="access_token",
            value=tokens.access_token,
            httponly=True,
            secure=secure,
            samesite="lax",
            max_age=max_age_access,
        )

        response.set_cookie(
            key="refresh_token",
            value=tokens.refresh_token,
            httponly=True,
            secure=secure,
            samesite="lax",
            max_age=max_age_refresh,
        )

        logger.debug("Tokens set in cookies")

    @staticmethod
    def clear_tokens_in_cookies(response: Response) -> None:
        """Deletes auth cookies from the client.

        Args:
            response: Outgoing response used to issue ``delete_cookie``.

        """
        secure = settings.app_settings.APP_SECURE_COOKIES

        response.delete_cookie(
            key="access_token",
            httponly=True,
            secure=secure,
            samesite="lax",
        )
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=secure,
            samesite="lax",
        )

        logger.debug("Tokens cleared from cookies")


auth_service = AuthService()
