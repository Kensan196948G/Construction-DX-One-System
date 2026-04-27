from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "IT-Change-CAB-Platform"
    database_url: str = "sqlite+aiosqlite:///./cab.db"

    model_config = {"env_prefix": "CAB_"}


settings = Settings()
