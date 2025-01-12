# handlers/universal_page.py

from aiogram import Router, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core import log, settings
from core.models import db_helper
from .utils import send_or_edit_message, get_content
from .on_start import get_start_content


router = Router()


class UniversalPageStates(StatesGroup):
    VIEWING_UNIVERSAL_PAGE = State()

@router.callback_query(lambda c: c.data and c.data.startswith("show_page_"))
async def show_universal_page(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()

    await state.clear()  # Clear the state before showing a new page
    
    context_marker = callback_query.data.split("_", 2)[2]
    
    log.info("Showing universal page for context_marker: %s", context_marker)
    
    async for session in db_helper.session_getter():
        try:
            text, keyboard, media_url = await get_content(context_marker, session)
            
            await state.set_state(UniversalPageStates.VIEWING_UNIVERSAL_PAGE)
            await state.update_data(current_page=context_marker)
            
            await send_or_edit_message(callback_query, text, keyboard, media_url)
        except Exception as e:
            log.error(f"Error in show_universal_page: {e}")
            await callback_query.answer(settings.universal_page_text.universal_page_error)
            await state.clear()
        finally:
            await session.close()


@router.callback_query(UniversalPageStates.VIEWING_UNIVERSAL_PAGE)
async def process_page_action(callback_query: types.CallbackQuery, state: FSMContext, bot: Bot):
    await callback_query.answer()
    
    action = callback_query.data
    log.info("Processing page action: %s", action)

    current_state = await state.get_state()
    if current_state != UniversalPageStates.VIEWING_UNIVERSAL_PAGE:
        log.warning("Unexpected state: %s for action: %s", current_state, action)
        await callback_query.answer(settings.universal_page_text.universal_page_try_again)
        await state.clear()
        return
    
    if action.startswith("show_page_"):
        await show_universal_page(callback_query, state)
    elif action == "back_to_start":
        await state.clear()
        chat_id = callback_query.from_user.id
        username = callback_query.from_user.username
        text, keyboard, media_url = await get_start_content(chat_id, username)
        await send_or_edit_message(callback_query, text, keyboard, media_url)
    
    elif action == "show_quizzes":
        await state.clear()
        from .quiz import show_quizzes
        await show_quizzes(callback_query, state)
    
    elif action == "show_psyco_tests":
        await state.clear()
        from .quiz import show_psycho_tests
        await show_psycho_tests(callback_query, state)

    elif action.startswith("start_quiz_"):
        await state.clear()
        from .quiz import start_quiz
        await start_quiz(callback_query, state)
    
    elif action.startswith("read_"):
        from .reader import start_reading
        await state.clear()
        await start_reading(callback_query, state)
    
    elif action == "ai_chat":
        from .ai_chat import start_ai_chat
        await state.clear()
        await start_ai_chat(callback_query, state)
    
    elif action == "ai_chat_with_memory":
        from .ai_chat_with_memory import start_ai_chat_with_memory
        await state.clear()
        await start_ai_chat_with_memory(callback_query, state)
        
    elif action == "dice":
        from .dice import dice
        await state.clear()
        await dice(callback_query, bot)
        
    elif action == "getpromo":
        from .promocode import get_promo_command
        await state.clear()
        await get_promo_command(callback_query)
