from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    APP_HOST: str = "0.0.0.0"  # Address to listen on
    APP_PORT: int = 5000
    MAIN_NODE_HOST: str = "127.0.0.1"  # Address to connect to main node
    MAIN_NODE_PORT: int = 5000
    PROOF_OF_WORK_DIFFICULTY: str = "0000"

    model_config = SettingsConfigDict(
        env_file="node/.env", case_sensitive=False, extra="ignore"
    )


class DatabaseSettings(BaseSettings):
    DEPLOY_MODE: str = "LOCAL"  # LOCAL or DOCKER
    POSTGRES_DB: str = "blockchain"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "8080"
    POSTGRES_HOST_LOCAL: str = "localhost"
    POSTGRES_HOST_PROD: str = "localhost"
    POSTGRES_PORT: int = 5432
    DEBUG: bool = True
    SQL_ECHO: bool = False  # Log SQL queries to console

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
        env_file="node/.env", case_sensitive=False, extra="ignore"
    )
    

class Settings(BaseSettings):
    app: AppSettings = AppSettings()
    database_settings: DatabaseSettings = DatabaseSettings()
    
settings = Settings()