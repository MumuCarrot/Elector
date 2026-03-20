from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """HTTP server and CORS-related settings.

    Attributes:
        CORS_ORIGINS: Comma-separated allowed origins; empty uses code defaults.
        APP_HOST: Bind address for Uvicorn.
        APP_PORT: Listen port.
        APP_SECURE_COOKIES: If True, auth cookies use the Secure flag.

    """

    CORS_ORIGINS: str = ""
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_SECURE_COOKIES: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


class DatabaseSettings(BaseSettings):
    """Async PostgreSQL connection via asyncpg.

    Attributes:
        DEPLOY_MODE: ``LOCAL`` or ``DOCKER`` to pick host field.
        POSTGRES_DB: Database name.
        POSTGRES_USER: User name.
        POSTGRES_PASSWORD: Password.
        POSTGRES_HOST_LOCAL: Host when not in Docker.
        POSTGRES_HOST_PROD: Host when ``DEPLOY_MODE`` is ``DOCKER``.
        POSTGRES_PORT: Port.
        DEBUG: When True, SQLAlchemy may echo SQL (see engine setup).

    """

    DEPLOY_MODE: str = "LOCAL"
    POSTGRES_DB: str = "database_name"
    POSTGRES_USER: str = "username"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_HOST_LOCAL: str = "localhost"
    POSTGRES_HOST_PROD: str = "db"
    POSTGRES_PORT: int = 5432
    DEBUG: bool = True

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Async SQLAlchemy URL for asyncpg.

        Returns:
            str: ``postgresql+asyncpg://...`` DSN.

        """
        host = (
            self.POSTGRES_HOST_PROD
            if self.DEPLOY_MODE == "DOCKER"
            else self.POSTGRES_HOST_LOCAL
        )
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{host}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


class RedisSettings(BaseSettings):
    """Redis URL for caching (e.g. token blacklist).

    Attributes:
        DEPLOY_MODE: Selects local vs Docker Redis host.
        REDIS_PROTOCOL: URL scheme (typically ``redis``).
        REDIS_HOST_LOCAL: Non-Docker host.
        REDIS_HOST_PROD: Docker service hostname.
        REDIS_PORT: Redis port.

    """

    DEPLOY_MODE: str = "LOCAL"
    REDIS_PROTOCOL: str = "redis"
    REDIS_HOST_LOCAL: str = "localhost"
    REDIS_HOST_PROD: str = "redis"
    REDIS_PORT: int = 6379

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        """Redis connection URL without auth DB fragment.

        Returns:
            str: ``redis://host:port`` style URL.

        """
        host = (
            self.REDIS_HOST_PROD
            if self.DEPLOY_MODE == "DOCKER"
            else self.REDIS_HOST_LOCAL
        )
        return f"{self.REDIS_PROTOCOL}://{host}:{self.REDIS_PORT}"

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


class LoggingSettings(BaseSettings):
    """Rotating file and console logging configuration.

    Attributes:
        LOG_LEVEL: File handler threshold name.
        LOG_FILE_PATH: Main application log path.
        LOG_MAX_BYTES: Rotate size for file handlers.
        LOG_BACKUP_COUNT: Number of rotated files to keep.
        DEBUG: Relaxes console and app logger levels when True.

    """

    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_MAX_BYTES: int = 10485760
    LOG_BACKUP_COUNT: int = 5
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


class AuthSettings(BaseSettings):
    """JWT signing and lifetime settings (RS256 key pair from env).

    Attributes:
        AUTH_ALGORITHM: JWT alg header value.
        AUTH_PRIVATE_KEY: PEM private key for signing.
        AUTH_PUBLIC_KEY: PEM public key for verification.
        ACCESS_TOKEN_EXPIRE_MINUTES: Access JWT lifetime.
        REFRESH_TOKEN_EXPIRE_DAYS: Refresh JWT lifetime.

    """

    AUTH_ALGORITHM: str = "RS256"
    AUTH_PRIVATE_KEY: str | None = None
    AUTH_PUBLIC_KEY: str | None = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


class BlockchainSettings(BaseSettings):
    """Upstream blockchain node base URL parts.

    Attributes:
        BLOCKCHAIN_HOST: Scheme and host (e.g. ``http://localhost``).
        BLOCKCHAIN_PORT: API port of the node.

    """

    BLOCKCHAIN_HOST: str = "http://localhost"
    BLOCKCHAIN_PORT: int = 5000

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


class Settings(BaseSettings):
    """Root settings grouping all sub-config objects.

    Attributes:
        app_settings: HTTP/CORS flags.
        database_settings: Postgres DSN inputs.
        redis_settings: Redis URL inputs.
        logging_settings: Log paths and levels.
        auth_settings: JWT configuration.
        blockchain_settings: External node location.

    """

    app_settings: AppSettings = AppSettings()
    database_settings: DatabaseSettings = DatabaseSettings()
    redis_settings: RedisSettings = RedisSettings()
    logging_settings: LoggingSettings = LoggingSettings()
    auth_settings: AuthSettings = AuthSettings()
    blockchain_settings: BlockchainSettings = BlockchainSettings()


settings = Settings()
