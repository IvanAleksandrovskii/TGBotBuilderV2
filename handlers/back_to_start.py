# handlers/back_to_start.py

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from handlers.utils import send_or_edit_message
from handlers.on_start import get_start_content

from services.decorators import handle_as_task, TaskPriority
from core import log


router = Router()


@router.callback_query(F.data == "back_to_start")
@handle_as_task(priority=TaskPriority.NORMAL)
async def back_to_start(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Главное меню")  # TODO: Move to config

    await state.clear()
    user_id = int(callback_query.from_user.id)
    username = callback_query.from_user.username
    text, keyboard, media_url, _ = await get_start_content(user_id, username)
    await send_or_edit_message(callback_query.message, text, keyboard, media_url)


async def back_to_start_from_message(message: types.Message, state: FSMContext):
    await state.clear()
    # chat_id = int(message.chat.id)
    user_id = int(message.from_user.id)
    username = message.from_user.username
    text, keyboard, media_url, _ = await get_start_content(user_id, username)
    try:
        await message.answer(text, reply_markup=keyboard, media=media_url)
    except Exception as e:
        log.exception(e)
        await send_or_edit_message(message, text, keyboard, media_url)
