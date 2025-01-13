# handlers/send_tests_pack.py

from async_lru import alru_cache

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from core import log
from core.models import db_helper
from services.text_service import TextService
# from services.user_services import UserService
# from services.button_service import ButtonService
from handlers.v1.utils import send_or_edit_message

router = Router()


@alru_cache(maxsize=1, ttl=60)
async def get_gefault_media() -> str:
    text_service = TextService()
    async with db_helper.db_session() as session:
        try:
            default_media = await text_service.get_default_media(session)
        except Exception as e:
            log.exception(f"Error in getting default media: {e}")
            default_media = None
    return default_media


@router.callback_query(F.data == "send_tests_pack")
@router.message(Command("send_tests_pack"))
async def tests_pack_menu(call: types.Message|types.CallbackQuery, state: FSMContext) -> None:
    if isinstance(call, types.CallbackQuery):
        await call.answer("Command called")
    
    await state.clear()
    
    default_media = await get_gefault_media()
    
    button_0 = InlineKeyboardButton(text="💽 Check My Tests Packs", callback_data="my_tests_packs")
    button_1 = InlineKeyboardButton(text="🆕 Create new Tests Pack", callback_data="tests_pack_create_new")
    button_2 = InlineKeyboardButton(text="🔍 Check Tests Results", callback_data="tests_pack_check_result")
    button_3 = InlineKeyboardButton(text="❓Custom Tests", callback_data="my_custom_tests")
    button_4 = InlineKeyboardButton(text="🏡 Main menu", callback_data="back_to_start")
    
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_0], [button_1], [button_2], [button_3], [button_4]])
    
    text = (
        "Here you can check test packs you have created or create the new one.\n\n"
        "Choose an action:"
    )
    
    await send_or_edit_message(call, text, keyboard, default_media)
