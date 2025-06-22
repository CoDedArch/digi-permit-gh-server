import os
import hashlib
import logging
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import ClassVar, List, Dict, Any

load_dotenv(".env", override=True)
logger = logging.getLogger(__name__)


def hash_key(key: str) -> str:
    """Hash the key using SHA-256."""
    return hashlib.sha256(key.encode()).hexdigest()


class Settings(BaseSettings):
    """Class to store all the settings of the application."""

    APOSTGRES_DATABASE_URL: str = Field(env="APOSTGRES_DATABASE_URL")
    HASHED_API_KEY: str = Field(env="HASHED_API_KEY")
    OPENAI_API_KEY: str = Field(env="OPENAI_API_KEY")
    SECRET_KEY: str = Field(env="SECRET_KEY")
    ALGORITHM: str = Field(env="ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(env="ACCESS_TOKEN_EXPIRE", default=30)
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "no-reply@versecatch.pro")
    BASE_URL: str = os.getenv("BASE_URL")
    PAYSTACK_SECRET_KEY: str = os.getenv("PAYSTACK_SECRET_KEY")
    DATA_DIR: str = Field(default="../../data",env="DATA_DIR")
    SEED_ON_STARTUP: bool = Field(True, env="SEED_ON_STARTUP")
    FORCE_SEED: bool = Field(False, env="FORCE_SEED")  # Ignore existing data
    REQUIRE_SEED: bool = Field(False, env="REQUIRE_SEED")  # Crash if seeding fails
    DB_MODELS: ClassVar[List[str]] = [
        "app.models.application",
        "app.models.document",
        "app.models.inspection",
        "app.models.notification",
        "app.models.payment",
        "app.models.review",
        "app.models.user",
    ]
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()