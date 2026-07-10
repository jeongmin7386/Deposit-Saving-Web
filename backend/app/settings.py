import os
from functools import lru_cache

from pydantic import BaseModel


class Settings(BaseModel):
    finlife_api_key: str | None = os.getenv("FINLIFE_API_KEY") or None
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./financial_products.db")
    sync_on_startup: bool = os.getenv("SYNC_ON_STARTUP", "false").lower() == "true"
    admin_token: str | None = os.getenv("ADMIN_TOKEN") or None


@lru_cache
def get_settings() -> Settings:
    return Settings()
