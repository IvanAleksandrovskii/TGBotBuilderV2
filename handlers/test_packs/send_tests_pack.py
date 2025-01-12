# handlers/send_tests_pack.py

from async_lru import alru_cache

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton

from core import log
from core.models import db_helper
from services.text_service import TextService
# from services.user_services import UserService
# from services.button_service import ButtonService
from handlers.utils import send_or_edit_message

router = Router()

# class SendTestsPackState(StatesGroup):
#     naming_pack = State()
#     choosing_tests = State()


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
async def send_tests_pack(call: types.Message|types.CallbackQuery) -> None:
    if isinstance(call, types.CallbackQuery):
        await call.answer("Command called")
    
    default_media = await get_gefault_media()
    
    button_0 = InlineKeyboardButton(text="💽 Check My Tests Packs", callback_data="my_tests_packs")
    button_1 = InlineKeyboardButton(text="🆕 Create new Tests Pack", callback_data="tests_pack_create_new")
    button_2 = InlineKeyboardButton(text="🔍 Check Tests Results", callback_data="tests_pack_check_result")
    button3 = InlineKeyboardButton(text="🏡 Main menu", callback_data="back_to_start")
    
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_0], [button_1], [button_2], [button3]])
    
    text = (
        "Here you can check test packs you have created or create the new one.\n\n"
        "Choose an action:"
    )
    
    await send_or_edit_message(call, text, keyboard, default_media)


@router.callback_query(F.data == "my_tests_packs")
async def my_tests_packs(callback_query: types.CallbackQuery) -> None:
    await callback_query.answer("Command called")

    default_media = await get_gefault_media()
    
    button_0 = InlineKeyboardButton(text="🔙 Back", callback_data="send_tests_pack")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_0]])
    
    text = (
        "Comming soon..."
    )
    await send_or_edit_message(callback_query, text, keyboard, default_media)


@router.callback_query(F.data == "tests_pack_create_new")
async def tests_pack_create_new(callback_query: types.CallbackQuery) -> None:
    await callback_query.answer("Command called")

    default_media = await get_gefault_media()
    
    button_0 = InlineKeyboardButton(text="🔙 Back", callback_data="send_tests_pack")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_0]])
    
    text = (
        "Comming soon..."
    )
    await send_or_edit_message(callback_query, text, keyboard, default_media)


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
