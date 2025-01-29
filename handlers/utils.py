# handlers/utils.py

from aiogram import types
from aiogram.exceptions import TelegramBadRequest

from aiogram.types import InputMediaAnimation, InputMediaPhoto, InputMediaVideo
from async_lru import alru_cache
from sqlalchemy.ext.asyncio import AsyncSession

from core import log, settings

from core.models import db_helper
from services.button_service import ButtonService
from services.text_service import TextService


async def send_or_edit_message(message: types.Message | types.CallbackQuery, text: str, keyboard=None, media_url: str = None):
    log.info(f"text: {text} \n keyboard: {keyboard} \n media_url: {media_url}")
    try:
        if isinstance(message, types.CallbackQuery):
            message = message.message

        if media_url:
            try:
                if message.photo or message.video or message.animation:
                    media = get_input_media(media_url, text)
                    await message.edit_media(media=media, reply_markup=keyboard)
                else:
                    await message.answer_photo(photo=media_url, caption=text, reply_markup=keyboard)
            except TelegramBadRequest as e:
                if "message is not modified" in str(e).lower():
                    log.debug("Message was not modified as the content didn't change")
                else:
                    log.error(f"Error editing message with media: {e}")
                    await message.answer(text=text, reply_markup=keyboard)
            except Exception as e:
                log.error(f"Error sending media: {e}")
                await message.answer(text=text, reply_markup=keyboard)
        else:
            try:
                await message.edit_text(text=text, reply_markup=keyboard)
            except TelegramBadRequest as e:
                if "message is not modified" in str(e).lower():
                    log.debug("Message was not modified as the content didn't change")
                else:
                    log.error(f"Error editing message: {e}")
                    await message.answer(text=text, reply_markup=keyboard)
            except Exception as e:
                log.error(f"Error in send_or_edit_message: {e}")
                await message.answer(text=text, reply_markup=keyboard)
    except Exception as e:
        log.error(f"Unexpected error in send_or_edit_message: {e}")
        try:
            await message.answer(settings.bot_main_page_text.utils_error_message)
        except Exception as final_error:
            log.critical(f"Failed to send error message: {final_error}")


def get_input_media(media_url: str, caption: str):
    file_ext = media_url.split('.')[-1].lower()
    if file_ext in ['jpg', 'jpeg', 'png']:
        return InputMediaPhoto(media=media_url, caption=caption)
    elif file_ext == 'gif':
        return InputMediaAnimation(media=media_url, caption=caption)
    else:
        return InputMediaVideo(media=media_url, caption=caption)


async def get_content(context_marker: str, session: AsyncSession):
    text_service = TextService()
    button_service = ButtonService()

    content_data = await text_service.get_text_with_media(context_marker, session)
    if not content_data:
        log.warning(f"Content not found for marker: {context_marker}")
        content_data = {
            "text": settings.bot_main_page_text.utils_handler_content_not_found,
            "media_urls": []
        }

    keyboard = await button_service.create_inline_keyboard(context_marker, session)

    media_url = content_data["media_urls"][0] if content_data["media_urls"] else None
    if not media_url:
        media_url = await text_service.get_default_media(session)

    return content_data["text"], keyboard, media_url


@alru_cache(maxsize=1, ttl=60)
async def get_default_media() -> str:
    text_service = TextService()
    async with db_helper.db_session() as session:
        try:
            default_media = await text_service.get_default_media(session)
        except Exception as e:
            log.exception(f"Error in getting default media: {e}")
            default_media = None
    return default_media
