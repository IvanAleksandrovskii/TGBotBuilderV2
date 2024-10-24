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

# SQLAdmin ENV variables
SQLADMIN_SECRET_KEY = os.getenv("SQLADMIN_SECRET_KEY", "sqladmin_secret_key")
SQLADMIN_USERNAME = os.getenv("SQLADMIN_USERNAME", "admin")
SQLADMIN_PASSWORD = os.getenv("SQLADMIN_PASSWORD", "password")

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


class SQLAdminConfig(BaseModel):
    secret_key: str = SQLADMIN_SECRET_KEY
    username: str = SQLADMIN_USERNAME
    password: str = SQLADMIN_PASSWORD


class MediaConfig(BaseModel):
    root: str = "app/media"
    base_url: str = BASE_SERVER_URL
    allowed_image_extensions: list[str] = list(MEDIA_FILES_ALLOWED_EXTENSIONS)

    @field_validator('allowed_image_extensions')
    def validate_extensions(cls, v):
        if not all(ext.startswith('.') for ext in v):
            raise ValueError("All extensions must start with a dot")
        return v


class BotAdminTexts(BaseModel):
    """
    RUSSIAN VERSION
    """
    full_success_broadcast: str = "Рассылка выполнена успешно: отправлено всем пользователям:"
    not_all_broadcast_1: str = "Рассылка выполнена, успешно отправлено пользователям"
    not_all_broadcast_2: str = "Но не удалось отправить сообщение пользователям:" 
    not_all_broadcast_3: str = "Пользователи могли не активировать чат с ботом."
    unsupported_file_type: str = "Извините, не поддерживаемый тип контента:"
    unsupported_message_type: str = "Неподдерживаемый тип сообщения: "
    broadcast_cancelled: str = "Рассылка отменена"
    added_to_broadcast: str = "Сообщение добавлено в рассылку. Отправьте еще сообщения или используйте /done для завершения."
    boadcast_approve: str = "Вы добавили сообщение(й) для рассылки. Вы уверены, что хотите начать рассылку? (да/нет)"
    braodcast_preview: str = "Вот предварительный просмотр вашей рассылки:"
    empty_broadcast: str = "Вы не добавили ни одного сообщения для рассылки. Пожалуйста, добавьте хотя бы одно сообщение. Вы сможете отменить на разу после этого."
    greeting: str = """Введите сообщение для массовой рассылки. Вы можете отправить следующие типы контента:\n\n
        • Текст\n
        • Фото\n
        • Видео\n
        • Аудио\n
        • Документ\n
        • Анимация (GIF)\n
        • Голосовое сообщение\n
        • Видеозапись\n
        • Стикер\n
        • Местоположение\n
        • Место (venue)\n
        • Контакт\n
        Вы можете отправить несколько сообщений разных типов. 
        Когда закончите, отправьте команду /done для подтверждения рассылки."""
    no_admin_rules: str = "У вас нет прав для выполнения этой команды."
    error_message: str = "Something went wrong. Please try again later or contact the developer."
    confirming_words: list[str] = ["да", "yes", "конечно", "отправить", "send", "accept", "absolutely", "lf"]


class BotMainPageTexts(BaseModel):
    user_error_message: str = "Something went wrong. Please try again later."
    welcome_fallback_user_word: str = "пользователь"


class Settings(BaseSettings):
    run: RunConfig = RunConfig()
    db: DBConfig = DBConfig()
    cors: CORSConfig = CORSConfig()
    bot: BotConfig = BotConfig()
    admin_panel: SQLAdminConfig = SQLAdminConfig()
    media: MediaConfig = MediaConfig()
    bot_admin_text: BotAdminTexts = BotAdminTexts()
    bot_main_page_text: BotMainPageTexts = BotMainPageTexts()


settings = Settings()
