# handlers/tests_packs.py

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from handlers.utils import get_default_media
from handlers.utils import send_or_edit_message


router = Router()


@router.callback_query(F.data == "send_tests_pack")
@router.message(Command("send_tests_pack"))
async def tests_pack_menu(
    call: types.Message | types.CallbackQuery, state: FSMContext
) -> None:
    if isinstance(call, types.CallbackQuery):
        await call.answer("Command called")

    await state.clear()

    default_media = await get_default_media()

    button_0 = InlineKeyboardButton(
        text="❓Custom Tests & Test Packs",
        url="https://t.me/tap_quiz_bot/myapp",  # TODO: Fix, move to config
    )
    button_1 = InlineKeyboardButton(
        text="💽 Check My Tests Packs", callback_data="my_tests_packs"
    )

    # button_2 = InlineKeyboardButton(
    #     text="(OLD) 🔍 Check Tests Results", callback_data="tests_pack_check_result"
    # )
    # btn = InlineKeyboardButton(text="(OLD) 🆕 Create new Tests Pack", callback_data="tests_pack_create_new")

    button_2 = InlineKeyboardButton(text="🏡 Main menu", callback_data="back_to_start")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[button_0], [button_1], [button_2]]
    )

    text = (
        "Here you can open your Custom Tests & Test Packs App or quickly check your test packs you have created and get it's link.\n\n"
        "Choose an action:"
    )

    await send_or_edit_message(call, text, keyboard, default_media)
