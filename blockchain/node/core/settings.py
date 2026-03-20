from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """HTTP server and proof-of-work settings for the node process.

    Attributes:
        APP_HOST: Interface to bind (e.g. ``0.0.0.0``).
        APP_PORT: TCP port for the API server.
        MAIN_NODE_HOST: Host of the seed/main node for peer registration.
        MAIN_NODE_PORT: Port of the seed/main node.
        PROOF_OF_WORK_DIFFICULTY: Hex prefix that a valid block hash must match
            (e.g. ``0000`` for four leading hex zeros).

    """

    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 5000
    MAIN_NODE_HOST: str = "127.0.0.1"
    MAIN_NODE_PORT: int = 5000
    PROOF_OF_WORK_DIFFICULTY: str = "0000"

    model_config = SettingsConfigDict(
        env_file="node/.env", case_sensitive=False, extra="ignore"
    )


class DatabaseSettings(BaseSettings):
    """PostgreSQL connection settings; supports LOCAL vs DOCKER host selection.

    Attributes:
        DEPLOY_MODE: ``LOCAL`` or ``DOCKER``; selects which Postgres host field is used.
        POSTGRES_DB: Database name.
        POSTGRES_USER: Database user.
        POSTGRES_PASSWORD: Database password.
        POSTGRES_HOST_LOCAL: Host when running locally.
        POSTGRES_HOST_PROD: Host when ``DEPLOY_MODE`` is ``DOCKER``.
        POSTGRES_PORT: Database port.
        DEBUG: Application debug flag (from env).
        SQL_ECHO: When True, log SQL statements (SQLAlchemy echo).

    """

    DEPLOY_MODE: str = "LOCAL"
    POSTGRES_DB: str = "blockchain"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "8080"
    POSTGRES_HOST_LOCAL: str = "localhost"
    POSTGRES_HOST_PROD: str = "localhost"
    POSTGRES_PORT: int = 5432
    DEBUG: bool = True
    SQL_ECHO: bool = False

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Async SQLAlchemy URL for asyncpg.

        Returns:
            str: ``postgresql+asyncpg://...`` connection string.

        """
        host = (
            self.POSTGRES_HOST_PROD
            if self.DEPLOY_MODE == "DOCKER"
            else self.POSTGRES_HOST_LOCAL
        )
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{host}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    model_config = SettingsConfigDict(
        env_file="node/.env", case_sensitive=False, extra="ignore"
    )


class Settings(BaseSettings):
    """Root settings container: app and database sub-settings.

    Attributes:
        app: Application and PoW configuration.
        database_settings: Database connection configuration.

    """

    app: AppSettings = AppSettings()
    database_settings: DatabaseSettings = DatabaseSettings()


settings = Settings()
