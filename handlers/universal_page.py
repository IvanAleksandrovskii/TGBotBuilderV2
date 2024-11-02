# handlers/universal_page.py

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core import log, settings
from core.models import db_helper
from services.button_service import ButtonService
from .utils import send_or_edit_message, get_content
from .on_start import get_start_content
# from .quiz_handler import show_quizzes, start_quiz
# from .large_text_handler import start_reading


router = Router()


class UniversalPageStates(StatesGroup):
    VIEWING_UNIVERSAL_PAGE = State()

@router.callback_query(lambda c: c.data and c.data.startswith("show_page_"))
async def show_universal_page(callback_query: types.CallbackQuery, state: FSMContext):

    await state.clear()  # Clear the state before showing a new page
    
    context_marker = callback_query.data.split("_", 2)[2]
    
    log.info("Showing universal page for context_marker: %s", context_marker)
    
    async for session in db_helper.session_getter():
        try:
            text, entities, keyboard, media_url = await get_content(context_marker, session)
            
            await state.set_state(UniversalPageStates.VIEWING_UNIVERSAL_PAGE)
            await state.update_data(current_page=context_marker)
            
            await send_or_edit_message(callback_query, text, entities, keyboard, media_url)
        except Exception as e:
            log.error(f"Error in show_universal_page: {e}")
            await callback_query.answer(settings.bot_text.universal_page_error)
            await state.clear()
        finally:
            await session.close()

@router.callback_query(UniversalPageStates.VIEWING_UNIVERSAL_PAGE)
async def process_page_action(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data
    log.info("Processing page action: %s", action)

    current_state = await state.get_state()
    if current_state != UniversalPageStates.VIEWING_UNIVERSAL_PAGE:
        log.warning("Unexpected state: %s for action: %s", current_state, action)
        await callback_query.answer(settings.bot_text.universal_page_try_again)
        await state.clear()
        return
    
    if action.startswith("show_page_"):
        await show_universal_page(callback_query, state)
    elif action == "back_to_start":
        await state.clear()
        chat_id = callback_query.from_user.id
        username = callback_query.from_user.username
        text, entities, keyboard, media_url = await get_start_content(chat_id, username)
        await send_or_edit_message(callback_query, text, entities, keyboard, media_url)
    # elif action == "show_quizzes": 
    #     await state.clear()
    #     await show_quizzes(callback_query, state)
    # elif action == "show_psyco_tests":
    #     await state.clear()
    #     from .quiz_handler import show_psyco_tests
    #     await show_psyco_tests(callback_query, state)
    # elif action.startswith("start_quiz_"):
    #     await state.clear()
    #     await start_quiz(callback_query, state)
    # elif action.startswith("read_"):
    #     await state.clear()
    #     await start_reading(callback_query, state)

    # elif action.startswith("view_received_tests"):
    #     from .send_test import view_received_tests
    #     await state.clear()
    #     await view_received_tests(callback_query, state)

    # elif action == "send_test":
    #     from .send_test import start_send_test
    #     await state.clear()
    #     await start_send_test(callback_query, state)

    else:
        # Process other buttons
        data = await state.get_data()
        current_page = data.get('current_page')
        if not current_page:
            log.error(f"Current page not found in state data: {data}")
            await callback_query.answer(settings.bot_text.universal_page_undefined_error)
            return

        async for session in db_helper.session_getter():
            try:
                button_service = ButtonService()
                buttons = await button_service.get_buttons_by_marker(current_page, session)
                button = next((b for b in buttons if b.callback_data == action), None)

                if not button:
                    log.warning(f"Unknown action: {action} for page: {current_page}")
                    await callback_query.answer(settings.bot_text.universal_page_unkown_action)
                    await state.clear()  # Clear the state if action is unknown
                    return

                if button:
                    if button.url:
                        await callback_query.answer(url=button.url)
                    else:
                        # Here you can add extra logic for button actions
                        log.info("Executing action for button: %s", button.text)
                        # await callback_query.answer(f"Выполнено действие: {action}")
                else:
                    log.warning(f"Unknown action: {action} for page: {current_page}")
                    await callback_query.answer(settings.bot_text.universal_page_unkown_action)
            except Exception as e:
                log.error(f"Error in process_page_action: {e}")
                await callback_query.answer(settings.bot_text.universal_page_action_error_try_again)
            finally:
                await session.close()
                await state.clear()
