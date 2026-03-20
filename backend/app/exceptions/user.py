from fastapi import HTTPException, status


class UserNotFoundError(HTTPException):
    """Raised when a user record cannot be resolved."""

    def __init__(self, detail: str = "User not found"):
        """Args:
            detail: Response body ``detail`` field.

        """
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UserAlreadyExistsError(HTTPException):
    """Raised on create/register when email or unique key conflicts."""

    def __init__(self, detail: str = "User already exists"):
        """Args:
            detail: Response body ``detail`` field.

        """
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class InvalidCredentialsError(HTTPException):
    """Raised for failed login or bad refresh token semantics."""

    def __init__(self, detail: str = "Invalid email or password"):
        """Args:
            detail: Response body ``detail`` field.

        """
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class TokenNotFoundError(HTTPException):
    """Raised when expected JWT cookie or header is missing."""

    def __init__(self, detail: str = "Token not found"):
        """Args:
            detail: Response body ``detail`` field.

        """
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class InvalidTokenTypeError(HTTPException):
    """Raised when JWT ``type`` claim does not match the operation."""

    def __init__(self, detail: str = "Invalid token type"):
        """Args:
            detail: Response body ``detail`` field.

        """
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class TokenBlacklistedError(HTTPException):
    """Raised when a refresh token was revoked (Redis blacklist)."""

    def __init__(self, detail: str = "Token is blacklisted"):
        """Args:
            detail: Response body ``detail`` field.

        """
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class PermissionDeniedError(HTTPException):
    """Raised when the caller lacks rights for the resource."""

    def __init__(self, detail: str = "Permission denied"):
        """Args:
            detail: Response body ``detail`` field.

        """
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class VoteNotFoundError(HTTPException):
    """Raised when a vote record is missing on lookup paths that 404."""

    def __init__(self, detail: str = "Vote not found"):
        """Args:
            detail: Response body ``detail`` field.

        """
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ValidationError(HTTPException):
    """Raised for domain validation failures (distinct from FastAPI 422)."""

    def __init__(self, detail: str = "Validation error"):
        """Args:
            detail: Response body ``detail`` field.

        """
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class BlockchainConnectionError(HTTPException):
    """Raised when the blockchain node HTTP client cannot complete a call."""

    def __init__(self, detail: str = "Blockchain node is unreachable"):
        """Args:
            detail: Response body ``detail`` field.

        """
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)
