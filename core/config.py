# core/config.py

import os

from pydantic import BaseModel, field_validator
from pydantic.networks import PostgresDsn

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(".env")


# App ENV variables
DEBUG = os.getenv("DEBUG", "True").lower() in ('true', '1')
APP_RUN_HOST = str(os.getenv("APP_RUN_HOST", "0.0.0.0"))
APP_RUN_PORT = int(os.getenv("APP_RUN_PORT", 8000))

# Database ENV variables
POSTGRES_ADDRESS = os.getenv("POSTGRES_ADDRESS", "0.0.0.0")
POSTGRES_DB = os.getenv("POSTGRES_DB", "BotTapQuiz")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

POSTGRES_POOL_SIZE = int(os.getenv("POSTGRES_POOL_SIZE", 10))
POSTGRES_MAX_OVERFLOW = int(os.getenv("POSTGRES_MAX_OVERFLOW", 20))

POSTGRES_ECHO = os.getenv("POSTGRES_ECHO", "True").lower() in ('true', '1')

# CORS ENV variables
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", ["*"])

# Bot ENV variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Media ENV variables
MEDIA_FILES_ALLOWED_EXTENSIONS = os.getenv("MEDIA_FILES_ALLOWED_EXTENSIONS", ['.jpg', '.jpeg', '.png', '.gif', '.mp4'])  # 'avi', 'mov' 
BASE_SERVER_URL = os.getenv("BASE_SERVER_URL", "https://5df3-184-22-35-211.ngrok-free.app")


class RunConfig(BaseModel):
    debug: bool = DEBUG
    host: str = APP_RUN_HOST
    port: int = APP_RUN_PORT


class DBConfig(BaseModel):
    url: PostgresDsn = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_ADDRESS}:5432/{POSTGRES_DB}"
    pool_size: int = POSTGRES_POOL_SIZE
    max_overflow: int = POSTGRES_MAX_OVERFLOW
    echo: bool = POSTGRES_ECHO

    naming_convention: dict[str, str] = {
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_N_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }

    @field_validator('pool_size', 'max_overflow')
    def validate_positive_int(cls, v):
        if v <= 0:
            raise ValueError("Must be a positive integer")
        return v


class CORSConfig(BaseModel):
    allowed_origins: list = ALLOWED_ORIGINS
    

class BotConfig(BaseModel):
    token: str = BOT_TOKEN


class MediaConfig(BaseModel):
    root: str = "app/media"
    base_url: str = BASE_SERVER_URL
    allowed_image_extensions: list[str] = list(MEDIA_FILES_ALLOWED_EXTENSIONS)

    @field_validator('allowed_image_extensions')
    def validate_extensions(cls, v):
        if not all(ext.startswith('.') for ext in v):
            raise ValueError("All extensions must start with a dot")
        return v


class Settings(BaseSettings):
    run: RunConfig = RunConfig()
    db: DBConfig = DBConfig()
    cors: CORSConfig = CORSConfig()
    bot: BotConfig = BotConfig()
    media: MediaConfig = MediaConfig()


settings = Settings()
