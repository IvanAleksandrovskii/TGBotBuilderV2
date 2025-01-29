# handlers/test_packs/solve_the_pack/notifications_for_creator.py

from aiogram import types

from core import log
from core.models import db_helper
from core.models.test_pack import TestPack
from core.models.test_pack_completion import TestPackCompletion


# TODO: Make notifications for the test pack start and completion
async def notify_creator(message: types.Message, test_pack_creator_chat_id: int, text: str):
    
    username: str = message.from_user.username
    
    if username is None:
        username = message.from_user.first_name
    if (username.strip() == "") or (username is None):
        username = f"User {message.from_user.id}"
    
    notification_text: str = f"{username}: {text}" 
    
    await message.bot.send_message(test_pack_creator_chat_id, notification_text)


# TODO: Make resending condidate's CV to the test pack creator on the end of the test pack
