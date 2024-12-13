# core/config.py

import os

from pydantic import BaseModel, field_validator
from pydantic.networks import PostgresDsn

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(".env")


# App ENV variables
DEBUG = os.getenv("DEBUG", "False").lower() in ('true', '1')
APP_RUN_HOST = str(os.getenv("APP_RUN_HOST", "0.0.0.0"))
APP_RUN_PORT = int(os.getenv("APP_RUN_PORT", 8000))

APP_RUN_WORKERS = int(os.getenv("APP_RUN_WORKERS", 1))

# Database ENV variables
POSTGRES_ADDRESS = os.getenv("POSTGRES_ADDRESS", "0.0.0.0")
POSTGRES_DB = os.getenv("POSTGRES_DB", "BotTapQuiz")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

POSTGRES_POOL_SIZE = int(os.getenv("POSTGRES_POOL_SIZE", 10))
POSTGRES_MAX_OVERFLOW = int(os.getenv("POSTGRES_MAX_OVERFLOW", 20))

POSTGRES_ECHO = os.getenv("POSTGRES_ECHO", "False").lower() in ('true', '1')

# CORS ENV variables
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", ["*"])

# Bot ENV variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# SQLAdmin ENV variables
SQLADMIN_SECRET_KEY = os.getenv("SQLADMIN_SECRET_KEY", "sqladmin_secret_key")
SQLADMIN_USERNAME = os.getenv("SQLADMIN_USERNAME", "admin")
SQLADMIN_PASSWORD = os.getenv("SQLADMIN_PASSWORD", "password")

# Media ENV variables
MEDIA_FILES_ALLOWED_EXTENSIONS = os.getenv("MEDIA_FILES_ALLOWED_EXTENSIONS", ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov', '.pdf']) 
BASE_SERVER_URL = os.getenv("BASE_SERVER_URL", "https://9a42-184-22-18-75.ngrok-free.app")

HTTP_CLIENT_TIMEOUT = int(os.getenv("HTTP_CLIENT_TIMEOUT", "300"))
HTTP_CLIENTS_MAX_KEEPALIVE_CONNECTIONS = int(os.getenv("HTTP_CLIENTS_MAX_KEEPALIVE_CONNECTIONS", "10"))


class RunConfig(BaseModel):
    debug: bool = DEBUG
    host: str = APP_RUN_HOST
    port: int = APP_RUN_PORT
    
    workers: int = APP_RUN_WORKERS
    timeout: int = 900 # APP_RUN_TIMEOUT


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
    # max_users_cached_time_seconds: int = 300
    # max_users_cached: int = 1000 


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
    utils_handler_content_not_found: str = "Content not found."


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


# class QuizTexts(BaseModel):
#     quiz_back_to_start: str = "Return to main menu"
#     quiz_list_menu_button_for_end_quiz: str = "Return to quiz list"
#     psycological_menu_button_for_end_quiz: str = "Return to tests list"
#     quizes_list_menu: str = "Select a quiz to take:"  # will be used if no quiz_list text is provided
#     psycological_rests_list_menu: str = "Select a test to take:"
#     quiz_not_found: str = "Test not found"
#     quiz_start_approve: str = "Start test"
#     user_not_found: str = "User not found"
#     forbidden_to_play_again_quiz_text: str = "You have already taken this test, sorry, it can only be taken once.\n\n"
#     question_text_begging_1: str = "Question "
#     question_text_begging_2: str = " of "
#     quiz_question_previous_button: str = "◀️ Back"
#     quiz_continue_button: str = "Continue"
#     question_comment_header: str = "Comment on the question:"
#     quiz_result_error_undefined: str = "Unable to determine the result."
#     quiz_result: str =  "Test completed!\n\nYour score: "    
#     quiz_multi_result: str = "Test completed!\n\nYour scores: " 


class QuizTexts(BaseModel):
    quiz_back_to_start: str = "В главное меню"
    quiz_list_menu_button_for_end_quiz: str = "◀️ К списку тестов"
    psycological_menu_button_for_end_quiz: str = "◀️ К списку тестов"
    quizes_list_menu: str = "Выберите тест для прохождения: "  # will be used if no quiz_list text is provided
    psycological_rests_list_menu: str = "Выберите тест для прохождения: "
    quiz_not_found: str = "Тест не найден"
    quiz_start_approve: str = "✅ Начать тест"
    user_not_found: str = "Пользователь не найден"
    forbidden_to_play_again_quiz_text: str = "Вы уже проходили этот тест, извините, нельзя проходить повторно.\n\n"
    question_text_begging_1: str = "Вопрос "
    question_text_begging_2: str = " из "
    quiz_question_previous_button: str = "◀️ Назад"
    quiz_continue_button: str = "Продолжить"
    question_comment_header: str = "Комментарий к вопросу:"
    quiz_result_error_undefined: str = "Произошла ошибка при определении результата. Сообщите об этом @Johnny_Taake."
    quiz_result: str =  "Тест завершен!\n\nВаш результат: "    
    quiz_multi_result: str = "Тест завершен!\n\nВаш результат: " 



# class SendTestTexts(BaseModel):
#     csv_export_back_button: str = "Back"
#     csv_choose_test_to_export: str = "Choose a test to export data:"
#     csv_export_by_tests_error: str = "An error occurred while loading the list of tests."
#     csv_export_success: str = "CSV file has been successfully generated and sent."
#     csv_send_success: str = "CSV file has been successfully generated and sent."
#     csv_export_error: str = "An error occurred while exporting data"
#     csv_export_all_button: str = "Export all data to CSV"
#     csv_export_by_tests_button: str = "Export by tests"
#     csv_export_user_button: str = "Export to CSV"
#     send_test_notification_reciver: str = "You have received new tests from user @"
#     send_apply_chosen_tests_button: str = "Confirm selection"
#     send_choose_another_tests_type_button: str = "Back to send test menu"  #  "Choose another test type"
#     back_button: str = "Back"
#     cancel_button: str = "Cancel"
#     button_accept: str = "Confirm"
#     back_to_userlist_button: str = "Back to user list"
#     back_to_main_menu_button: str = "Return to main menu"
#     choose_another_test: str = "Choose a test to send:"
#     selected_tests_count: str = "Tests selected:"
#     selected_tests_list: str = "Selected tests:"
#     check_sent_tests_button: str = "View sent tests"
#     send_psyco_tests_button: str = "Send psychological tests"
#     send_other_tests_button: str = "Regular tests"
#     send_tests_cancel_button: str = "Cancel"
#     send_tests_choose_type: str = "Choose an action:"
#     sent_tests_user_choose: str = "Select a user to view sent tests:"
#     send_tests_users_fetch_error: str = "An error occurred while loading the user list. Please try again."
    
#     test_sent: str = "Sent"
#     test_delivered: str = "Delivered"
#     test_completed: str = "Completed"
#     test_rejected: str = "Rejected"
#     test_unkown_status: str = "Unknown status"
#     test_name_repr: str = "Test"
#     test_status_repr: str = "Status"
#     test_score_result_repr: str = "Result"
#     test_text_result_repr: str = "Result text"
#     no_sent_tests_from_username: str = "No sent tests for user @"
#     tests_send_to_username: str = "Tests sent to user @"
#     user_results_page_number: str = "Page number"
#     no_chosen_tests_to_send: str = "You haven't selected any tests. Please choose at least one test."
#     tests_chosen_to_send_1: str = "You have selected the following tests to send"
#     tests_chosen_to_send_2: str = "Confirm your selection or go back to make changes."
#     confirm_send_button: str = "Confirm"
#     send_test_description: str = "Test description:"
#     send_test_add_test_button: str = "Add test"
#     send_test_back_to_tests_list_button: str = "Back to test list"
#     send_test_load_info_error: str = "An error occurred while loading test information."
#     send_test_added_to_list: str = "Test added to the selected list"
#     send_test_unknown_action: str = "Unknown action"
#     send_test_enter_username: str = "Enter the username of the user you want to send tests to:"
#     send_test_error_no_tests_selected: str = "Error: no tests selected. Please start the test sending process again. Enter another username or cancel."
#     send_test_error_send_youself: str = "Error: you cannot send a test to yourself."
#     send_test_reciver_authenticated: str = "authenticated"
#     send_test_reciver_not_authenticated: str = "not authenticated"
#     send_test_all_chosen_tests_uncomplete: str = "All selected tests have already been sent and are not completed."
#     send_test_all_chosen_tests_uncomplete_2: str = "Please select other tests."
#     send_test_return_to_test_choose_button: str = "Return to test selection"
#     send_test_last_confirm: str = "You are about to send the following tests to user @"
#     send_test_last_confirm_2: str = "User status: "
#     send_test_last_confirm_3: str = " in the bot."
#     send_test_last_confirm_sent_before: str = "The following tests have already been sent and are not completed"
#     send_test_last_confirm_sent_before_2: str = "They will be skipped."
#     send_test_last_confirm_accept: str = "Confirm the action."
#     send_test_last_confirm_error: str = "An error occurred while processing the request. Please try again."
#     send_test_confirm_error: str = "Invalid action. Please confirm sending or cancel."
#     send_test_confirm_error_not_enough_data: str = "Not enough data to send tests. Please start over."
#     send_test_confirm_different_error: str = "An error occurred while sending tests. Please try again."
    
#     tests_sent_success: str = "Tests successfully sent to user @"
#     tests_sent_success_2: str = "and they have been notified."
#     tests_sent_unsuccess: str = "Tests sent to user @"
#     tests_sent_unsuccess_2: str = ("As soon as the user authorizes in the bot, they will be prompted to take the tests. "
#         "\nMake sure you sent to the correct username if the tests don't reach a user who has already authorized in the bot."
#         "\nHere is your invite link: \n\n"
#     )


class SendTestTexts(BaseModel):
    csv_export_back_button: str = "⬅️ Назад"
    csv_choose_test_to_export: str = "Выберите тест для экспорта данных:"
    csv_export_by_tests_error: str = "Произошла ошибка при загрузке списка тестов."
    csv_export_success: str = "CSV файл отправлен."
    csv_send_success: str = "CSV файл отправлен."
    csv_export_error: str = "Произошла ошибка при экспорте данных"
    csv_export_all_button: str = "💾 Экспортировать все данные в CSV"
    csv_export_by_tests_button: str = "💾 Экспортировать по тестам"
    csv_export_user_button: str = "💾 Экспортировать в CSV"
    send_test_notification_reciver: str = "Вам отправлены новые тесты от пользователя @"
    send_apply_chosen_tests_button: str = "✅ Подтвердить выбор"
    send_choose_another_tests_type_button: str = "⬅️ Назад"  #  "Choose another test type"
    back_button: str = "⬅️ Назад"
    cancel_button: str = "❌ Отмена"
    button_accept: str = "✅ Подтвердить"
    back_to_userlist_button: str = "⬅️ Назад к списку пользователей"
    back_to_main_menu_button: str = "В главное меню"
    choose_another_test: str = "Выберите тест для отправки:"
    selected_tests_count: str = "Выбранны тесты: "
    selected_tests_list: str = "Выбранные тесты: "
    check_sent_tests_button: str = "📤 Посмотреть отправленные тесты"
    send_psyco_tests_button: str = "📨 Отправить тесты"
    # send_other_tests_button: str = "Обычные тесты"  # Unused now
    send_tests_cancel_button: str = "❌ Отмена"
    send_tests_choose_type: str = "Выберите действие:"
    sent_tests_user_choose: str = "Выберите пользователся, чтобы посмотреть отправленные ему тесты:"
    send_tests_users_fetch_error: str = "Обнаружена ошибка при загрузке списка пользователей. Сообщие об этом @Johnny_Taake."
    
    test_sent: str = "Отправлено"
    test_delivered: str = "Доставлено"
    test_completed: str = "Завершено"
    test_rejected: str = "Отклонено"
    test_unkown_status: str = "Неизвестный статус"
    test_name_repr: str = "Тест"
    test_status_repr: str = "Статус"
    test_score_result_repr: str = "Результат"
    test_text_result_repr: str = "Расшифровка результата"
    no_sent_tests_from_username: str = "Нет отправленных тестов от пользователя @"
    tests_send_to_username: str = "Тесты отправлены пользователю @"
    user_results_page_number: str = "Номер страницы"
    no_chosen_tests_to_send: str = "Вы не выбрали ни одного теста. Пожалуйста, выберите хотя бы один."
    tests_chosen_to_send_1: str = "Вы выбрали следующие тесты для отправки"
    tests_chosen_to_send_2: str = "Подтвердите выбор или вернитесь назад для изменений."
    confirm_send_button: str = "✅ Подтвердить"
    send_test_description: str = "Описание теста:"
    send_test_add_test_button: str = "✅ Добавить тест"
    send_test_back_to_tests_list_button: str = "⬅️ Назад к списку тестов"
    send_test_load_info_error: str = "Произошла ошибка при загрузке информации о тесте. Сообщите об этом @Johnny_Taake."
    send_test_added_to_list: str = "Тест добавлен"
    send_test_unknown_action: str = "Неизвестное действие"
    send_test_enter_username: str = "Введите Usermane пользователя, которому вы хотите отправить тесты:"
    send_test_error_no_tests_selected: str = "Произошла ошибка: не выбраны тесты. Пожалуйста, попробуйте еще раз и сообщите об этом @Johnny_Taake."
    send_test_error_send_youself: str = "Вы не можете отправить тесты самому себе."
    send_test_reciver_authenticated: str = "авторизован"
    send_test_reciver_not_authenticated: str = "не авторизован"
    send_test_all_chosen_tests_uncomplete: str = "Все выбранные тесты уже отправлены и не завершены."
    send_test_all_chosen_tests_uncomplete_2: str = "Пожалуйста, выберите другие тесты."
    send_test_return_to_test_choose_button: str = "⬅️ Назад к выбору тестов"
    send_test_last_confirm: str = "Вы собираетесь отправить следующие тесты пользователю @"
    send_test_last_confirm_2: str = "Статус пользователя: "
    send_test_last_confirm_3: str = " в боте."
    send_test_last_confirm_sent_before: str = "Тесты, которые уже отправлены и еще не завершены"
    send_test_last_confirm_sent_before_2: str = "Они будут пропущены."
    send_test_last_confirm_accept: str = "Выберите действие:"
    send_test_last_confirm_error: str = "Произошла ошибка при обработке запроса. Сообщите об этом @Johnny_Taake."
    send_test_confirm_error: str = "Неверное действие. Пожалуйста, подтвердите отправку или отмените."
    send_test_confirm_error_not_enough_data: str = "Недостаточно данных для отправки тестов. Пожалуйста, попробуйте еще раз и сообщите об этом @Johnny_Taake."
    send_test_confirm_different_error: str = "Произошла ошибка при отправке тестов. Попробуйте еще раз и сообщите об этом @Johnny_Taake."
    
    tests_sent_success: str = "Тесты успешно отправлены пользователю @"
    tests_sent_success_2: str = "и он был уведомлен."
    tests_sent_unsuccess: str = "Тесты отправлены пользователю @"
    tests_sent_unsuccess_2: str = ("Как только пользователь авторизуется в боте, ему будет предложено пройти тесты. "
        "\nУбедитесь, что вы отправили правильное имя пользователя, если тесты не приходят пользователю."
        "\nВот ссылка для приглашения: \n\n"
    )


class OnStartTexts(BaseModel):
    # start_recived_tests_button: str = "❗ View received tests"
    start_recived_tests_button: str = "❗ Посмотреть полученные тесты"


# class ReceivedTestTexts(BaseModel):
#     send_tests_notifier: str = "User @"
#     send_tests_notifier_completed: str = "has completed the test"
#     send_tests_notifier_rejected: str = "has rejected the test"
#     page_number: str = "Page number"
#     tests_choose_sender: str = "Choose a sender to view received tests:"
#     tests_no_tests: str = "You have no received tests."
#     senders_page_loading_error: str = "An error occurred while loading the list of senders. Please try again."
#     choose_sent_test_button: str = "✅"
#     reject_all_from_user_button: str = "❌ Reject all tests"
#     back_to_senders_list_button: str = "🔙 Back to senders list"
#     to_main_menu_button: str = "Main menu"
#     back_button: str = "⬅️ Back"
#     no_test_from_user: str = "You have no active tests from this user."
#     tests_from_username_button: str = "Tests from user @"
#     tests_loading_error: str = "An error occurred while loading tests. Please try again."
    
#     test_not_found: str = "Test not found"
#     start_test_button: str = "✅ Start test"
#     send_saved_result_button: str = "💾 Send result"
#     reject_test_button: str = "❌ Reject test"
#     back_to_tests_list_button: str = "🔙 Back to test list"
#     start_test_confirm: str = "You are about to start the test:"
#     start_test_confirm_2: str = "Confirm the action or go back."
#     start_test_error: str = "An error occurred while preparing the test. Please try again."
#     start_test_error_test_not_found: str = "Test not found"
#     test_error_answers_processing_error: str = "An error occurred while processing the answer. Please try again."
#     test_error_comment_processing_error: str = "An error occurred while displaying the comment. Please continue the test."
#     test_end_error: str = "An error occurred while completing the test. Please contact the administrator."
#     other_tests_from_sender_button: str = "Other tests from this sender"
#     tests_from_other_senders_button: str = "Tests from other senders"
#     result_send_not_found_please_pass_test: str = "Existing result not found. Please take the test."
#     result_send_error: str = "An error occurred while preparing to send the result. Please try again."
#     send_test_result_confirm_1: str = "You are about to send the test result"
#     send_test_result_confirm_2: str = "Your score"
#     send_test_result_confirm_3: str = "Result interpretation"
#     send_test_result_confirm_4: str = "Are you sure you want to send this result?"
#     confirm_send_test_result_button: str = "Yes, send"
#     reject_send_test_result_button: str = "No, cancel"
#     send_test_result_success_sent_1: str = "The test result"
#     send_test_result_success_sent_2: str = "has been successfully sent.\n\nYour score:"
#     send_result_cancel: str = "Result sending canceled."
#     back_to_recived_tests_button: str = "Return to received tests"
#     confirm_reject_test_button: str = "✅ Yes, reject"
#     cancel_reject_test_button: str = "⬅️ No, go back"
#     reject_test_confirm: str = "Are you sure you want to reject this test?"
#     reject_test_error: str = "An error occurred while rejecting the test."
#     reject_all_tests_from_user: str = "❌ Reject all tests"
#     reject_test_from_user_canceled: str = "Test rejection canceled."
#     no_tests_from_user: str = "You have no active tests from this user."
#     error_loading_tests: str = "An error occurred while loading tests. Please try again."
#     sender_info_not_found_error: str = "Sorry, error. Could not find sender information."
#     confirm_reject_all_test_button: str = "✅ Yes, reject all"
#     reject_all_tests_confirmation: str = "Are you sure you want to reject all tests from user"
#     reject_all_tests_error: str = "An error occurred while rejecting tests."
#     confirm_error: str = "An error occurred while preparing confirmation."


class ReceivedTestTexts(BaseModel):
    send_tests_notifier: str = "Пользователь @"
    send_tests_notifier_completed: str = "прошел тест"
    send_tests_notifier_rejected: str = "отклонил тест"
    page_number: str = "Номер страницы"
    tests_choose_sender: str = "Выберите отправителя для просмотра полученных тестов:"
    tests_no_tests: str = "У вас нет полученных тестов."
    senders_page_loading_error: str = "Произошла ошибка при загрузке списка отправителей, попробуйте еще раз и сообщите об этом @Johnny_Taake."
    choose_sent_test_button: str = "✅"
    reject_all_from_user_button: str = "❌ Отклонить все тесты"
    back_to_senders_list_button: str = "⬅️ Назад к списку отправителей"
    to_main_menu_button: str = "В главное меню"
    back_button: str = "⬅️ Назад"
    no_test_from_user: str = "У вас нет активных тестов от этого пользователя."
    tests_from_username_button: str = "Тесты от отправителя @"
    tests_loading_error: str = "Произошла ошибка при загрузке тестов, попробуйте еще раз и сообщите об этом @Johnny_Taake."
    
    test_not_found: str = "Тест не найден"
    start_test_button: str = "✅ Начать тест"
    send_saved_result_button: str = "💾 Отправить результат"
    reject_test_button: str = "❌ Отклонить тест"
    back_to_tests_list_button: str = "⬅️ Назад к списку тестов"
    start_test_confirm: str = "Вы собираетесь начать тест:"
    start_test_confirm_2: str = "Подтвердите действие или вернуться назад."
    start_test_error: str = "Произошла ошибка при подготовке теста, попробуйте еще раз и сообщите об этом @Johnny_Taake."
    start_test_error_test_not_found: str = "Tест не найден, пожалуйста, сообщите об этом @Johnny_Taake."
    test_error_answers_processing_error: str = "Произошла ошибка при обработке ответа, попробуйте еще раз и сообщите об этом @Johnny_Taake."
    test_error_comment_processing_error: str = "Произошла ошибка при отображении комментария, сообщите об этом @Johnny_Taake."
    test_end_error: str = "Произошла ошибка при завершении теста, сообщите об этом @Johnny_Taake."
    other_tests_from_sender_button: str = "Другие тесты от этого отправителя"
    tests_from_other_senders_button: str = "Тесты от других отправителей"
    result_send_not_found_please_pass_test: str = "Результат не найден, пожалуйста, пройдите тест."
    result_send_error: str = "Произошла ошибка при подготовке отправки результата, попробуйте еще раз и сообщите об этом @Johnny_Taake."
    # send_test_result_confirm_1: str = "You are about to send the test result"
    # send_test_result_confirm_2: str = "Your score"
    # send_test_result_confirm_3: str = "Result interpretation"
    # send_test_result_confirm_4: str = "Are you sure you want to send this result?"
    # confirm_send_test_result_button: str = "Yes, send"
    # reject_send_test_result_button: str = "No, cancel"
    send_test_result_success_sent_1: str = "Результат теста"
    send_test_result_success_sent_2: str = "был успешно отправлен.\n\nВаш результат:"
    # send_result_cancel: str = "Отправка результата отменена."
    back_to_recived_tests_button: str = "⬅️ Назад к полученным тестам"
    confirm_reject_test_button: str = "✅ Да, отклонить"
    cancel_reject_test_button: str = "⬅️ Нет, вернуться назад"
    reject_test_confirm: str = "Вы уверены, что хотите отклонить этот тест?"
    reject_test_error: str = "Произошла ошибка при отклонении теста, попробуйте еще раз и сообщите об этом @Johnny_Taake."
    reject_all_tests_from_user: str = "❌ Отклонить все тесты"
    reject_test_from_user_canceled: str = "Отклонение теста отменено."
    no_tests_from_user: str = "У вас нет активных тестов от этого пользователя."
    error_loading_tests: str = "Произошла ошибка при загрузке тестов, попробуйте еще раз и сообщите об этом @Johnny_Taake."
    sender_info_not_found_error: str = "Извините, произошла ошибка. Не удалось найти информацию о отправителе, сообщите об этом @Johnny_Taake."
    confirm_reject_all_test_button: str = "✅ Да, отклонить все"
    reject_all_tests_confirmation: str = "Вы уверены, что хотите отклонить все тесты от пользователя"
    reject_all_tests_error: str = "Произошла ошибка при отклонении тестов, попробуйте еще раз и сообщите об этом @Johnny_Taake."
    confirm_error: str = "Произошла ошибка при подтверждении, попробуйте еще раз и сообщите об этом @Johnny_Taake."


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
    send_test: SendTestTexts = SendTestTexts()
    on_start_text: OnStartTexts = OnStartTexts()
    received_tests: ReceivedTestTexts = ReceivedTestTexts()



settings = Settings()
