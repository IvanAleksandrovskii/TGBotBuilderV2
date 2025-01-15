# handlers/test_packs/custom_tests.py

from sqlalchemy import select

from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from handlers.test_packs.send_tests_pack import get_gefault_media
from handlers.v1.utils import send_or_edit_message

from core import log
from core.models import db_helper
from core.models.custom_test import CustomTest

router = Router()


@router.callback_query(F.data == "my_custom_tests")
async def my_custom_tests(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer("Command called")
    await state.clear()
    
    media = await get_gefault_media()
    text = "Your custom tests:\n\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    async with db_helper.db_session() as session:
        try:
            custom_tests_query = select(CustomTest).where(CustomTest.creator_id == callback_query.from_user.id)
            
            custom_tests = await session.execute(custom_tests_query)
            custom_tests = custom_tests.scalars().all()
            
            if len(custom_tests) == 0:
                text += "You have no custom tests yet."
            
            for custom_test in custom_tests:
                btn = InlineKeyboardButton(text=custom_test.name, callback_data=f"custom_test_{custom_test.id}")
                keyboard.inline_keyboard.append([btn])
            
        except Exception as e:
            log.error(e)
            text += "Error while fetching custom tests."
    
    if len(custom_tests) <= 3:
        button_create_test = InlineKeyboardButton(text="📝 Create test", url="https://s3dbwm-ip-49-228-96-123.tunnelmole.net")  # TODO: FIX
        keyboard.inline_keyboard.append([button_create_test])
    else:
        button_create_test = InlineKeyboardButton(text="📝 Create test", callback_data="custom_tests_full")
        keyboard.inline_keyboard.append([button_create_test])
        
    button_back = InlineKeyboardButton(text="🔙 Back", callback_data="send_tests_pack")
    keyboard.inline_keyboard.append([button_back])
    
    await send_or_edit_message(callback_query, text, keyboard, media)


@router.callback_query(F.data == "custom_tests_full")
async def custom_test(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer("Command called")
    await callback_query.message.answer("You have 3 tests created, please delete some to create more.")


@router.callback_query(F.data.startswith("custom_test_"))
async def custom_test(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer("Command called")
    
    parts = callback_query.data.split("_")
    custom_test_id = parts[-1]

    media = await get_gefault_media()
    
    async with db_helper.db_session() as session:
        try:
            custom_test_query = select(CustomTest).where(CustomTest.id == custom_test_id)
            custom_test = await session.execute(custom_test_query)
            custom_test = custom_test.scalars().one()
        except Exception as e:
            log.error(e)
            await callback_query.message.answer("Error while fetching custom test.")
            return
    
    text = f"Custom test: {custom_test.name}\n\n"
    text += "Description:\n"
    text += custom_test.description
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    button_delete = InlineKeyboardButton(text="🗑 Delete", callback_data=f"delete_custom_test_{custom_test.id}")
    keyboard.inline_keyboard.append([button_delete])
    
    button_back = InlineKeyboardButton(text="🔙 Back", callback_data="my_custom_tests")
    keyboard.inline_keyboard.append([button_back])
    
    await send_or_edit_message(callback_query, text, keyboard, media)


@router.callback_query(F.data.startswith("delete_custom_test_"))
async def delete_custom_test(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer("Command called")
