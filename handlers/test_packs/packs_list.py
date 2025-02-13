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

from handlers.utils import get_default_media

from services.decorators import handle_as_task, TaskPriority


router = Router()


class TestPackDeleteState(StatesGroup):
    DELETING = State()


@router.callback_query(F.data == "my_tests_packs")
@handle_as_task(priority=TaskPriority.NORMAL)
async def my_tests_packs(callback_query: types.CallbackQuery, state: FSMContext) -> None:  # TODO: Add link (to pass the pack) to the output
    
    await callback_query.answer()
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
                text += "Ваши наборы тестов:\n\n"  # TODO: Move to config
            else:
                text += "Вы пока не создали ни одного набора тестов, перейдите назад и отройте приложение для создания набора тестов.\n\n"  # TODO: Move to config
            
        except Exception as e:
            log.exception(f"Error in my_tests_packs: {e}")
            text += "Произошла ошибка при загрузке ваших наборов тестов. Попробуйте позже. Пожалуйста, нажмите -> /abort"  # TODO: Move to config
            test_packs = []
    
    for test_pack in test_packs:
        keyboard.inline_keyboard.append([InlineKeyboardButton(text=(f"{test_pack.name} - ({test_pack.test_count} тестов внутри)"), callback_data=f"test_pack_check_{test_pack.id}")])
    
    button_0 = InlineKeyboardButton(text="🔙 Назад", callback_data="send_tests_pack")  # TODO: Move to config
    keyboard.inline_keyboard.append([button_0])
    
    await send_or_edit_message(callback_query, text, keyboard, default_media)


@router.callback_query(TestPackDeleteState.DELETING, F.data.startswith("test_pack_check_"))
@router.callback_query(F.data.startswith("test_pack_check_"))
@handle_as_task(priority=TaskPriority.NORMAL)
async def test_pack_check(callback_query: types.CallbackQuery, state: FSMContext):
    
    await callback_query.answer()
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
        await callback_query.answer("Набор тестов не найден, ошибка.")  # TODO: Move to config
        return
    
    text = f"Набор тестов: {test_pack.name}\n\n"  # TODO: Move to config
    
    bot_username = (await callback_query.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start={test_pack.id}"
    text += f"Пригласительная ссылка: \n<code>{invite_link}</code>\n\n"  # TODO: Move to config
    
    text += f"Тесты внутри: {test_pack.test_count}\n\n"  # TODO: Move to config
    
    for test in test_pack.tests:
        text += f"● {test.name}\n\n"
        # text += f"Description: {test.description[:100]}...\n\n"
    
    for custom_test in test_pack.custom_tests:
        text += f"● {custom_test.name}\n\n"
        # text += f"Description: {custom_test.description[:100]}...\n\n"
    
    # text += f"Creator: {test_pack.creator_username}\n\n"
    # text += f"Created at: {test_pack.created_at}\n\n"  # TODO: подумать, как добавить, чтобы отображать в формате для пользователя
    # text += f"Updated at: {test_pack.updated_at}\n\n"
    
    button_delete = InlineKeyboardButton(text="❌ Удалить", callback_data=f"test_pack_delete_{test_pack.id}")  # TODO: Move to config
    
    button_0 = InlineKeyboardButton(text="🔙 Назад", callback_data="my_tests_packs")  # TODO: Move to config
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_delete], [button_0]])
    
    await send_or_edit_message(callback_query, text, keyboard, media)


@router.callback_query(F.data.startswith("test_pack_delete_"))
@handle_as_task(priority=TaskPriority.NORMAL)
async def test_pack_delete(callback_query: types.CallbackQuery, state: FSMContext):
    
    await callback_query.answer()
    await state.set_state(TestPackDeleteState.DELETING)
    
    parts = callback_query.data.split("_")
    test_pack_id = parts[-1]
    
    await state.update_data(test_pack_id=test_pack_id)
    
    media = await get_default_media()

    text = f"Вы уверены, что хотите удалить набор тестов?"  # TODO: Move to config
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Да", callback_data="yes")],  # TODO: Move to config
        [types.InlineKeyboardButton(text="Нет", callback_data=f"test_pack_check_{test_pack_id}")]  # TODO: Move to config
    ])
    
    await send_or_edit_message(callback_query, text, keyboard, media)


@router.callback_query(TestPackDeleteState.DELETING, F.data == "yes")
@handle_as_task(priority=TaskPriority.NORMAL)
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
                await callback_query.answer("Набор тестов не найден, ошибка.")  # TODO: Move to config
                return
            
            await session.delete(test_pack)
            await session.commit()
            
            await callback_query.answer("Набор тестов удален.")  # TODO: Move to config
            
        except Exception as e:
            log.exception(f"Error in test_pack_delete_yes: {e}")
            await callback_query.answer("Ошибка при удалении набора тестов. Пожалуйста, попробуйте еще раз.")  # TODO: Move to config
    await my_tests_packs(callback_query, state)
