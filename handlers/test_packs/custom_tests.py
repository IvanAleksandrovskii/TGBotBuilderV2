# handlers/test_packs/custom_tests.py

from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
# from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from handlers.test_packs.send_tests_pack import get_gefault_media
from handlers.v1.utils import send_or_edit_message


router = Router()


@router.callback_query(F.data == "my_custom_tests")
async def my_custom_tests(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer("Command called")
    await state.clear()
    
    media = await get_gefault_media()
    text = ( 
            "Comming soon..."
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    button_0 = InlineKeyboardButton(text="🔙 Back", callback_data="send_tests_pack")
    keyboard.inline_keyboard.append([button_0])
    
    await send_or_edit_message(callback_query, text, keyboard, media)
