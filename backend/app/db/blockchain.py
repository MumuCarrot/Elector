from backend.app.core import settings


def blockchain_client():
    return f"{settings.blockchain_settings.BLOCKCHAIN_HOST}:{settings.blockchain_settings.BLOCKCHAIN_PORT}"