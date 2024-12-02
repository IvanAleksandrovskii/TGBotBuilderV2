# handlers/on_start.py

from datetime import datetime

from aiogram import Router, Bot, types
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy import select

from core import log, settings
from core.models import db_helper
from core.models.sent_test import SentTest, TestStatus
from services import UserService
from services.promocode_service import PromoCodeService
from services.text_service import TextService
from services.button_service import ButtonService
from .utils import send_or_edit_message


router = Router()


# TODO: Add sent tests deletion if tests are not existing anymore
class FirstGreetingStates(StatesGroup):
    GREETING = State()


async def get_start_content(chat_id: int, username: str | None):
    user_service = UserService()
    text_service = TextService()
    button_service = ButtonService()
    async for session in db_helper.session_getter():
        try:
            user = await user_service.get_user(chat_id)
            is_new_user = False
            if not user:
                user = await user_service.create_user(chat_id, username)
                log.info("Created new user: %s, username: %s", user.chat_id, user.username)
                is_new_user = True
            elif user.username != username:
                updated = await user_service.update_username(chat_id, username)
                if updated:
                    log.info("Updated username for user %s to %s", chat_id, username)
                else:
                    log.warning("Failed to update username for user %s", chat_id)

            context_marker = "first_greeting" if is_new_user or user.is_new_user else "welcome_message"
            content = await text_service.get_text_with_media(context_marker, session)
            
            if not content:
                log.warning("Content not found for marker: %s", context_marker)
                return settings.bot_main_page_text.user_error_message, None, None, False

            text = content["text"]
            media_url = content["media_urls"][0] if content["media_urls"] else None

            formatted_text = text.replace("{username}", username or settings.bot_main_page_text.welcome_fallback_user_word)
            
            keyboard = await button_service.create_inline_keyboard(context_marker, session)

            log.debug("Media URL: %s", media_url)
            log.debug("Formatted text: %s", formatted_text)

            if not media_url:
                media_url = await text_service.get_default_media(session)
            
            
            # Check for undelivered tests
            undelivered_tests = await session.execute(
                select(SentTest)
                .where(SentTest.receiver_username == username, SentTest.status.in_([TestStatus.SENT, TestStatus.DELIVERED]))
            )
            undelivered_tests = undelivered_tests.scalars().all()

            if undelivered_tests:
                new_keyboard = keyboard.inline_keyboard + [[types.InlineKeyboardButton(text=settings.on_start_text.start_recived_tests_button, callback_data="view_received_tests")]]
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=new_keyboard)
                
                # Notify senders
                for test in undelivered_tests:
                    if test.status == TestStatus.SENT:
                        test.status = TestStatus.DELIVERED
                        test.delivered_at = datetime.now()
                        test.receiver_id = chat_id
                await session.commit()
            
            return formatted_text, keyboard, media_url, is_new_user or user.is_new_user

        except Exception as e:
            log.error("Error in get_start_content: %s", e)
            return settings.bot_main_page_text.user_error_message, None, None, False
        finally:
            await session.close()


@router.message(Command("start"))
async def start_command(message: types.Message, bot: Bot, state: FSMContext):
    """Handler for /start command with promocode support"""
    args = message.text.split()[1:]
    chat_id = int(message.chat.id)
    username = message.from_user.username
    promocode = args[0] if args else None
    
    log.info(f"Start command received. Chat ID: {chat_id}, Username: {username}, Promocode: {promocode}")

    # Get start content will create user if needed
    text, keyboard, media_url, is_new_user = await get_start_content(chat_id, username)
    
    # Now get the user that was just created or retrieved
    user_service = UserService()
    user = await user_service.get_user(chat_id)
    
    if not user:
        log.error(f"Failed to get/create user for chat_id {chat_id}")
        await message.answer("An error occurred. Please try again later.")
        return

    # Handle promocode if provided and user is new
    if promocode and is_new_user:
        log.info(f"Processing promocode {promocode} for new user {chat_id}")
        try:
            success = await PromoCodeService.register_promo_usage(promocode, user.id)
            if success:
                log.info(f"Successfully registered promocode usage for user {chat_id}")
                # Optionally notify about successful referral
                # await message.answer("Welcome! You've joined using a referral link!")
            else:
                log.info(f"Failed to register promocode usage for user {chat_id}, might be already registered")
        except Exception as e:
            log.exception(f"Error processing promocode: {e}")
    elif promocode and not is_new_user:
        log.info(f"Existing user {chat_id} tried to use promocode {promocode}")
        # await message.answer("Promocodes are only for new users!")
        # return

    # Set state and send message
    if is_new_user:
        await state.set_state(FirstGreetingStates.GREETING)
    else:
        await state.clear()
    
    await send_or_edit_message(message, text, keyboard, media_url)


@router.callback_query(lambda c: c.data == "end_first_greeting")
async def end_first_greeting(callback_query: types.CallbackQuery, state: FSMContext):
    
    await callback_query.answer("Going to Bot")  # TODO: Move to config
    
    chat_id = int(callback_query.from_user.id)
    username = callback_query.from_user.username

    user_service = UserService()
    await user_service.mark_user_as_not_new(chat_id)

    text, keyboard, media_url, _ = await get_start_content(chat_id, username)
    await state.clear()
    await send_or_edit_message(callback_query, text, keyboard, media_url)


@router.callback_query(lambda c: c.data == "back_to_start")
async def back_to_start(callback_query: types.CallbackQuery, state: FSMContext):
    
    await callback_query.answer("Back to start")  # TODO: Move to config
    
    await state.clear()
    chat_id = int(callback_query.from_user.id)
    username = callback_query.from_user.username
    text, keyboard, media_url, _ = await get_start_content(chat_id, username)
    await send_or_edit_message(callback_query.message, text, keyboard, media_url)
