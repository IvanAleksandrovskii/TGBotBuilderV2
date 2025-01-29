# handlers/abort.py

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core import log
from handlers.utils import send_or_edit_message
from handlers.on_start import get_start_content, FirstGreetingStates
from services import UserService


router = Router()


@router.message(Command("abort"))
async def abortk(message: types.Message, state: FSMContext) -> None:
    chat_id = int(message.chat.id)
    username = message.from_user.username
    
    # Get start content will create user if needed
    text, keyboard, media_url, is_new_user = await get_start_content(chat_id, username)
    
    # Now get the user that was just created or retrieved
    user = await UserService.get_user(chat_id)
    
    if not user:
        log.error(f"Failed to get/create user for chat_id {chat_id}")
        await message.answer("An error occurred. Please try again later.")
        return

    # Set state and send message
    if is_new_user:
        await state.set_state(FirstGreetingStates.GREETING)
    else:
        await state.clear()
    
    await send_or_edit_message(message, text, keyboard, media_url)
