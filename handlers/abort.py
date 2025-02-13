# handlers/abort.py

from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from core import log
from handlers.utils import send_or_edit_message
from handlers.on_start import get_start_content, FirstGreetingStates
from services import UserService

from services.decorators import handle_as_task, TaskPriority


router = Router()


@router.message(Command("abort"))
@handle_as_task(priority=TaskPriority.NORMAL)
async def abort(message: types.Message, state: FSMContext) -> None:
    # chat_id = int(message.chat.id)
    user_id = int(message.from_user.id)
    username = message.from_user.username

    await state.clear()

    # Get start content will create user if needed
    text, keyboard, media_url, is_new_user = await get_start_content(user_id, username)

    # Now get the user that was just created or retrieved
    user = await UserService.get_user(user_id)

    if not user:
        log.error(f"Failed to get/create user for user_id {user_id}")
        await message.answer("An error occurred. Please try again later.")
        return

    # Set state and send message
    if is_new_user:
        await state.set_state(FirstGreetingStates.GREETING)

    await send_or_edit_message(message, text, keyboard, media_url)
