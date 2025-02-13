# handlers/tests_packs.py

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from core import settings
from handlers.utils import get_default_media
from handlers.utils import send_or_edit_message

from services.decorators import handle_as_task, TaskPriority


router = Router()


@router.callback_query(F.data == "send_tests_pack")
@router.message(Command("send_tests_pack"))
@handle_as_task(priority=TaskPriority.NORMAL)
async def tests_pack_menu(
    call: types.Message | types.CallbackQuery, state: FSMContext
) -> None:
    if isinstance(call, types.CallbackQuery):
        await call.answer()

    await state.clear()
    
    bot_username = (await call.bot.get_me()).username
    app_url = f"https://t.me/{bot_username}/{settings.bot.app_name}"

    default_media = await get_default_media()

    button_0 = InlineKeyboardButton(
        text="❓Наборы тестов и кастомные тесты",  # TODO: Move to config
        url=app_url,  # TODO: Fix, move to config
    )
    button_1 = InlineKeyboardButton(
        text="💽 Мои наборы тестов", callback_data="my_tests_packs"  # TODO: Move to config
    )

    # button_2 = InlineKeyboardButton(
    #     text="(OLD) 🔍 Check Tests Results", callback_data="tests_pack_check_result"
    # )
    # btn = InlineKeyboardButton(text="(OLD) 🆕 Create new Tests Pack", callback_data="tests_pack_create_new")

    button_2 = InlineKeyboardButton(text="🏡 Главное меню", callback_data="back_to_start")  # TODO: Move to config

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[button_0], [button_1], [button_2]]
    )

    text = (
        "Здесь вы можете открыть приложение \"Наборы тестов и кастомные тесты\" или быстро проверить свои наборы тестов, которые вы создали, "
        "а так же получить ссылку на прохождение.\n\n"
        "Выберите действие:"
    )  # TODO: Move to config

    await send_or_edit_message(call, text, keyboard, default_media)
