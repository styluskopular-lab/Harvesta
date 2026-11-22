from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Harvesta"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production-please-use-a-long-random-string",
        validation_alias=AliasChoices("JWT_SECRET_KEY", "SECRET_KEY"),
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = "sqlite:///./harvesta.db"

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:8000",
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
