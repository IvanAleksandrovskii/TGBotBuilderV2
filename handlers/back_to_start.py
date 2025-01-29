# handlers/back_to_start.py

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from handlers.utils import send_or_edit_message
from handlers.on_start import get_start_content

router = Router()


@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Главное меню")  # TODO: Move to config

    await state.clear()
    chat_id = callback_query.from_user.id
    username = callback_query.from_user.username
    text, keyboard, media_url, _ = await get_start_content(chat_id, username)

    """
    await callback_query.bot.send_photo(
        callback_query.message.chat.id,
        photo=media_url,
        caption=text,
        reply_markup=keyboard,
    )"""

    await send_or_edit_message(callback_query, text, keyboard, media_url)
