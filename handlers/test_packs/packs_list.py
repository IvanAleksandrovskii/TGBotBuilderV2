# handlers/test_packs/packs_list.py

from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy import select

from core import log
from core.models import db_helper
from core.models.test_pack import TestPack
from handlers.utils import send_or_edit_message

from ..utils import get_default_media


router = Router()


class TestPackDeleteState(StatesGroup):
    DELETING = State()


@router.callback_query(F.data == "my_tests_packs")
async def my_tests_packs(callback_query: types.CallbackQuery, state: FSMContext) -> None:  # TODO: Add link (to pass the pack) to the output
    
    await callback_query.answer("Command called")
    await state.clear()
    
    default_media = await get_default_media()
    
    text = ""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    async with db_helper.db_session() as session:
        try:
            test_packs_query = select(TestPack).where(TestPack.creator_id == callback_query.from_user.id)
            test_packs = await session.execute(test_packs_query)
            test_packs = test_packs.scalars().all()
            
            if test_packs:
                text += "Here is your test packs:\n\n"
            else:
                text += "You don't have any test packs created yet.\n\n"
            
        except Exception as e:
            log.exception(f"Error in my_tests_packs: {e}")
            text += "An error occurred while loading your test packs. Please try again."
            test_packs = []
    
    for test_pack in test_packs:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=(f"{test_pack.name} - ({test_pack.test_count} tests inside)"), callback_data=f"test_pack_check_{test_pack.id}")])
    
    button_0 = InlineKeyboardButton(text="🔙 Back", callback_data="send_tests_pack")
    keyboard.inline_keyboard.append([button_0])
    
    await send_or_edit_message(callback_query, text, keyboard, default_media)


@router.callback_query(TestPackDeleteState.DELETING, F.data.startswith("test_pack_check_"))
@router.callback_query(F.data.startswith("test_pack_check_"))
async def test_pack_check(callback_query: types.CallbackQuery, state: FSMContext):
    
    await callback_query.answer("Command called")
    await state.clear()
    
    parts = callback_query.data.split("_")
    test_pack_id = parts[-1]
    
    media = await get_default_media()
    
    async with db_helper.db_session() as session:
        try:
            test_query = select(TestPack).where(TestPack.id == test_pack_id)
            test_pack = await session.execute(test_query)
            test_pack = test_pack.scalar_one_or_none()
            
        except Exception as e:
            log.exception(f"Error in test_pack_check: {e}")
            test_pack = None
            
    if not test_pack:
        await callback_query.answer("Test pack not found, ERROR")
        return
    
    text = f"Test pack: {test_pack.name}\n\n"
    
    bot_username = (await callback_query.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start={test_pack.id}"
    text += f"Invite link: \n<code>{invite_link}</code>\n\n"
    
    text += f"Tests inside: {test_pack.test_count}\n\n"
    
    for test in test_pack.tests:
        text += f"● {test.name}\n\n"
        # text += f"Description: {test.description[:100]}...\n\n"
    
    for custom_test in test_pack.custom_tests:
        text += f"● {custom_test.name}\n\n"
        # text += f"Description: {custom_test.description[:100]}...\n\n"
    
    # text += f"Creator: {test_pack.creator_username}\n\n"
    # text += f"Created at: {test_pack.created_at}\n\n"  # TODO: подумать, как добавить, чтобы отображать в формате для пользователя
    # text += f"Updated at: {test_pack.updated_at}\n\n"
    
    button_delete = InlineKeyboardButton(text="❌ Delete", callback_data=f"test_pack_delete_{test_pack.id}")
    
    button_0 = InlineKeyboardButton(text="🔙 Back", callback_data="my_tests_packs")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_delete], [button_0]])
    
    await send_or_edit_message(callback_query, text, keyboard, media)


@router.callback_query(F.data.startswith("test_pack_delete_"))
async def test_pack_delete(callback_query: types.CallbackQuery, state: FSMContext):
    
    await callback_query.answer("Command called")
    await state.set_state(TestPackDeleteState.DELETING)
    
    parts = callback_query.data.split("_")
    test_pack_id = parts[-1]
    
    await state.update_data(test_pack_id=test_pack_id)
    
    media = await get_default_media()

    text = f"Are you sure you want to delete test pack?"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Yes", callback_data="yes")],
        [types.InlineKeyboardButton(text="No", callback_data=f"test_pack_check_{test_pack_id}")]
    ])
    
    await send_or_edit_message(callback_query, text, keyboard, media)


@router.callback_query(TestPackDeleteState.DELETING, F.data == "yes")
async def test_pack_delete_yes(callback_query: types.CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    await state.clear()
    test_pack_id = state_data["test_pack_id"]
    
    async with db_helper.db_session() as session:
        try:
            test_pack_query = select(TestPack).where(TestPack.id == test_pack_id)
            test_pack = await session.execute(test_pack_query)
            test_pack = test_pack.scalar_one_or_none()
            
            if not test_pack:
                await callback_query.answer("Test pack not found, ERROR")
                return
            
            await session.delete(test_pack)
            await session.commit()
            
            await callback_query.answer("Test pack deleted seccessfully")
            
        except Exception as e:
            log.exception(f"Error in test_pack_delete_yes: {e}")
            await callback_query.answer("An error occurred while deleting test pack. Please try again.")
    await my_tests_packs(callback_query, state)
