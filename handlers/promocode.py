# handlers/promocode.py

from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from core import log
from services import UserService
from services.promocode_service import PromoCodeService

router = Router()


@router.callback_query(lambda c: c.data == "getpromo")
async def get_promo_command(message: types.Message, state: FSMContext):
    """Handler for /getpromo command that generates a promocode for the user"""
    try:
        chat_id = message.from_user.id
        
        # Get user from database
        user = await UserService().get_user(chat_id)
        if not user:
            await message.answer("You need to start the bot first with /start")
            return

        # Generate promocode
        promocode = await PromoCodeService.create_promocode(user.id)
        # if not promocode:
        #     await message.answer("You already have an active promocode!")
        #     return

        bot_username = (await message.bot.get_me()).username
        invite_link = f"https://t.me/{bot_username}?start={promocode.code}"
        
        # await message.answer(
        #     f"Here's your unique invite link:\n{invite_link}\n\n"
        #     f"Share it with friends! We'll track how many people join using your link."
        # )  # TODO: Fix this, make a separate message instead of alert answer
        
        # from core.models import db_helper
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        btn = InlineKeyboardButton(
                text="main manu",
                url=None,
                callback_data="back_to_start"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn]])
                
        from .utils import send_or_edit_message

        await send_or_edit_message(message, f"Here's your unique invite link:\n{invite_link}\n\nShare it with friends! We'll track how many people join using your link.", keyboard, None)

    except Exception as e:
        log.exception(f"Error in get_promo_command: {e}")
        await message.answer("Sorry, something went wrong. Please try again later.")
