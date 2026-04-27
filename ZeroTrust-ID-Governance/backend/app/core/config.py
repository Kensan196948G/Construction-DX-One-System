from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    app_name: str = "ZeroTrust-ID-Governance API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://ztig:ztig_pass@localhost:5432/ztig_db"
    database_url_sync: str = "postgresql+psycopg2://ztig:ztig_pass@localhost:5432/ztig_db"

    # JWT
    secret_key: str = "change-me-in-production-use-32-chars-minimum"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000", "https://ztig.miraikensetu.co.jp"]

    # EntraID (Microsoft Graph API)
    entraid_base_url: str = ""
    entraid_tenant_id: str = ""
    entraid_client_id: str = ""
    entraid_client_secret: str = ""

    # HENGEONE (SCIM 2.0)
    hengeone_base_url: str = ""
    hengeone_api_key: str = ""

    # Active Directory (LDAPS)
    ad_server: str = ""
    ad_port: int = 636
    ad_base_dn: str = ""
    ad_bind_dn: str = ""
    ad_bind_password: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
