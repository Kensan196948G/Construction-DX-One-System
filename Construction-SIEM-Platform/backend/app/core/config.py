from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Construction-SIEM-Platform API"
    app_version: str = "0.1.0"
    database_url: str = "sqlite+aiosqlite:///./siem.db"
    secret_key: str = "siem-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
