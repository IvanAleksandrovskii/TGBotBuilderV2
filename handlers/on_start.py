# handlers/on_start.py

from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import log, settings
from core.models import (
    db_helper,
)
from core.models.test_pack_completion import TestPackCompletion, CompletionStatus
from core.models.sent_test import SentTest, TestStatus
from services import UserService
from services.text_service import TextService
from services.button_service import ButtonService

from .utils import send_or_edit_message

from handlers.test_packs.solve_the_pack import start_solve_the_pack, SolveThePackStates

from handlers.test_packs.solve_the_pack.solve_pack_menu import (
    get_solve_test_menu,
)

from handlers.test_packs.solve_the_test.inside_the_custom_test import (
    PassCustomTestStates,
)
from handlers.test_packs.solve_the_test.inside_the_psychological_test import (
    PassingTestStates,
)
from handlers.test_packs.solve_the_pack.solve_test import PassTestMenuStates


router = Router()


async def notify_creator_completion_continued(
    message: types.Message, test_pack_completion: TestPackCompletion
):
    await message.bot.send_message(
        test_pack_completion.test_pack_creator_id,
        "1 test pack completion was continued.",
    )


async def continue_completion(
    message: types.Message,
    test_pack_completion: TestPackCompletion,
    session: AsyncSession,
):
    await notify_creator_completion_continued(message, test_pack_completion)
    test_pack_completion.status = CompletionStatus.IN_PROGRESS
    session.add(test_pack_completion)
    await session.commit()


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
                log.info(
                    "Created new user: %s, username: %s", user.chat_id, user.username
                )
                is_new_user = True
            elif user.username != username:
                updated = await user_service.update_username(chat_id, username)
                if updated:
                    log.info("Updated username for user %s to %s", chat_id, username)
                else:
                    log.warning("Failed to update username for user %s", chat_id)

            context_marker = (
                "first_greeting"
                if is_new_user or user.is_new_user
                else "welcome_message"
            )
            content = await text_service.get_text_with_media(context_marker, session)

            if not content:
                log.warning("Content not found for marker: %s", context_marker)
                return settings.bot_main_page_text.user_error_message, None, None, False

            text = content["text"]
            media_url = content["media_urls"][0] if content["media_urls"] else None

            formatted_text = text.replace(
                "{username}",
                username or settings.bot_main_page_text.welcome_fallback_user_word,
            )

            keyboard = await button_service.create_inline_keyboard(
                context_marker, session
            )

            log.debug("Media URL: %s", media_url)
            log.debug("Formatted text: %s", formatted_text)

            if not media_url:
                media_url = await text_service.get_default_media(session)

            # Check for undelivered tests
            undelivered_tests = await session.execute(
                select(SentTest).where(
                    SentTest.receiver_username == username,
                    SentTest.status.in_([TestStatus.SENT, TestStatus.DELIVERED]),
                )
            )
            undelivered_tests = undelivered_tests.scalars().all()

            if undelivered_tests:
                new_keyboard = keyboard.inline_keyboard + [
                    [
                        types.InlineKeyboardButton(
                            text=settings.on_start_text.start_recived_tests_button,
                            callback_data="view_received_tests",
                        )
                    ]
                ]
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
async def start_command(message: types.Message, state: FSMContext):
    """Handler for /start command with promocode support"""
    args = message.text.split()[1:]
    chat_id = int(message.chat.id)
    username = message.from_user.username
    test_pack_id = args[0] if args else None

    user_service = UserService()

    current_state = await state.get_state()
    forbidden_states = [
        SolveThePackStates.WELCOME,
        SolveThePackStates.SOLVING,
        SolveThePackStates.COMPLETING,
        SolveThePackStates.ANSWERING_TEST,
        PassCustomTestStates.PASSING,
        PassCustomTestStates.QUESTION,
        PassingTestStates.VIEWING_INTRO,
        PassingTestStates.ANSWERING,
        PassingTestStates.SHOWING_COMMENT,
        PassingTestStates.SHOWING_RESULT,
        PassTestMenuStates.STARTING,
    ]

    if current_state in forbidden_states and test_pack_id is None:
        state_data = await state.get_data()
        test_pack_completion_id = state_data.get("test_pack_completion_id")

        await state.set_state(SolveThePackStates.SOLVING)
        await state.update_data(test_pack_completion_id=test_pack_completion_id)

        await get_solve_test_menu(message, state)
        return

    # Now get the user that was just created or retrieved
    user = await user_service.get_user(chat_id)

    if not user:
        user = await user_service.create_user(chat_id, username)
        log.info("Created new user: %s, username: %s", user.chat_id, user.username)
    elif user.username != username:
        updated = await user_service.update_username(chat_id, username)
        if updated:
            log.info("Updated username for user %s to %s", chat_id, username)
        else:
            log.warning("Failed to update username for user %s", chat_id)

    # if not user.is_active:
    #     log.info("Blocked user pressed start command: %s", chat_id)
    #     await message.answer("Извините, ваш аккаунт заблокирован..")
    #     return

    # If user came to solve the pack
    if test_pack_id:
        log.info(
            f"Start command received. Chat ID: {chat_id}, Username: {username}, Test pack ID: {test_pack_id}"
        )
        async with db_helper.db_session() as session:
            try:
                existing_test_pack_completion_query = (
                    select(TestPackCompletion)
                    .where(TestPackCompletion.user_id == user.chat_id)
                    .where(TestPackCompletion.test_pack_id == test_pack_id)
                )

                existing_test_pack_completion = await session.execute(
                    existing_test_pack_completion_query
                )
                existing_test_pack_completion = (
                    existing_test_pack_completion.scalar_one_or_none()
                )
            except Exception as e:
                log.exception(f"Error in get_start_content: {e}")
                existing_test_pack_completion = None

        if existing_test_pack_completion is not None:
            log.info(
                "User %s already has test pack completion %s", user.id, test_pack_id
            )

            if existing_test_pack_completion.status == CompletionStatus.COMPLETED:
                log.info("Test pack completion %s already completed", test_pack_id)

                # Generate the jinja environment and render the template
                env = Environment(
                    loader=FileSystemLoader(
                        "handlers/test_packs/solve_the_pack/templates"
                    )
                )
                template = env.get_template("start_solved_pack.html")
                await send_or_edit_message(message, template.render(), None, None)
                return

            if existing_test_pack_completion.status == CompletionStatus.IN_PROGRESS:
                log.info(
                    "Test pack completion %s already in progress",
                    existing_test_pack_completion.id,
                )
                await state.set_state(SolveThePackStates.SOLVING)
                await state.update_data(
                    test_pack_completion_id=existing_test_pack_completion.id
                )

                await get_solve_test_menu(message, state)
                return

            if existing_test_pack_completion.status == CompletionStatus.ABANDONED:
                await state.set_state(SolveThePackStates.SOLVING)
                await state.update_data(
                    test_pack_completion_id=existing_test_pack_completion.id
                )
                # TODO: Add notification for creator and set status to IN_PROGRESS (( ! ))
                await continue_completion(message, existing_test_pack_completion, session)
                await get_solve_test_menu(message, state)
                return

        await start_solve_the_pack(message, test_pack_id, state)
        return

    # Get start content will create user if needed
    text, keyboard, media_url, is_new_user = await get_start_content(chat_id, username)

    if not user:
        log.error(f"Failed to get/create user for chat_id {chat_id}")
        await message.answer("An error occurred. Please try again later.")
        return

    # Set state and send message
    if is_new_user:
        await state.set_state(FirstGreetingStates.GREETING)
    else:
        await state.clear()

    await send_or_edit_message(message, text, keyboard, media_url)


@router.callback_query(F.data == "end_first_greeting")
async def end_first_greeting(callback_query: types.CallbackQuery, state: FSMContext):

    await callback_query.answer("Главное меню")  # TODO: Move to config

    chat_id = int(callback_query.from_user.id)
    username = callback_query.from_user.username

    user_service = UserService()
    await user_service.mark_user_as_not_new(chat_id)

    text, keyboard, media_url, _ = await get_start_content(chat_id, username)
    await state.clear()
    await send_or_edit_message(callback_query, text, keyboard, media_url)


@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback_query: types.CallbackQuery, state: FSMContext):

    await callback_query.answer("Главное меню")  # TODO: Move to config

    await state.clear()
    chat_id = int(callback_query.from_user.id)
    username = callback_query.from_user.username
    text, keyboard, media_url, _ = await get_start_content(chat_id, username)
    await send_or_edit_message(callback_query.message, text, keyboard, media_url)


async def back_to_start_from_message(message: types.Message, state: FSMContext):
    await state.clear()
    chat_id = int(message.chat.id)
    username = message.from_user.username
    text, keyboard, media_url, _ = await get_start_content(chat_id, username)
    await send_or_edit_message(message, text, keyboard, media_url)
