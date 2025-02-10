# handlers/ai_chat_with_memory.py

from typing import List, Dict

from aiogram import Router, types, F
from aiogram.utils.chat_action import ChatActionSender
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ChatAction

from core import log, settings
from core.models import db_helper
from services.ai_services import get_ai_response
from services.text_service import TextService
from handlers.utils import send_or_edit_message

from services.decorators import handle_as_task, TaskPriority


router = Router()


class AIChatMemoryStates(StatesGroup):
    CHATTING_WITH_MEMORY = State()


class ChatHistoryMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


async def get_conversation_history(state: FSMContext) -> List[ChatHistoryMessage]:
    """Get conversation history from the chat state data"""
    data = await state.get_data()
    messages: List[Dict] = data.get("chat_history", [])
    return [ChatHistoryMessage(**msg) for msg in messages]


async def update_chat_history(state: FSMContext, role: str, content: str):
    """Add a message to the conversation history and keep the last {history_length} messages"""
    data = await state.get_data()
    messages: List[Dict] = data.get("chat_history", [])
    
    # Add new message
    messages.append({
        "role": role,
        "content": content
    })
    
    # Leave only the last {history_length} messages
    history_length = settings.ai_chat.history_length
    
    messages = messages[-history_length:]
    
    # Update the state
    await state.update_data(chat_history=messages)


@router.callback_query(F.data == "ai_chat_with_memory")
@handle_as_task(priority=TaskPriority.NORMAL)
async def start_ai_chat_with_memory(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    
    text_service = TextService()
    async for session in db_helper.session_getter():
        try:
            # Clear the chat history when starting a new chat
            await state.set_data({"chat_history": []})
            
            content = await text_service.get_text_with_media("ai_chat_with_memory", session)
            text = content["text"] if content else "Добро пожаловать! Как я могу вам сегодня помочь?"  # TODO: Move to config
            media_url = content["media_urls"][0] if content and content["media_urls"] else None
            
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="Завершить чат", callback_data="back_to_start")]  # TODO: Move to config
            ])  
            await send_or_edit_message(callback_query.message, text, keyboard, media_url)
            await state.set_state(AIChatMemoryStates.CHATTING_WITH_MEMORY)
            
        except Exception as e:
            log.error(f"Error in start_ai_chat_with_memory: {e}")
        finally:
            await session.close()


@router.message(AIChatMemoryStates.CHATTING_WITH_MEMORY)
@handle_as_task(priority=TaskPriority.NORMAL)
async def handle_memory_chat(message: types.Message, state: FSMContext):
    
    # await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    sender = ChatActionSender(
        bot=message.bot,
        chat_id=message.chat.id,
        action=ChatAction.TYPING
    )
    async with sender:
        
        user_message = message.text
        
        # Add the user's message to the conversation history
        await update_chat_history(state, "user", user_message)
        
        # Get the chat history
        chat_history = await get_conversation_history(state)
        
        async for session in db_helper.session_getter():
            try:
                # Make the context from the chat history
                context = "\n".join([
                    f"{'Assistant' if msg.role == 'assistant' else 'User'}: {msg.content}"
                    for msg in chat_history
                ])
                
                # Get the AI response with the context
                result = await get_ai_response(
                    session, 
                    f"Previous conversation:\n{context}\n\nUser: {user_message}"
                )
                
                if result and result.content:
                    ai_response = result.content
                    # Add the AI response to the chat history
                    await update_chat_history(state, "assistant", ai_response)
                else:
                    ai_response = "Извините, я не могу ответить сейчас. Пожалуйста, попробуйте еще раз позже."
                
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text="Завершить чат", callback_data="back_to_start")]  # TODO: Move to config
                ])
                
                await message.reply(ai_response, reply_markup=keyboard)
                
            except Exception as e:
                log.error(f"Error in handle_memory_chat: {e}")
                await message.reply("An error occurred. Please try again.")
            finally:
                await session.close()
