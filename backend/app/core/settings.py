from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    CORS_ORIGINS: str = ""
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_SECURE_COOKIES: bool = False

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


class DatabaseSettings(BaseSettings):
    DEPLOY_MODE: str = "LOCAL"  # LOCAL or DOCKER
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
    DEPLOY_MODE: str = "LOCAL"  # LOCAL or DOCKER
    REDIS_PROTOCOL: str = "redis"
    REDIS_HOST_LOCAL: str = "localhost"
    REDIS_HOST_PROD: str = "redis"
    REDIS_PORT: int = 6379
    
    @computed_field
    @property
    def REDIS_URL(self) -> str:
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
    LOG_LEVEL: str = "INFO"
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


class AuthSettings(BaseSettings):
    AUTH_ALGORITHM: str = "RS256"
    AUTH_PRIVATE_KEY: str | None = None
    AUTH_PUBLIC_KEY: str | None = None
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


class BlockchainSettings(BaseSettings):
    BLOCKCHAIN_HOST: str = "http://localhost"
    BLOCKCHAIN_PORT: int = 5000

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


class Settings(BaseSettings):
    app_settings: AppSettings = AppSettings()
    database_settings: DatabaseSettings = DatabaseSettings()
    redis_settings: RedisSettings = RedisSettings()
    logging_settings: LoggingSettings = LoggingSettings()
    auth_settings: AuthSettings = AuthSettings()
    blockchain_settings: BlockchainSettings = BlockchainSettings()

settings = Settings()