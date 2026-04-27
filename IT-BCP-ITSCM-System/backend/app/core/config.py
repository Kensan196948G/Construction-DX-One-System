from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "IT-BCP-ITSCM-System API"
    app_version: str = "0.1.0"
    database_url: str = "sqlite+aiosqlite:///./bcp.db"

    class Config:
        env_file = ".env"


settings = Settings()
