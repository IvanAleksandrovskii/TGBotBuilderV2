# handlers/promocode.py

# import os

from aiogram import Router, types, Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import func, select
# from aiogram.types import FSInputFile
# from aiogram.types import InputMediaPhoto

from core import log, settings
from core.models import db_helper
from core.models.promocode import PromoRegistration
from services import UserService
from services.promocode_service import PromoCodeService

from ..utils import send_or_edit_message, get_content


router = Router()


# TODO: Move all texts to config file
@router.callback_query(lambda c: c.data == "getpromo")
async def get_promo_command(callback_query: types.CallbackQuery):
    """Handler for /getpromo command that generates a promocode for the user"""
    
    await callback_query.answer()
    
    try:
        chat_id = callback_query.from_user.id
        
        # Get user from database
        user = await UserService().get_user(chat_id)
        if not user:
            await callback_query.answer("You need to start the bot first with /start")
            return

        # Generate promocode
        promocode = await PromoCodeService.create_promocode(user.id)

        bot_username = (await callback_query.bot.get_me()).username
        invite_link = f"https://t.me/{bot_username}?start={promocode.code}"
        
        # from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        # btn = InlineKeyboardButton(
        #         text="main manu",
        #         url=None,
        #         callback_data="back_to_start"
        #     )
        
        # keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn]])
        
        # # TODO: NEW, remove and make the normal one with default media and media and text by marker
        
        # user_photos = await bot.get_user_profile_photos(user.chat_id)
        
        # # Create directory if it doesn't exist
        # os.makedirs("media/users", exist_ok=True)

        # # Check if user has any photos
        # if user_photos.total_count > 0:
        #     try:
        #         # Get the file path of the photo
        #         file = await bot.get_file(user_photos.photos[0][-1].file_id)
        #         # Download the photo
        #         photo_path = f"media/users/{chat_id}_photo.jpg"
        #         await bot.download_file(file.file_path, photo_path)
                
        #         # Create FSInputFile for the photo
        #         input_file = FSInputFile(photo_path)
                
        #         # Create InputMediaPhoto for editing
        #         media = InputMediaPhoto(
        #             media=input_file,
        #             caption=f"Here's your unique invite link:\n{invite_link}\n\n"
        #                    f"Share it with friends! We'll track how many people join using your link."
        #         )
        
        try:
            async with db_helper.db_session() as session:
                text, keyboard, media = await get_content("getpromo", session)
                
                is_default_text = text == settings.bot_main_page_text.utils_handler_content_not_found

                
                if is_default_text:
                    final_text = (
                        "Ваша ссылка для приглашения:\n\n"
                        f"{invite_link}\n\n"
                        "Поделитесь ею с друзьями!\n\n"
                    )
                else:
                    final_text = f"{text}\n\n{invite_link}\n\n"
                
                result = await session.execute(
                    select(func.count()).select_from(PromoRegistration).where(PromoRegistration.promocode_id == promocode.id)
                )
                user_count = result.scalar_one()
                
                final_text += f"Пользователей присодинилось по ссылке: {user_count}"
                
                btn = InlineKeyboardButton(
                    text="Главное меню",
                    url=None,
                    callback_data="back_to_start"
                )
                
                if keyboard:
                    keyboard.inline_keyboard.append([btn])
                else:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[[btn]])
                    
                await send_or_edit_message(callback_query, final_text, keyboard, media)
        
        except Exception as e:
            log.exception(f"Error in get_promo_command: {e}")
            await callback_query.answer("Sorry, something went wrong. Please try again later.")
            
    #             # Edit existing message with new photo and text
    #             await message.message.edit_media(
    #                 media=media,
    #                 reply_markup=keyboard
    #             )
                
    #             # Clean up the temporary file
    #             # if os.path.exists(photo_path):
    #             #     os.remove(photo_path)
                    
    #         except Exception as photo_error:
    #             # log.exception(f"Error processing photo: {photo_error}")
    #             # If photo processing fails, send message without photo
    #             await send_or_edit_message(
    #                 message,
    #                 f"Here's your unique invite link:\n{invite_link}\n\n"
    #                 f"Share it with friends! We'll track how many people join using your link.",
    #                 keyboard,
    #                 None
    #             )
    #     else:
    #         await send_or_edit_message(
    #             message,
    #             f"Here's your unique invite link:\n{invite_link}\n\n"
    #             f"Share it with friends! We'll track how many people join using your link.",
    #             keyboard,
    #             None
    #         )
            
    except Exception as e:
        log.exception(f"Error in get_promo_command: {e}")
        await callback_query.answer("Sorry, something went wrong. Please try again later.")
