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

class Settings(BaseSettings):
    app: AppSettings = AppSettings()

settings = Settings()