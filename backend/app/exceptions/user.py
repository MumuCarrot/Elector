from fastapi import HTTPException, status


class UserNotFoundError(HTTPException):
    """Exception raised when user is not found."""

    def __init__(self, detail: str = "User not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UserAlreadyExistsError(HTTPException):
    """Exception raised when user already exists."""

    def __init__(self, detail: str = "User already exists"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, detail=detail)


class InvalidCredentialsError(HTTPException):
    """Exception raised when credentials are invalid."""

    def __init__(self, detail: str = "Invalid email or password"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class TokenNotFoundError(HTTPException):
    """Exception raised when token is not found."""

    def __init__(self, detail: str = "Token not found"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class InvalidTokenTypeError(HTTPException):
    """Exception raised when token type is invalid."""

    def __init__(self, detail: str = "Invalid token type"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class TokenBlacklistedError(HTTPException):
    """Exception raised when token is blacklisted."""

    def __init__(self, detail: str = "Token is blacklisted"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class PermissionDeniedError(HTTPException):
    """Exception raised when user doesn't have permission to perform action."""

    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class VoteNotFoundError(HTTPException):
    """Exception raised when vote is not found."""

    def __init__(self, detail: str = "Vote not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class ValidationError(HTTPException):
    """Exception raised when validation fails."""

    def __init__(self, detail: str = "Validation error"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class BlockchainConnectionError(HTTPException):
    """Exception raised when blockchain node is unreachable."""

    def __init__(self, detail: str = "Blockchain node is unreachable"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)