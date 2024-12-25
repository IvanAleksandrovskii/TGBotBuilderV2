# handlers/ai_test_result_transcription.py

from typing import List

from aiogram import Router, types
from aiogram.enums import ChatAction

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core import log
from core.models import db_helper, SentTest
from core.models.psycho_tests_ai_trascription import PsycoTestsAITranscription
from core.models.sent_test import TestStatus
from services.ai_services import get_ai_response
from handlers.utils import send_or_edit_message


router = Router()


@router.callback_query(lambda c: c.data.startswith("get_ai_transcription_"))
async def get_ai_transcription(callback_query: types.CallbackQuery):
    parts = callback_query.data.split("_")
    username = "_".join(parts[3:])
    
    sender_id = callback_query.from_user.id
        
    await callback_query.bot.send_chat_action(callback_query.message.chat.id, ChatAction.TYPING)
        
    async with db_helper.db_session() as session:
        try:
            # Subquery to get the latest completed_at for each test_id
            latest_test_subquery = (
                select(
                    SentTest.test_id, 
                    func.max(SentTest.completed_at).label('latest_completed_at')
                )
                .where(
                    SentTest.sender_id == sender_id, 
                    SentTest.receiver_username == username,
                    SentTest.status == TestStatus.COMPLETED
                )
                .group_by(SentTest.test_id)
                .subquery()
            )

            # Main query to get the latest test for each test_id
            tests = await session.execute(
                select(SentTest)
                .join(
                    latest_test_subquery, 
                    (SentTest.test_id == latest_test_subquery.c.test_id) & 
                    (SentTest.completed_at == latest_test_subquery.c.latest_completed_at)
                )
                .where(
                    SentTest.sender_id == sender_id, 
                    SentTest.receiver_username == username,
                    SentTest.status == TestStatus.COMPLETED
                )
                .order_by(SentTest.completed_at.desc())
            )
            tests = tests.scalars().all()

            if not tests:
                await callback_query.answer("Пользователь еще не прошел писхологические тесты.")  # TODO: Move to config
                return

            # Check if transcription already exists
            tests_ids = "&".join([str(test.id) for test in tests])
            
            existing_transcription = await session.execute(
                select(PsycoTestsAITranscription)
                .where(PsycoTestsAITranscription.sender_chat_id == sender_id,
                       PsycoTestsAITranscription.reciver_chat_id == tests[0].receiver_id)
                .order_by(PsycoTestsAITranscription.created_at.desc())
                .limit(1)
            )
            existing_transcription = existing_transcription.scalar_one_or_none()
            
            if existing_transcription and existing_transcription.tests_ids == tests_ids:
                # Transcription already exists
                transcription = existing_transcription.transcription
                log.info(f"Transcription already exists for {tests_ids}, text: {transcription}")
                
            else:
                # Generate new transcription
                transcription = await get_ai_psychological_transcrpit(session, tests)
                log.info(f"New transcription generated for {tests_ids}, text: {transcription}")
                
                if transcription is not None:
                    # Save new transcription
                    new_transcription = PsycoTestsAITranscription(
                        sender_chat_id=sender_id,
                        reciver_chat_id=tests[0].receiver_id,
                        tests_ids=tests_ids,
                        transcription=transcription
                    )
                    session.add(new_transcription)
                    await session.commit()
                
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    # [types.InlineKeyboardButton(text="Back", callback_data=f"view_sent_psyco_tests")]
                    [types.InlineKeyboardButton(text="Back", callback_data=f"user_tests_page_1_{username}")]
                ])
            
            if transcription is None:
                keyboard.inline_keyboard.insert(0, [types.InlineKeyboardButton(text="Попробовать еще раз", callback_data=f"get_ai_transcription_{username}")])
                await send_or_edit_message(callback_query.message, "Не удалось получить ответ от ИИ. Пожалуйста, попробуйте позже.", keyboard, None)  # TODO: Move to config 
                return
            
            await send_or_edit_message(callback_query.message, f"ИИ расшифровка для пользователя @{username}:\n\n{transcription}", keyboard, None)  # TODO: Move to config

        except Exception as e:
            log.exception(e)
            await callback_query.answer("An error occurred while generating the AI transcription. Please try again.")
        finally:
            await session.close()


prompt_psyco = """Отвечай по-русски. Я провожу кинологические психологические тесты для собак, где сами их хозяева проходят за них тесты, 
отвечая на поведенческие вопросы за своих питомцев, главная задача определить подходит ли их собака для работы или 
нет и стоит ли брать ее в рабочий коллектив или это может повредить другим собакам или самой собаке. Какие рекомендации мы можем дать хозяину, 
чтобы поддерживать мотивацию собаки, быстро адаптировать ее в коллектив.
Чтобы не рушить атмосферу "психологии переноса", отвечай не используя слов собака или что либо другое относящееся к теме животных, 
говори о личности, собаки очень похожи на людей, говори именно не обо мне, а о личности, о результатах которой идет речь. Нельзя использовать
слова хозин/питомец или другие связанные с этим слова, можно говорить тольок работодатель и сотрудник.
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
        return None
    
    return ai_response.content
