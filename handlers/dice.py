# testing scripts, here got a working dice

from typing import Any
from icecream import ic
import asyncio

from aiogram import Router, types
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from aiogram.enums.dice_emoji import DiceEmoji

from core.models import db_helper
from .utils import send_or_edit_message


router = Router()

@router.callback_query(lambda c: c.data == "dice")
async def back_to_start(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot, **kwargs: Any):

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="restart", url=None, callback_data="back_to_start")]])
    
    text = "Your dice roll is..."  # TODO: Make configurable
    ic(kwargs)
    
    from services.text_service import TextService
    
    async with db_helper.db_session() as session:
        media = await TextService.get_default_media(session)  # TODO: Make configurable
    
    await send_or_edit_message(callback_query.message, text, keyboard, media)
    
    # await asyncio.sleep(5)
    
    result = await bot.send_dice(callback_query.from_user.id, emoji=DiceEmoji.DICE)
    
    await asyncio.sleep(4)
    
    await bot.send_message(callback_query.from_user.id, f"Result: {result.dice.value}")
