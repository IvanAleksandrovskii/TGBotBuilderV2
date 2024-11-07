# handlers/ai_chat_with_memory.py

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import List, Dict

from core import log
from core.models import db_helper
from services.ai_services import get_ai_response
from services.text_service import TextService
from handlers.utils import send_or_edit_message


router = Router()


class AIChatMemoryStates(StatesGroup):
    CHATTING_WITH_MEMORY = State()


class ChatHistoryMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


async def get_conversation_history(state: FSMContext) -> List[ChatHistoryMessage]:
    """Получение истории чата из состояния"""
    data = await state.get_data()
    messages: List[Dict] = data.get("chat_history", [])
    return [ChatHistoryMessage(**msg) for msg in messages]


async def update_chat_history(state: FSMContext, role: str, content: str):
    """Добавление сообщения в историю с сохранением последних 5"""
    data = await state.get_data()
    messages: List[Dict] = data.get("chat_history", [])
    
    # Добавляем новое сообщение
    messages.append({
        "role": role,
        "content": content
    })
    
    # Оставляем только последние 5 сообщений
    messages = messages[-5:]
    
    # Обновляем состояние
    await state.update_data(chat_history=messages)


@router.callback_query(lambda c: c.data == "ai_chat_with_memory")
async def start_ai_chat_with_memory(callback_query: types.CallbackQuery, state: FSMContext):
    text_service = TextService()
    
    async for session in db_helper.session_getter():
        try:
            # Очищаем историю сообщений при старте нового чата
            await state.set_data({"chat_history": []})
            
            content = await text_service.get_text_with_media("ai_chat_with_memory", session)
            text = content["text"] if content else "Welcome to AI Chat with Memory! Send me a message and I'll respond."
            media_url = content["media_urls"][0] if content and content["media_urls"] else None
            
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="End Memory Chat", callback_data="back_to_start")]
            ])
            
            await send_or_edit_message(callback_query.message, text, keyboard, media_url)
            await state.set_state(AIChatMemoryStates.CHATTING_WITH_MEMORY)
            
        except Exception as e:
            log.error(f"Error in start_ai_chat_with_memory: {e}")
        finally:
            await session.close()


@router.message(AIChatMemoryStates.CHATTING_WITH_MEMORY)
async def handle_memory_chat(message: types.Message, state: FSMContext):
    user_message = message.text
    
    # Добавляем сообщение пользователя в историю
    await update_chat_history(state, "user", user_message)
    
    # Получаем историю чата
    chat_history = await get_conversation_history(state)
    
    async for session in db_helper.session_getter():
        try:
            # Формируем контекст из истории
            context = "\n".join([
                f"{'Assistant' if msg.role == 'assistant' else 'User'}: {msg.content}"
                for msg in chat_history
            ])
            
            # Получаем ответ от AI с учетом контекста
            result = await get_ai_response(
                session, 
                f"Previous conversation:\n{context}\n\nUser: {user_message}"
            )
            
            if result and result.content:
                ai_response = result.content
                # Добавляем ответ AI в историю
                await update_chat_history(state, "assistant", ai_response)
            else:
                ai_response = "Sorry, I couldn't generate a response. Please try again."
            
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="End Memory Chat", callback_data="back_to_start")]
            ])
            
            await message.reply(ai_response, reply_markup=keyboard)
            
        except Exception as e:
            log.error(f"Error in handle_memory_chat: {e}")
            await message.reply("An error occurred. Please try again.")
        finally:
            await session.close()
