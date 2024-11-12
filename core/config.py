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
BASE_SERVER_URL = os.getenv("BASE_SERVER_URL", "https://59a5-184-22-35-232.ngrok-free.app")

HTTP_CLIENT_TIMEOUT = int(os.getenv("HTTP_CLIENT_TIMEOUT", "300"))
HTTP_CLIENTS_MAX_KEEPALIVE_CONNECTIONS = int(os.getenv("HTTP_CLIENTS_MAX_KEEPALIVE_CONNECTIONS", "10"))


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
    
    # TODO: Move to conf vars
    max_users_cached_time_seconds: int = 300
    max_users_cached: int = 1000 


class SQLAdminConfig(BaseModel):
    secret_key: str = SQLADMIN_SECRET_KEY
    username: str = SQLADMIN_USERNAME
    password: str = SQLADMIN_PASSWORD


class MediaConfig(BaseModel):
    root: str = "app/media"
    quiz_media: str = "app/media/quiz"
    base_url: str = BASE_SERVER_URL  # TODO: Move to main configurations
    allowed_image_extensions: list[str] = list(MEDIA_FILES_ALLOWED_EXTENSIONS)

    @field_validator('allowed_image_extensions')
    def validate_extensions(cls, v):
        if not all(ext.startswith('.') for ext in v):
            raise ValueError("All extensions must start with a dot")
        return v


class HTTPClientConfig(BaseModel):
    timeout: int = HTTP_CLIENT_TIMEOUT
    max_keepalive_connections: int = HTTP_CLIENTS_MAX_KEEPALIVE_CONNECTIONS


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
    utils_error_message: str = "Something went wrong. Please try again later."


class UniversalPageTexts(BaseModel):
    universal_page_error: str = "An error occurred while loading the page. Please try again."
    universal_page_try_again: str = "An error occurred. Please try starting over."


class WebhookConfig(BaseModel):
    path: str = "/webhook/bot/"


class BotReaderTexts(BaseModel):
    reader_chunks: int = 500
    reader_command_error: str = "Пожалуйста, укажите идентификатор текста после команды /read"
    reader_text_not_found: str = "Извините, текст не найден: "
    reader_end_reading_to_main: str = "Главное меню"
    reader_custom_action_processing_error: str = "Произошла ошибка при обработке действия. Попробуйте еще раз."
    reader_action_unkown: str = "Неизвестное действие"
    reader_page_load_error: str = "Произошла ошибка при загрузке страницы. Попробуйте еще раз."
    reader_page_number_button_ansewer: str = "Номер страницы, введите в чат"


class AIChatConfig(BaseSettings):
    history_length: int = 5


class QuizTexts(BaseModel):
    quiz_back_to_start: str = "Return to main menu"
    quiz_list_menu_button_for_end_quiz: str = "Return to quiz list"
    psycological_menu_button_for_end_quiz: str = "Return to tests list"
    quizes_list_menu: str = "Select a quiz to take:"  # will be used if no quiz_list text is provided
    psycological_rests_list_menu: str = "Select a test to take:"
    quiz_not_found: str = "Test not found"
    quiz_start_approve: str = "Start test"
    user_not_found: str = "User not found"
    forbidden_to_play_again_quiz_text: str = "You have already taken this test, sorry, it can only be taken once.\n\n"
    question_text_begging_1: str = "Question "
    question_text_begging_2: str = " of "
    quiz_question_previous_button: str = "◀️ Back"
    quiz_continue_button: str = "Continue"
    question_comment_header: str = "Comment on the question:"
    quiz_result_error_undefined: str = "Unable to determine the result."
    quiz_result: str =  "Test completed!\n\nYour score: "
    quiz_error: str = "Sorry, an error occurred. Please try starting again."
    
    quiz_multi_result: str = "Test completed!\n\nYour scores: "  # TODO: New


class Settings(BaseSettings):
    run: RunConfig = RunConfig()
    db: DBConfig = DBConfig()
    cors: CORSConfig = CORSConfig()
    bot: BotConfig = BotConfig()
    admin_panel: SQLAdminConfig = SQLAdminConfig()
    media: MediaConfig = MediaConfig()
    bot_admin_text: BotAdminTexts = BotAdminTexts()
    bot_main_page_text: BotMainPageTexts = BotMainPageTexts()
    http_client: HTTPClientConfig = HTTPClientConfig()
    webhook: WebhookConfig = WebhookConfig()
    bot_reader_text: BotReaderTexts = BotReaderTexts()
    ai_chat: AIChatConfig = AIChatConfig()
    universal_page_text: UniversalPageTexts = UniversalPageTexts()
    quiz_text: QuizTexts = QuizTexts()



settings = Settings()
