from app.core.settings import settings


def blockchain_client() -> str:
    """Returns ``host:port`` for the blockchain HTTP API from settings.

    Returns:
        str: Concatenated ``BLOCKCHAIN_HOST`` (without trailing slash) and port.

    """
    return f"{settings.blockchain_settings.BLOCKCHAIN_HOST.rstrip('/')}:{settings.blockchain_settings.BLOCKCHAIN_PORT}"
