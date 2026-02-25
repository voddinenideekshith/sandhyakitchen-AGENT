from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import AnyUrl, Field, PostgresDsn, validator
from pydantic_settings import BaseSettings


# ---------------------------------------------------
# LOAD ENV FILES
# ---------------------------------------------------
load_dotenv(dotenv_path=".env", override=False)

env = os.environ.get("ENV") or os.environ.get("APP_ENV")
if env:
    # supports .env.production / .env.staging / .env.development
    load_dotenv(dotenv_path=f".env.{env}", override=True)


# ---------------------------------------------------
# SETTINGS
# ---------------------------------------------------
class Settings(BaseSettings):
    # App
    ENV: str = Field("development", env="ENV")
    APP_NAME: str = Field("Sandhya Kitchen API", env="APP_NAME")
    API_V1_PREFIX: str = Field("/api/v1", env="API_V1_PREFIX")

    # Database
    DATABASE_URL: PostgresDsn = Field(..., env="DATABASE_URL")

    # JWT
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        60, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # OpenAI / AI
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    OPENAI_API_BASE: Optional[AnyUrl] = Field(None, env="OPENAI_API_BASE")

    AI_PROVIDER: str = Field("openai", env="AI_PROVIDER")
    AI_MODEL: str = Field("gpt-4o-mini", env="AI_MODEL")

    # Logging
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")

    # CORS
    ALLOWED_ORIGINS: List[str] = Field(
        default_factory=list, env="ALLOWED_ORIGINS"
    )

    # Admin defaults
    ADMIN_USERNAME: str = Field("admin", env="ADMIN_USERNAME")
    ADMIN_PASSWORD: str = Field("admin", env="ADMIN_PASSWORD")

    CLEAR_MENU: bool = Field(False, env="CLEAR_MENU")

    # ---------------------------------------------------
    # ✅ PYDANTIC V2 CONFIG (ONLY THIS — NO class Config)
    # ---------------------------------------------------
    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

    # ---------------------------------------------------
    # VALIDATORS
    # ---------------------------------------------------
    @validator("ALLOWED_ORIGINS", pre=True)
    def parse_allowed_origins(cls, v):
        if v is None:
            return []

        if isinstance(v, (list, tuple)):
            return list(v)

        s = str(v).strip()
        if not s:
            return []

        if s.startswith("[") and s.endswith("]"):
            try:
                import json
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass

        return [p.strip() for p in s.split(",") if p.strip()]

    @validator("OPENAI_API_KEY", always=True)
    def require_openai_key_in_production(cls, v, values):
        env = values.get("ENV")
        provider = values.get("AI_PROVIDER")

        if env in ("production", "staging") and provider == "openai" and not v:
            raise ValueError(
                "OPENAI_API_KEY is required for openai provider in non-development environments"
            )
        return v


# ---------------------------------------------------
# SETTINGS SINGLETON
# ---------------------------------------------------
@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()