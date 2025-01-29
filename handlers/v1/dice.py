# testing scripts, here got a working dice game

from typing import Any
import asyncio

from aiogram import Router, types
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.enums.dice_emoji import DiceEmoji

from core.models import db_helper
from ..utils import send_or_edit_message


router = Router()

@router.callback_query(lambda c: c.data == "dice")
async def dice(callback_query: types.CallbackQuery, bot: Bot, **kwargs: Any):
    await callback_query.answer()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Main Menu", url=None, callback_data="back_to_start")]])  # TODO: Make configurable
    
    text = "Your dice roll is..." 
    
    from services.text_service import TextService
    
    async with db_helper.db_session() as session:
        media = await TextService.get_default_media(session) 
    
    await send_or_edit_message(callback_query.message, text, keyboard, media)
    
    result = await bot.send_dice(callback_query.from_user.id, emoji=DiceEmoji.DICE)
    
    await asyncio.sleep(4)
    
    await bot.send_message(callback_query.from_user.id, f"Result: {result.dice.value}")
