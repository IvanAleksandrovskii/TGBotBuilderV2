# handlers/ai_chat.py

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core import log
from core.models import db_helper
from services.ai_services import get_ai_response
from services.text_service import TextService
from handlers.utils import send_or_edit_message


router = Router()


class AIChatStates(StatesGroup):
    CHATTING = State()


# TODO: Rework sending message to follow my concept, move texts to config  (( maybe or maybe not ))

@router.callback_query(lambda c: c.data == "ai_chat")
async def start_ai_chat(callback_query: types.CallbackQuery, state: FSMContext):
    text_service = TextService()
    async for session in db_helper.session_getter():
        try:
            content = await text_service.get_text_with_media("ai_chat", session)
            text = content["text"] if content else "Welcome to AI Chat! Send me a message and I'll respond."
            media_url = content["media_urls"][0] if content and content["media_urls"] else None

            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="End Chat", callback_data="back_to_start")]
            ])

            await send_or_edit_message(callback_query.message, text, keyboard, media_url)
            await state.set_state(AIChatStates.CHATTING)
        except Exception as e:
            log.error(f"Error in start_ai_chat: {e}")
        finally:
            await session.close()


@router.message(AIChatStates.CHATTING)
async def handle_message(message: types.Message, state: FSMContext):
    user_message = message.text
    async for session in db_helper.session_getter():
        try:
            result = await get_ai_response(session, user_message)
            if result and result.content:
                ai_response = result.content
            else:
                ai_response = "Sorry, I couldn't generate a response. Please try again."

            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="End Chat", callback_data="back_to_start")]
            ])

            await message.reply(ai_response, reply_markup=keyboard)
        except Exception as e:
            log.error(f"Error in handle_message: {e}")
            await message.reply("An error occurred. Please try again.")
        finally:
            await session.close()
