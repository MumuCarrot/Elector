from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hashes a plaintext password with bcrypt.

    Args:
        password: User-supplied password.

    Returns:
        str: Stored hash string.

    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plaintext against a bcrypt hash.

    Args:
        plain_password: Candidate password.
        hashed_password: Value from storage.

    Returns:
        bool: True if the password matches.

    """
    return pwd_context.verify(plain_password, hashed_password)
