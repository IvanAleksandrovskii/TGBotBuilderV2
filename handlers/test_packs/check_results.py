# handlers/test_packs/check_results.py

from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from handlers.v1.utils import send_or_edit_message

from .send_tests_pack import get_gefault_media


router = Router()


@router.callback_query(F.data == "tests_pack_check_result")
async def tests_pack_check_result(callback_query: types.CallbackQuery) -> None:
    await callback_query.answer("Command called")

    default_media = await get_gefault_media()
    
    button_0 = InlineKeyboardButton(text="🔙 Back", callback_data="send_tests_pack")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_0]])
    
    text = (
        "Comming soon..."
    )
    await send_or_edit_message(callback_query, text, keyboard, default_media)
