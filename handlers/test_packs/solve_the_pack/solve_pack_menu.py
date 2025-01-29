# handlers/test_packs/solve_the_pack/solve_pack_menu.py

# from uuid import UUID
# from sqlalchemy.orm import selectinload
from sqlalchemy import select

from aiogram import Router, types, F
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from jinja2 import Environment, FileSystemLoader

from core import log
from core.models import (
    db_helper,
    TestPackCompletion,
)
from handlers.utils import send_or_edit_message, get_default_media
# from handlers.test_packs.solve_the_pack.notifications_for_creator import notify_creator


router = Router()


# jinja environment
env = Environment(
    loader=FileSystemLoader("handlers/test_packs/solve_the_pack/templates")
)


async def get_solve_test_menu(message: types.Message, state: FSMContext):
    data = await state.get_data()
    test_pack_completion_id = data.get('test_pack_completion_id')
    
    async with db_helper.db_session() as session:
        try:
            test_pack_completion_query = select(TestPackCompletion).where(TestPackCompletion.id == test_pack_completion_id)
            test_pack_completion = await session.execute(test_pack_completion_query)
            test_pack_completion = test_pack_completion.scalar_one_or_none()
            
            if not test_pack_completion:
                await message.answer("Test pack completion not found, ERROR")
                return
        except Exception as e:
            log.exception(f"Error in get_solve_test_menu: {e}")
            await message.answer("An error occurred. Please try again later.")

    await message.answer(f"Test pack completion found: {test_pack_completion.status.value}")
