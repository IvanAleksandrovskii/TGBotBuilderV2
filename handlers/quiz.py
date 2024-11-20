# handlers/quiz_handler.py

from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import func, select
import random
from collections import defaultdict

from core.models import Test, Question, QuizResult, User, Result
from core.models import db_helper
from core import log, settings
from services.text_service import TextService
from services.button_service import ButtonService
from .utils import send_or_edit_message


router = Router()


class QuizStates(StatesGroup):
    VIEWING_TESTS = State()
    CONFIRMING = State()
    VIEWING_INTRO = State()  # New state for showing intro
    ANSWERING = State()
    SHOWING_COMMENT = State()


@router.callback_query(lambda c: c.data == "show_psycho_tests")
async def show_psycho_tests(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()  # Clear the state before showing the list of psycological tests
    async for session in db_helper.session_getter():
        try:

            tests = await session.execute(Test.active().where(Test.is_psycological == True))  # Only psycological tests 
            tests = tests.scalars().all()

            keyboard = []
            for test in tests:
                keyboard.append([types.InlineKeyboardButton(text=test.name, callback_data=f"start_quiz_{test.id}")])

            button_service = ButtonService()
            custom_buttons = await button_service.get_buttons_by_marker("show_psycho_tests", session)
            for button in custom_buttons:
                if button.url:
                    keyboard.append([types.InlineKeyboardButton(text=button.text, url=button.url)])
                elif button.callback_data:
                    keyboard.append([types.InlineKeyboardButton(text=button.text, callback_data=button.callback_data)])

            keyboard.append([types.InlineKeyboardButton(text=settings.quiz_text.quiz_back_to_start, callback_data="back_to_start")])

            reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

            text_service = TextService()
            content = await text_service.get_text_with_media("show_psycho_tests", session)
            text = content["text"] if content else settings.quiz_text.psycological_rests_list_menu
            media_url = content["media_urls"][0] if content and content["media_urls"] else await text_service.get_default_media(session)

            if media_url and not media_url.startswith(('http://', 'https://')):
                media_url = f"{settings.media.base_url}/app/{media_url}"

            await send_or_edit_message(callback_query.message, text, reply_markup, media_url)
            await state.set_state(QuizStates.VIEWING_TESTS)

        except Exception as e:
            log.exception(e)
        finally:
            await session.close()


@router.callback_query(lambda c: c.data == "show_quizzes")
async def show_quizzes(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()  # Clear the state before showing the list of tests
    async for session in db_helper.session_getter():
        try:
            # tests = await session.execute(select(Test).where(Test.is_active == True))  
            tests = await session.execute(Test.active().where(Test.is_psycological == False))  # Only non psycological tests 
            tests = tests.scalars().all()

            keyboard = []
            for test in tests:
                keyboard.append([types.InlineKeyboardButton(text=test.name, callback_data=f"start_quiz_{test.id}")])

            button_service = ButtonService()
            custom_buttons = await button_service.get_buttons_by_marker("show_quizzes", session)
            for button in custom_buttons:
                if button.url:
                    keyboard.append([types.InlineKeyboardButton(text=button.text, url=button.url)])
                elif button.callback_data:
                    keyboard.append([types.InlineKeyboardButton(text=button.text, callback_data=button.callback_data)])

            keyboard.append([types.InlineKeyboardButton(text=settings.quiz_text.quiz_back_to_start, callback_data="back_to_start")])

            reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

            text_service = TextService()
            content = await text_service.get_text_with_media("show_quizzes", session)
            text = content["text"] if content else settings.quiz_text.quizes_list_menu
            media_url = content["media_urls"][0] if content and content["media_urls"] else await text_service.get_default_media(session)

            if media_url and not media_url.startswith(('http://', 'https://')):
                media_url = f"{settings.media.base_url}/app/{media_url}"

            await send_or_edit_message(callback_query.message, text, reply_markup, media_url)
            await state.set_state(QuizStates.VIEWING_TESTS)

        except Exception as e:
            log.exception(e)
        finally:
            await session.close()


@router.callback_query(lambda c: c.data and c.data.startswith("start_quiz_"))
async def start_quiz(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    quiz_id = callback_query.data.split("_")[-1]
    
    async for session in db_helper.session_getter():
        try:
            test = await session.execute(select(Test).where(Test.id == quiz_id))
            test = test.scalar_one_or_none()
            
            if not test:
                await callback_query.answer(settings.quiz_text.quiz_not_found)
                return

            user = await session.execute(select(User).where(User.chat_id == callback_query.from_user.id))
            user = user.scalar_one_or_none()

            if not user:
                await callback_query.answer(settings.quiz_text.user_not_found)
                return

            has_passed_test = False
            if not test.allow_play_again:
                # Check if the user has already played the test
                result_count = await session.execute(
                    select(func.count()).select_from(QuizResult).where(
                        QuizResult.user_id == user.id,
                        QuizResult.test_id == test.id
                    )
                )
                has_passed_test = result_count.scalar() > 0

            if test.is_psycological:
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text=settings.quiz_text.psycological_menu_button_for_end_quiz, callback_data="show_psycho_tests")],
                    [types.InlineKeyboardButton(text=settings.quiz_text.quiz_back_to_start, callback_data="back_to_start")]
                ])
            else:
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text=settings.quiz_text.quiz_list_menu_button_for_end_quiz, callback_data="show_quizzes")],
                    [types.InlineKeyboardButton(text=settings.quiz_text.quiz_back_to_start, callback_data="back_to_start")]
                ])

            if not has_passed_test:
                keyboard.inline_keyboard.insert(0, [types.InlineKeyboardButton(text=settings.quiz_text.quiz_start_approve, callback_data=f"confirm_start_{quiz_id}")])

            text_service = TextService()
            media_url = test.picture if test.picture else await text_service.get_default_media(session)
            if media_url and not media_url.startswith(('http://', 'https://')):
                media_url = f"{settings.media.base_url}/app/{media_url}"

            log.info("Generated media URL: %s", media_url)

            description = f"<b>{test.name}</b>\n\n"
            if has_passed_test:
                description += settings.quiz_text.forbidden_to_play_again_quiz_text

            if not has_passed_test:
                description += test.description.replace('\\n', '\n')
            

            await send_or_edit_message(
                callback_query.message,
                description,
                keyboard,
                media_url
            )

            if not has_passed_test:
                await state.set_state(QuizStates.CONFIRMING)
                await state.update_data(quiz_id=quiz_id)
            else:
                await state.clear()

        except Exception as e:
            log.exception(e)
        finally:
            await session.close()


async def get_sorted_questions(session, test_id):
    """Get questions sorted by order and category."""
    questions = await session.execute(
        Question.active()
        .where(Question.test_id == test_id)
        .order_by(Question.order)
    )
    questions = questions.scalars().all()
    
    # Group questions by order
    questions_by_order = defaultdict(list)
    for question in questions:
        # Создаем копию вопроса с его данными
        question_data = {
            'question': question,
            'intro_text': question.intro_text,
            'comment': question.comment,
            'picture': question.picture,
            'order': question.order
        }
        questions_by_order[question.order].append(question_data)
    
    # Create final sorted list with randomization for same order
    sorted_questions = []
    for order in sorted(questions_by_order.keys()):
        order_questions = questions_by_order[order]
        if len(order_questions) > 1:
            # Randomly shuffle questions with the same order
            random.shuffle(order_questions)
        sorted_questions.extend(order_questions)
    
    return sorted_questions


@router.callback_query(QuizStates.VIEWING_INTRO)
async def process_intro(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "show_question":
        data = await state.get_data()
        data['intro_shown'] = True
        await state.update_data(data)
        await send_question(callback_query.message, state)


@router.callback_query(lambda c: c.data and c.data.startswith("confirm_start_"))
async def confirm_start_quiz(callback_query: types.CallbackQuery, state: FSMContext):
    quiz_id = callback_query.data.split("_")[-1]
    async for session in db_helper.session_getter():
        try:
            # Получаем и сохраняем порядок вопросов при старте
            sorted_questions = await get_sorted_questions(session, quiz_id)
            await state.update_data(
                quiz_id=quiz_id, 
                current_question=0, 
                answers=[], 
                category_scores={}, 
                intro_shown=False,
                sorted_questions=sorted_questions  # сохраняем порядок
            )
            await send_question(callback_query.message, state)
        except Exception as e:
            log.exception(e)
        finally:
            await session.close()


@router.callback_query(lambda c: c.data and c.data.startswith("start_questions_"))
async def start_questions(message: types.Message, state: FSMContext, quiz_id: str = None):
    if not quiz_id:  # If called from callback
        quiz_id = message.data.split("_")[-1]
    await send_question(message if isinstance(message, types.Message) else message.message, state)


async def send_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    quiz_id = data['quiz_id']
    current_question = data['current_question']
    sorted_questions = data['sorted_questions']

    async for session in db_helper.session_getter():
        try:
            test = await session.execute(select(Test).where(Test.id == quiz_id))
            test = test.scalar_one_or_none()

            if current_question >= len(sorted_questions):
                await finish_quiz(message, state)
                return

            question_data = sorted_questions[current_question]
            question = question_data['question']  # Получаем сам объект вопроса

            # Проверяем наличие интро текста для текущего вопроса
            if question_data['intro_text'] and not data.get('intro_shown'):
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text=settings.quiz_text.quiz_continue_button, callback_data="show_question")]
                ])
                
                text_service = TextService()
                # Изменяем приоритет медиа
                if question_data['picture']:
                    media_url = question_data['picture']
                elif test.picture:
                    media_url = test.picture
                else:
                    media_url = await text_service.get_default_media(session)
                
                if media_url and not media_url.startswith(('http://', 'https://')):
                    media_url = f"{settings.media.base_url}/app/{media_url}"
                
                intro_text = question_data['intro_text'].replace('\\n', '\n')
                
                await send_or_edit_message(
                    message,
                    intro_text,
                    keyboard,
                    media_url
                )
                
                data['intro_shown'] = True
                await state.update_data(data)
                await state.set_state(QuizStates.VIEWING_INTRO)
                return

            # Если нет интро или оно уже показано, показываем вопрос
            keyboard = []
            for i in range(1, 7):
                answer_text = getattr(question, f'answer{i}_text')  # Используем объект вопроса для получения ответов
                if answer_text:
                    keyboard.append([types.InlineKeyboardButton(
                        text=answer_text,
                        callback_data=f"answer_{current_question}_{i}"
                    )])

            if test.allow_back and current_question > 0:
                keyboard.append([types.InlineKeyboardButton(text=settings.quiz_text.quiz_question_previous_button, callback_data="quiz_back")])

            reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

            text_service = TextService()
            
            if question_data['picture']:
                media_url = question_data['picture']
            elif test.picture:
                media_url = test.picture
            else:
                media_url = await text_service.get_default_media(session)
                
            if media_url and not media_url.startswith(('http://', 'https://')):
                media_url = f"{settings.media.base_url}/app/{media_url}"

            log.info("Generated media URL for question: %s", media_url) 

            question_text = settings.quiz_text.question_text_begging_1 + f"{current_question + 1}" + settings.quiz_text.question_text_begging_2 + f"{len(sorted_questions)}:\n\n{question.question_text.replace('\\n', '\n')}"

            await send_or_edit_message(
                message,
                question_text,
                reply_markup,
                media_url
            )

            data['intro_shown'] = False  # Сбрасываем флаг для следующего вопроса
            await state.update_data(data)
            await state.set_state(QuizStates.ANSWERING)

        except Exception as e:
            log.exception(e)
        finally:
            await session.close()


@router.callback_query(QuizStates.ANSWERING)
async def process_answer(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sorted_questions = data['sorted_questions']
    
    if callback_query.data == "quiz_back":
        if data['current_question'] > 0:
            data['current_question'] -= 1
            if data['answers']:
                last_answer = data['answers'].pop()
                # Remove from category scores if needed
                if data.get('category_scores'):  # Проверяем наличие словаря
                    data['category_scores'][last_answer] = data['category_scores'].get(last_answer, 1) - 1
                    if data['category_scores'][last_answer] <= 0:
                        del data['category_scores'][last_answer]
            await state.update_data(data)
            await send_question(callback_query.message, state)
        return

    question_num, answer_num = map(int, callback_query.data.split("_")[1:])
    
    async for session in db_helper.session_getter():
        try:
            question_data = sorted_questions[question_num]
            question = question_data['question']  # Получаем сам объект вопроса
            
            test = await session.execute(select(Test).where(Test.id == data['quiz_id']))
            test = test.scalar_one()
            
            score = getattr(question, f'answer{answer_num}_score')
            data['answers'].append(score)
            
            # Update category scores if this is a multi-graph test
            if test.multi_graph_results:
                if 'category_scores' not in data:
                    data['category_scores'] = {}
                # Используем score как идентификатор категории и считаем количество ответов
                data['category_scores'][score] = data['category_scores'].get(score, 0) + 1
            
            await state.update_data(data)
            
            if question_data['comment']:
                await show_comment(callback_query.message, question_data['comment'], state)
            else:
                data['current_question'] += 1
                await state.update_data(data)
                await send_question(callback_query.message, state)

        except Exception as e:
            log.exception(e)
        finally:
            await session.close()


async def show_comment(message: types.Message, comment: str, state: FSMContext):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=settings.quiz_text.quiz_continue_button, callback_data="continue_quiz")]
    ])
    
    data = await state.get_data()
    async for session in db_helper.session_getter():
        try:
            questions = await get_sorted_questions(session, data['quiz_id'])
            question = questions[data['current_question']]['question']  # получаем сам вопрос
            
            comment = questions[data['current_question']]['comment']  # получаем комментарий

                        
            test = await session.execute(select(Test).where(Test.id == data['quiz_id']))
            test = test.scalar_one()
            
            text_service = TextService()
            
            # Priority: question -> test -> default media
            if question.picture:
                media_url = question.picture
            elif test.picture:
                media_url = test.picture
            else:
                media_url = await text_service.get_default_media(session)
            
            if media_url and not media_url.startswith(('http://', 'https://')):
                media_url = f"{settings.media.base_url}/app/{media_url}"
            
            comment_text = settings.quiz_text.question_comment_header + f"\n\n{comment.replace('\\n', '\n')}"
            
            await send_or_edit_message(
                message,
                comment_text,
                keyboard,
                media_url
            )
        except Exception as e:
            log.exception(e)
        finally:
            await session.close()
    
    await state.set_state(QuizStates.SHOWING_COMMENT)


@router.callback_query(QuizStates.SHOWING_COMMENT)
async def process_comment(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "continue_quiz":
        data = await state.get_data()
        data['current_question'] += 1
        await state.update_data(data)
        await send_question(callback_query.message, state)


# async def calculate_results(session, test, total_scores, category_scores):
#     """Calculate results based on test type and scoring method."""
#     if test.multi_graph_results:
#         final_results = []
#         for category_id, count in category_scores.items():
#             results = await session.execute(
#                 select(Result).where(
#                     Result.test_id == test.id,
#                     Result.category_id == category_id,
#                     Result.min_score <= count,
#                     Result.max_score >= count
#                 )
#             )
#             category_result = results.scalar_one_or_none()
#             if category_result:
#                 final_results.append({
#                     'category_id': category_id,
#                     'category_name': test.get_category_name(category_id),
#                     'score': count,
#                     'text': category_result.text,
#                     'picture': category_result.picture
#                 })
#         return final_results
#     else:
#         # For traditional single-result tests
#         results = await session.execute(
#             select(Result).where(
#                 Result.test_id == test.id,
#                 Result.category_id.is_(None),  # Обычные результаты без категорий
#                 Result.min_score <= total_scores,
#                 Result.max_score >= total_scores
#             )
#         )
#         result = results.scalar_one_or_none()
#         return [{
#             'score': total_scores,
#             'text': result.text if result else settings.quiz_text.quiz_result_error_undefined,
#             'picture': result.picture if result else None
#         }]

async def calculate_results(session, test, total_scores, category_scores):
    """Calculate results based on test type and scoring method."""
    if test.multi_graph_results:
        final_results = []
        # Get all distinct category IDs
        all_categories = await session.execute(
            select(Result.category_id).distinct()
            .where(Result.test_id == test.id)
            .where(Result.category_id.isnot(None))
        )
        all_categories = [cat[0] for cat in all_categories.fetchall()]
        
        # Process each category including 0 score 
        for category_id in all_categories:
            count = category_scores.get(category_id, 0)  # If category not found, set score to 0
            results = await session.execute(
                select(Result).where(
                    Result.test_id == test.id,
                    Result.category_id == category_id,
                    Result.min_score <= count,
                    Result.max_score >= count
                )
            )
            category_result = results.scalar_one_or_none()
            if category_result:
                final_results.append({
                    'category_id': category_id,
                    'category_name': test.get_category_name(category_id),
                    'score': count,
                    'text': category_result.text,
                    'picture': category_result.picture
                })
        return final_results
    else:
        # For traditional single-result tests
        results = await session.execute(
            select(Result).where(
                Result.test_id == test.id,
                Result.category_id.is_(None),  # Regular results without categories for regular non multi-graph tests
                Result.min_score <= total_scores,
                Result.max_score >= total_scores
            )
        )
        result = results.scalar_one_or_none()
        return [{
            'score': total_scores,
            'text': result.text if result else settings.quiz_text.quiz_result_error_undefined,
            'picture': result.picture if result else None
        }]


async def finish_quiz(message: types.Message, state: FSMContext):
    data = await state.get_data()
    quiz_id = data['quiz_id']
    total_score = sum(data['answers'])
    category_scores = data.get('category_scores', {})

    async for session in db_helper.session_getter():
        try:
            test = await session.execute(select(Test).where(Test.id == quiz_id))
            test = test.scalar_one()

            user = await session.execute(select(User).where(User.chat_id == message.chat.id))
            user = user.scalar_one()

            # Calculate results
            results = await calculate_results(session, test, total_score, category_scores)

            # Save results
            for result in results:
                quiz_result = QuizResult(
                    user_id=user.id,
                    test_id=test.id,
                    score=result.get('score', 0),
                    category_id=result.get('category_id'),
                    is_psychological=test.is_psycological,
                    result_text=result['text']
                )
                session.add(quiz_result)
            await session.commit()

            # Prepare result message and media
            if test.multi_graph_results:
                result_message = settings.quiz_text.quiz_multi_result + "\n\n"
                for result in results:
                    result_message += f"{result['category_name']}: {result['score']}\n{result['text']}\n\n"
            else:
                result_message = settings.quiz_text.quiz_result + f"{total_score}\n\n{results[0]['text']}"

            # Prepare keyboard based on test type
            if test.is_psycological:
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text=settings.quiz_text.psycological_menu_button_for_end_quiz, callback_data="show_psyco_tests")],
                    [types.InlineKeyboardButton(text=settings.quiz_text.quiz_back_to_start, callback_data="back_to_start")]
                ])
            else:
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text=settings.quiz_text.quiz_list_menu_button_for_end_quiz, callback_data="show_quizzes")],
                    [types.InlineKeyboardButton(text=settings.quiz_text.quiz_back_to_start, callback_data="back_to_start")]
                ])

            # Get appropriate media URL
            text_service = TextService()
            media_url = (results[0].get('picture') if results else None) or test.picture or await text_service.get_default_media(session)
            
            if media_url and not media_url.startswith(('http://', 'https://')):
                media_url = f"{settings.media.base_url}/app/{media_url}"

            await send_or_edit_message(
                message,
                result_message,
                keyboard,
                media_url
            )

        except Exception as e:
            log.exception(e)
        finally:
            await session.close()
            await state.clear()


@router.callback_query(lambda c: c.data and c.data.startswith(("show_quizzes", "start_quiz_", "confirm_start_", "start_questions_", "answer_", "quiz_back", "continue_quiz")))
async def process_quiz_callback(callback_query: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await show_quizzes(callback_query, state)
    elif current_state == QuizStates.VIEWING_TESTS:
        if callback_query.data.startswith("start_quiz_"):
            await start_quiz(callback_query, state)
        else:
            await show_quizzes(callback_query, state)
    elif current_state == QuizStates.CONFIRMING:
        if callback_query.data.startswith("confirm_start_"):
            await confirm_start_quiz(callback_query, state)
        else:
            await show_quizzes(callback_query, state)
    elif current_state == QuizStates.VIEWING_INTRO:
        if callback_query.data.startswith("start_questions_"):
            await start_questions(callback_query, state)
    elif current_state == QuizStates.ANSWERING:
        await process_answer(callback_query, state)
    elif current_state == QuizStates.SHOWING_COMMENT:
        await process_comment(callback_query, state)
    else:
        await callback_query.answer(settings.quiz_text.quiz_error)
        await state.clear()
        await show_quizzes(callback_query, state)
