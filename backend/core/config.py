from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional, Literal

from dotenv import load_dotenv
from pydantic import AnyUrl, Field, PostgresDsn, validator
from pydantic_settings import BaseSettings


# Load .env and optional environment-specific .env.<ENV> before constructing settings
load_dotenv(dotenv_path=".env", override=False)
env = os.environ.get("ENV") or os.environ.get("APP_ENV")
if env:
    # allow .env.production, .env.staging, .env.development
    load_dotenv(dotenv_path=f".env.{env}", override=True)


class Settings(BaseSettings):
    ENV: Literal["development", "staging", "production"] = Field(..., env="ENV")
    APP_NAME: str = Field("Sandhya Kitchen API", env="APP_NAME")
    API_V1_PREFIX: str = Field("/api/v1", env="API_V1_PREFIX")

    DATABASE_URL: PostgresDsn = Field(..., env="DATABASE_URL")

    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    OPENAI_API_BASE: Optional[AnyUrl] = Field(None, env="OPENAI_API_BASE")

    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    ALLOWED_ORIGINS: List[str] = Field(default_factory=list, env="ALLOWED_ORIGINS")

    # extras used in project
    AI_PROVIDER: str = Field("openai", env="AI_PROVIDER")
    AI_MODEL: str = Field("gpt-4o-mini", env="AI_MODEL")
    ADMIN_USERNAME: str = Field("admin", env="ADMIN_USERNAME")
    ADMIN_PASSWORD: str = Field("admin", env="ADMIN_PASSWORD")
    CLEAR_MENU: bool = Field(False, env="CLEAR_MENU")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    # Pydantic v2 settings for BaseSettings
    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

    @validator("ALLOWED_ORIGINS", pre=True)
    def _parse_allowed_origins(cls, v):
        if v is None:
            return []
        if isinstance(v, (list, tuple)):
            return list(v)
        # allow comma-separated strings or JSON-like list
        s = str(v).strip()
        if not s:
            return []
        if s.startswith("[") and s.endswith("]"):
            # rely on simple eval for now (safer parsing could be json.loads)
            try:
                import json

                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
        return [p.strip() for p in s.split(",") if p.strip()]

    @validator("OPENAI_API_KEY", always=True)
    def _require_openai_key_in_production(cls, v, values):
        env = values.get("ENV")
        provider = values.get("AI_PROVIDER")
        if env in ("staging", "production") and provider == "openai" and not v:
            raise ValueError("OPENAI_API_KEY is required for openai provider in non-development environments")
        return v


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    return s


settings = get_settings()
