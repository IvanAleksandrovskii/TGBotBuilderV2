# handlers/ai_test_result_transcription.py

from typing import List

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core import log
from core.models import db_helper, SentTest  # , User, PsycoTestsAITranscription, Test
from core.models.sent_test import TestStatus
from services.ai_services import get_ai_response
from services.text_service import TextService
from handlers.utils import send_or_edit_message


router = Router()

# TODO: Rework sending message to follow my concept
# TODO: Fix to include only psychological tests' results

class AIChatStates(StatesGroup):
    CHATTING = State()
    VIEWING_USERS = State()
    VIEWING_TESTS = State()


@router.callback_query(lambda c: c.data == "view_sent_psyco_tests")
async def view_sent_psyco_tests(callback_query: types.CallbackQuery, state: FSMContext):
    sender_id = callback_query.from_user.id
    page = 1
    await state.update_data(current_page=page)
    await show_sent_tests_users_page(callback_query.message, sender_id, page, state)


async def show_sent_tests_users_page(message: types.Message, sender_id: int, page: int, state: FSMContext):
    async for session in db_helper.session_getter():
        try:
            subquery = (
                select(SentTest.receiver_username, func.max(SentTest.created_at).label("last_sent"))
                .where(SentTest.sender_id == sender_id)
                .group_by(SentTest.receiver_username)
                .subquery()
            )

            query = (
                select(subquery.c.receiver_username)
                .select_from(subquery)
                .order_by(subquery.c.last_sent.desc())
                .offset((page - 1) * 20)
                .limit(20)
            )

            result = await session.execute(query)
            users = result.scalars().all()

            total_users_query = (
                select(func.count(func.distinct(SentTest.receiver_username)))
                .where(SentTest.sender_id == sender_id)
            )
            total_users_result = await session.execute(total_users_query)
            total_users = total_users_result.scalar()

            total_pages = (total_users - 1) // 20 + 1

            keyboard = []
            for i in range(0, len(users), 2):
                row = []
                for user in users[i:i+2]:
                    row.append(types.InlineKeyboardButton(text=user, callback_data=f"view_user_psyco_tests_{user}"))
                keyboard.append(row)

            navigation = []
            if page > 1:
                navigation.append(types.InlineKeyboardButton(text="◀️", callback_data="prev_page"))
            navigation.append(types.InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="current_page"))
            if page < total_pages:
                navigation.append(types.InlineKeyboardButton(text="▶️", callback_data="next_page"))
            if navigation:
                keyboard.append(navigation)

            keyboard.append([types.InlineKeyboardButton(text="Back to Main Menu", callback_data="back_to_start")])  # TODO: Move text to config

            text_service = TextService()
            content = await text_service.get_text_with_media("view_sent_psyco_tests", session)
            text = content["text"] if content else "Select a user to view sent psychological tests:"  # TODO: Move text to config
            media_url = content["media_urls"][0] if content and content["media_urls"] else None

            await send_or_edit_message(message, text, types.InlineKeyboardMarkup(inline_keyboard=keyboard), media_url)
            await state.set_state(AIChatStates.VIEWING_USERS)

        except Exception as e:
            log.exception(e)
            await message.answer("An error occurred while loading the user list. Please try again.")
        finally:
            await session.close()


@router.callback_query(AIChatStates.VIEWING_USERS)
async def process_users_navigation(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data
    data = await state.get_data()
    current_page = data.get('current_page', 1)

    if action == "prev_page":
        current_page = max(1, current_page - 1)
    elif action == "next_page":
        current_page += 1
    elif action == "current_page":
        await callback_query.answer("Current page number")
        return
    # elif action == "back_to_start":
    #     return
    elif action.startswith("view_user_psyco_tests_"):
        # username = action.split("_")[-1]
        parts = action.split("_")
        username = "_".join(parts[4:]) 
        
        await view_user_psyco_tests(callback_query, username, state)
        return

    await state.update_data(current_page=current_page)
    await show_sent_tests_users_page(callback_query.message, callback_query.from_user.id, current_page, state)


async def view_user_psyco_tests(callback_query: types.CallbackQuery, username: str, state: FSMContext):
    sender_id = callback_query.from_user.id
    async for session in db_helper.session_getter():
        try:
            tests = await session.execute(
                select(SentTest)
                .where(SentTest.sender_id == sender_id, 
                       SentTest.receiver_username == username,
                       SentTest.status == TestStatus.COMPLETED)
                .order_by(SentTest.completed_at.desc())
            )
            tests = tests.scalars().all()

            if not tests:
                await callback_query.answer("Этот пользователь пока не прошел тесты.")  # TODO: Move text to config
                return

            keyboard = [
                [types.InlineKeyboardButton(text="Get AI Transcription", callback_data=f"get_ai_transcription_{username}")]  # TODO: Move text to config
            ]
            keyboard.append([types.InlineKeyboardButton(text="Back to Users List", callback_data="view_sent_psyco_tests")])

            text = f"Completed psychological tests for {username}:\n\n"
            for test in tests:
                text += f"• {test.test_name} (Score: {test.result_score})\n"

            # media_url = TextService().get_default_media(session)
            content = await TextService().get_text_with_media("view_sent_psyco_tests", session)
            media_url = content["media_urls"][0] if content and content["media_urls"] else None
            
            # await callback_query.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard))
            await send_or_edit_message(callback_query.message, text, types.InlineKeyboardMarkup(inline_keyboard=keyboard), media_url)
            
            await state.set_state(AIChatStates.VIEWING_TESTS)

        except Exception as e:
            log.exception(e)
            await callback_query.answer("An error occurred while loading tests. Please try again.")
        finally:
            await session.close()


@router.callback_query(lambda c: c.data.startswith("get_ai_transcription_"))
async def get_ai_transcription(callback_query: types.CallbackQuery, state: FSMContext):
    parts = callback_query.data.split("_")
    username = "_".join(parts[3:])
    
    sender_id = callback_query.from_user.id
    
    async for session in db_helper.session_getter():
        try:
            tests = await session.execute(
                select(SentTest)
                .where(SentTest.sender_id == sender_id, 
                       SentTest.receiver_username == username,
                       SentTest.status == TestStatus.COMPLETED)
                .order_by(SentTest.completed_at.desc())
            )
            tests = tests.scalars().all()

            if not tests:
                await callback_query.answer("Пользователь не прошол писхологические тесты.")
                return

            # Check if transcription already exists
            # existing_transcription = await session.execute(
            #     select(PsycoTestsAITranscription)
            #     .where(PsycoTestsAITranscription.sender_chat_id == sender_id,
            #            PsycoTestsAITranscription.reciver_chat_id == tests[0].receiver_id)
            # )
            # existing_transcription = existing_transcription.scalar_one_or_none()

            # if existing_transcription:
            #     transcription = existing_transcription.transcription
            # else:
            
            # Generate new transcription
            transcription = await get_ai_psychological_transcrpit(session, tests)
                
                # Save new transcription
                # new_transcription = PsycoTestsAITranscription(
                #     sender_chat_id=sender_id,
                #     reciver_chat_id=tests[0].receiver_id,
                #     tests="-&-".join([test.test_name for test in tests]),
                #     transcription=transcription
                # )
                # session.add(new_transcription)
                # await session.commit()
                
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    # [types.InlineKeyboardButton(text="Back", callback_data=f"view_sent_psyco_tests")]
                    [types.InlineKeyboardButton(text="Back", callback_data=f"user_tests_page_1_{username}")]
                ])
            
            await send_or_edit_message(callback_query.message, f"AI Transcription for @{username}:\n\n{transcription}", keyboard, None)  # TODO: Move to config

        except Exception as e:
            log.exception(e)
            await callback_query.answer("An error occurred while generating the AI transcription. Please try again.")
        finally:
            await session.close()


prompt_psyco = """Я провожу кинологические психологические тесты для собак, где сами их хозяева проходят за них тесты, 
отвечая на поведенческие вопросы за своих питомцев, главная задача определить подходит ли их собака для работы или 
нет и стоит ли брать ее в рабочий коллектив или это может повредить другим собакам или самой собаке. Какие рекомендации мы можем дать хозяину, чтобы поддерживать мотивацию собаки, быстро адаптировать ее в коллектив.
Чтобы не рушить атмосферу "психологии переноса", отвечай не используя слов собака или что либо другое относящееся к теме животных, 
говори о личности, собаки очень похожи на людей, говори именно не обо мне, а о личности, о результатах которой идет речь. 
Подведи короткое и емкое итого просуммировав результат тестов и сделав общий вывод о необходимости данной личности на работе или нет, 
о рисках работы, которые это за собой влечет для остального коллектива, далее результаты тестов:"""


# TODO: Move this function to a services file
async def get_ai_psychological_transcrpit(session: AsyncSession, tests_results: List[SentTest]) -> str:
    message = prompt_psyco.replace("\n", "")
    for test_result in tests_results:
        message += f"\n\n{test_result.result_text}"
    
    ai_response = await get_ai_response(session, message)
    
    if ai_response.ai_model is None:
        log.error("AI models are not responding")
        return "An error occurred while getting a response from AI, please try again later."
    
    return ai_response.content
