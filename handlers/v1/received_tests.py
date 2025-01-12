# handlers/received_tests.py

from datetime import datetime

from aiogram import Router, types, Bot
from aiogram.types import CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from sqlalchemy import select, func, or_

from core import log, settings
from core.models import db_helper
from core.models import Test, QuizResult, User, SentTest, Result
from core.models.sent_test import TestStatus
from services.text_service import TextService
from services.user_services import UserService

from .utils import send_or_edit_message
from .quiz import get_sorted_questions


router = Router()

class BaseQuizStates(StatesGroup):
    VIEWING_INTRO = State()
    ANSWERING = State()
    SHOWING_COMMENT = State()

class ReceivedTestStates(BaseQuizStates):
    VIEWING_RECEIVED_TESTS = State()
    VIEWING_SENDER_TESTS = State()
    CONFIRMING = State()


async def notify_sender(bot: Bot, sender_id: int, receiver_username: str, action: str, test_name: str = None):  # TODO: Add button  (( ? ))
    try:
        if action == "completed":
            message = settings.received_tests.send_tests_notifier + f"{receiver_username} " + settings.received_tests.send_tests_notifier_completed + f" '{test_name}'."
        elif action == "rejected":
            message = settings.received_tests.send_tests_notifier + f"{receiver_username} " + settings.received_tests.send_tests_notifier_rejected +  f" '{test_name}'."
        else:
            return
        await bot.send_message(sender_id, message)
    except Exception as e:
        log.exception("Failed to notify sender %s: %s", sender_id, e)


@router.callback_query(lambda c: c.data == "view_received_tests")
async def view_received_tests(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    receiver_id = callback_query.from_user.id
    page = 1
    await state.update_data(current_page=page)
    await show_received_tests_page(callback_query, callback_query.message, receiver_id, page, state)


@router.callback_query(lambda c: c.data == "current_page")  # TODO: Double check (( ! ))
async def current_page(callback_query: types.CallbackQuery):
    await callback_query.answer(settings.received_tests.page_number)


async def show_received_tests_page(callback_query, message: types.Message, receiver_id: int, page: int, state: FSMContext):
    async for session in db_helper.session_getter():
        try:
            subquery = (
                select(SentTest.sender_username, func.max(SentTest.created_at).label("last_sent"))
                .where(SentTest.receiver_username == callback_query.from_user.username, SentTest.status.in_([TestStatus.DELIVERED, TestStatus.SENT]))
                .group_by(SentTest.sender_username)
                .subquery()
            )

            query = (
                select(subquery.c.sender_username)
                .select_from(subquery)
                .order_by(subquery.c.last_sent.desc())
                .offset((page - 1) * 20)
                .limit(20)
            )

            result = await session.execute(query)
            senders = result.scalars().all()

            total_senders_query = (
                select(func.count(func.distinct(SentTest.sender_username)))
                .where(SentTest.receiver_id == receiver_id, SentTest.status.in_([TestStatus.DELIVERED, TestStatus.SENT]))
            )
            total_senders_result = await session.execute(total_senders_query)
            total_senders = total_senders_result.scalar()

            total_pages = (total_senders - 1) // 20 + 1

            keyboard = []
            for i in range(0, len(senders), 2):
                row = []
                for sender in senders[i:i+2]:
                    row.append(types.InlineKeyboardButton(text=sender, callback_data=f"view_sender_tests_{sender}"))
                keyboard.append(row)

            navigation = []
            if page > 1:
                navigation.append(types.InlineKeyboardButton(text="◀️", callback_data="prev_page"))
            navigation.append(types.InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="current_page"))
            if page < total_pages:
                navigation.append(types.InlineKeyboardButton(text="▶️", callback_data="next_page"))
            if navigation:
                keyboard.append(navigation)

            keyboard.append([types.InlineKeyboardButton(text=settings.received_tests.back_button, callback_data="back_to_start")])

            text_service = TextService()

            if total_senders == 0:
                text = settings.received_tests.tests_no_tests
            else:
                text = settings.received_tests.tests_choose_sender
                
            media_url = await text_service.get_default_media(session)

            await send_or_edit_message(message, text, types.InlineKeyboardMarkup(inline_keyboard=keyboard), media_url)
            await state.set_state(ReceivedTestStates.VIEWING_RECEIVED_TESTS)

        except Exception as e:
            log.exception(e)
            await message.answer(settings.received_tests.senders_page_loading_error)
        finally:
            await session.close()


@router.callback_query(lambda c: c.data and c.data.startswith("view_sender_tests_"))
async def view_sender_tests(callback_query: types.CallbackQuery, state: FSMContext, sender_username: str | None = None):
    await callback_query.answer()
    
    if not sender_username:
        parts = callback_query.data.split("_")
        sender_username = "_".join(parts[3:])
    
    receiver_username = callback_query.from_user.username
    
    async for session in db_helper.session_getter():
        try:
            log.info("Fetching tests for receiver %s from sender %s", receiver_username, sender_username)
            
            tests = await session.execute(
                select(SentTest)
                .where(
                    SentTest.receiver_username == receiver_username,
                    SentTest.sender_username == sender_username,
                    or_(
                        SentTest.status == TestStatus.DELIVERED,
                        SentTest.status == TestStatus.SENT
                    )
                )
                .order_by(SentTest.created_at.desc())
            )
            tests = tests.scalars().all()
            log.info("Found %s tests", len(tests))

            user_id_to_get_him_from_db = int(callback_query.from_user.id)
            user_from_db = await UserService.get_user(user_id_to_get_him_from_db)

            if not user_from_db:
                log.error("User %s not found in database", callback_query.from_user.id)
                return
            
            keyboard = []
            for test in tests:
                test_info = await session.execute(select(Test).where(Test.id == test.test_id))
                test_info = test_info.scalar_one()

                keyboard.append([types.InlineKeyboardButton(text=(settings.received_tests.choose_sent_test_button + f" {test.test_name}"), callback_data=f"start_received_test_{test.id}")])

            if tests:
                keyboard.append([types.InlineKeyboardButton(text=(settings.received_tests.reject_all_from_user_button + f" {sender_username}"), callback_data=f"reject_all_tests_{sender_username}")])
            keyboard.append([types.InlineKeyboardButton(text=settings.received_tests.back_to_senders_list_button, callback_data="view_received_tests")])
            keyboard.append([types.InlineKeyboardButton(text=settings.received_tests.to_main_menu_button, callback_data="back_to_start")])

            text_service = TextService()
            text = (settings.received_tests.tests_from_username_button + f"{sender_username}:")
            if not tests:
                text += "\n\n" + settings.received_tests.no_test_from_user
            
            media_url = await text_service.get_default_media(session)

            await send_or_edit_message(callback_query.message, text, types.InlineKeyboardMarkup(inline_keyboard=keyboard), media_url)
            await state.set_state(ReceivedTestStates.VIEWING_SENDER_TESTS)

        except Exception as e:
            log.exception("Error in view_sender_tests: %s", e)
            await callback_query.answer(settings.received_tests.tests_loading_error)
        finally:
            await session.close()


@router.callback_query(lambda c: c.data and c.data.startswith("reject_all_tests_"))
async def reject_all_tests(callback_query: types.CallbackQuery): 
    await callback_query.answer()
    parts = callback_query.data.split("_")
    sender_username = "_".join(parts[3:])
    
    if not sender_username:
        await callback_query.answer(settings.received_tests.sender_info_not_found_error)
        return
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=settings.received_tests.confirm_reject_all_test_button, callback_data=f"confirm_reject_all_{sender_username}")],
        [types.InlineKeyboardButton(text=settings.received_tests.cancel_reject_test_button, callback_data=f"view_sender_tests_{sender_username}")],
    ])
    
    text_service = TextService()
    async for session in db_helper.session_getter():
        try:
            text = settings.received_tests.reject_all_tests_confirmation + f" @{sender_username}?"
            
            media_url = await text_service.get_default_media(session)
            
            await send_or_edit_message(
                callback_query.message,
                text,
                keyboard,
                media_url
            )
        except Exception as e:
            log.exception(e)
            await callback_query.answer(settings.received_tests.confirm_error)
        finally:
            await session.close()


@router.callback_query(lambda c: c.data and c.data.startswith("confirm_reject_all_"))
async def confirm_reject_all_tests(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    parts = callback_query.data.split("_")
    sender_username = "_".join(parts[3:])
    async for session in db_helper.session_getter():
        try:
            tests = await session.execute(
                select(SentTest)
                .where(SentTest.receiver_username == callback_query.from_user.username,
                    SentTest.sender_username == sender_username,
                    SentTest.status.in_([TestStatus.DELIVERED, TestStatus.SENT]))
            )
            tests = tests.scalars().all()
            for test in tests:
                test.status = TestStatus.REJECTED
                await notify_sender(callback_query.bot, test.sender_id, callback_query.from_user.username, "rejected", test.test_name)
            await session.commit()
            
            # Check if there are other tests from other senders
            other_tests = await session.execute(
                select(SentTest)
                .where(SentTest.receiver_username == callback_query.from_user.username,
                    SentTest.sender_username != sender_username,
                    SentTest.status.in_([TestStatus.DELIVERED, TestStatus.SENT]))
            )
            other_tests = other_tests.scalars().all()
            
            if other_tests:
                await view_received_tests(callback_query, state)
            else:
                from .on_start import back_to_start
                await back_to_start(callback_query, state)
            
        except Exception as e:
            log.exception(e)
            await callback_query.answer(settings.received_tests.reject_all_tests_error)
        finally:
            await session.close()


@router.callback_query(lambda c: c.data and c.data.startswith("reject_test_"))
async def reject_test(callback_query: types.CallbackQuery):
    await callback_query.answer()
    sent_test_id = callback_query.data.split("_")[-1]
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=settings.received_tests.confirm_reject_test_button, callback_data=f"confirm_reject_test_{sent_test_id}")],
        [types.InlineKeyboardButton(text=settings.received_tests.cancel_reject_test_button, callback_data=f"cancel_reject_test_{sent_test_id}")]
    ])

    async for session in db_helper.session_getter():  # TODO: Upgrade to send test's media with higher priority then default (( ! ))
        try:
            media = await TextService.get_default_media(session)
        except Exception as e:
            log.exception(e)
            media = None
        finally:
            await session.close()
    
    await send_or_edit_message(
        callback_query.message,
        settings.received_tests.reject_test_confirm,
        keyboard,
        media
    )


@router.callback_query(lambda c: c.data and c.data.startswith("confirm_reject_test_"))
async def confirm_reject_test(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    sent_test_id = callback_query.data.split("_")[-1]
    async for session in db_helper.session_getter():
        try:
            sent_test = await session.execute(select(SentTest).where(SentTest.id == sent_test_id))
            sent_test = sent_test.scalar_one()
            sent_test.status = TestStatus.REJECTED
            await session.commit()
            
            await notify_sender(callback_query.bot, sent_test.sender_id, callback_query.from_user.username, "rejected", sent_test.test_name)
            
            # Проверяем наличие других тестов от того же отправителя
            other_tests_from_sender = await session.execute(
                select(SentTest)
                .where(SentTest.receiver_username == callback_query.from_user.username,
                    SentTest.sender_username == sent_test.sender_username,
                    SentTest.status.in_([TestStatus.DELIVERED, TestStatus.SENT]))
            )
            other_tests_from_sender = other_tests_from_sender.scalars().all()
            
            if other_tests_from_sender:
                await view_sender_tests(callback_query, state, sent_test.sender_username) 
            else:
                # Проверяем наличие тестов от других отправителей
                other_tests = await session.execute(
                    select(SentTest)
                    .where(SentTest.receiver_username == callback_query.from_user.username,
                        SentTest.status.in_([TestStatus.DELIVERED, TestStatus.SENT]))
                )
                other_tests = other_tests.scalars().all()
                
                if other_tests:
                    await view_received_tests(callback_query, state)
                else:
                    from .on_start import back_to_start
                    await back_to_start(callback_query, state)
            
        except Exception as e:
            log.exception(e)
            await callback_query.answer(settings.received_tests.reject_test_error)
        finally:
            await session.close()


@router.callback_query(lambda c: c.data and c.data.startswith("cancel_reject_test_"))
async def cancel_reject_test(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer(settings.received_tests.reject_test_from_user_canceled)
    await start_received_test(callback_query, state)


async def get_latest_category_results(session, user_id: str, test_id: str):
    """
    Get the latest results for each category of a test for a specific user.
    Returns a list of QuizResult objects, one per category.
    """
    # First get all distinct categories for this test/user combination
    distinct_categories = await session.execute(
        select(QuizResult.category_id)
        .distinct()
        .where(
            QuizResult.user_id == user_id,
            QuizResult.test_id == test_id,
            QuizResult.category_id.isnot(None)
        )
    )
    categories = [cat[0] for cat in distinct_categories.fetchall()]
    
    # For each category, get the latest result
    latest_results = []
    for category_id in categories:
        latest_result = await session.execute(
            select(QuizResult)
            .where(
                QuizResult.user_id == user_id,
                QuizResult.test_id == test_id,
                QuizResult.category_id == category_id
            )
            .order_by(QuizResult.created_at.desc())
            .limit(1)
        )
        result = latest_result.scalar_one_or_none()
        if result:
            latest_results.append(result)
    
    # Sort results by score in descending order # TODO: Doublecheck
    latest_results.sort(key=lambda x: x.score, reverse=True)
    
    return latest_results


@router.callback_query(lambda c: c.data and c.data.startswith("send_existing_result_"))
async def send_existing_result(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    sent_test_id = callback_query.data.split("_")[-1]
    async for session in db_helper.session_getter():
        try:
            sent_test = await session.execute(select(SentTest).where(SentTest.id == sent_test_id))
            sent_test = sent_test.scalar_one()

            test = await session.execute(select(Test).where(Test.id == sent_test.test_id))
            test = test.scalar_one()

            user = await session.execute(select(User).where(User.chat_id == callback_query.from_user.id))
            user = user.scalar_one()

            # Handle multi-category results
            if test.multi_graph_results:
                latest_results = await get_latest_category_results(session, str(user.id), str(test.id))
                
                if latest_results:
                    # Combine all category results into one message
                    combined_result_text = ""  #settings.received_tests.quiz_multi_result + "\n\n"
                    total_score = 0
                    
                    for result in latest_results:
                        combined_result_text += f"{result.category_name}: {result.score}\n{result.result_text}\n\n"
                        total_score += result.score
                    
                    sent_test.status = TestStatus.COMPLETED
                    sent_test.completed_at = datetime.now()
                    sent_test.result_score = str(total_score)  # Sum of all category scores
                    sent_test.result_text = combined_result_text
                    
                    await session.commit()
                    
                    await notify_sender(callback_query.bot, sent_test.sender_id, user.username, "completed", test.name)
                    
                    result_message = (settings.received_tests.send_test_result_success_sent_1 + 
                                    f" '{test.name}' " + 
                                    settings.received_tests.send_test_result_success_sent_2 + 
                                    f"\n\n{combined_result_text}")
                else:
                    await callback_query.answer(settings.received_tests.result_send_not_found_please_pass_test)
                    return
            else:
                # Handle single-result tests (existing logic)
                latest_result = await session.execute(
                    select(QuizResult)
                    .where(QuizResult.user_id == str(user.id), QuizResult.test_id == str(test.id))
                    .order_by(QuizResult.created_at.desc())
                    .limit(1)
                )
                latest_result = latest_result.scalar_one_or_none()

                if not latest_result:
                    await callback_query.answer(settings.received_tests.result_send_not_found_please_pass_test)
                    return

                sent_test.status = TestStatus.COMPLETED
                sent_test.completed_at = datetime.now()
                sent_test.result_score = str(latest_result.score)
                sent_test.result_text = latest_result.result_text
                
                await session.commit()
                
                await notify_sender(callback_query.bot, sent_test.sender_id, user.username, "completed", test.name)
                
                result_message = (settings.received_tests.send_test_result_success_sent_1 + 
                                f" '{test.name}' " + 
                                settings.received_tests.send_test_result_success_sent_2 + 
                                f" {latest_result.score}\n\n{sent_test.result_text.replace('\\n', '\n')}")

            # Check for other tests from the same sender
            other_tests_from_sender = await session.execute(
                select(SentTest)
                .where(SentTest.receiver_username == callback_query.from_user.username,
                    SentTest.sender_username == sent_test.sender_username,
                    SentTest.status.in_([TestStatus.DELIVERED, TestStatus.SENT]))
            )
            other_tests_from_sender = other_tests_from_sender.scalars().all()

            if other_tests_from_sender:
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text=settings.received_tests.back_to_recived_tests_button, 
                                              callback_data=f"view_sender_tests_{sent_test.sender_username}")],
                    [types.InlineKeyboardButton(text=settings.received_tests.to_main_menu_button, 
                                              callback_data="back_to_start")]
                ])
            else:
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text=settings.received_tests.back_to_recived_tests_button, 
                                              callback_data="view_received_tests")],
                    [types.InlineKeyboardButton(text=settings.received_tests.to_main_menu_button, 
                                              callback_data="back_to_start")]
                ])

            media_url = test.picture if test.picture else await TextService().get_default_media(session)
            
            if media_url and not media_url.startswith(('http://', 'https://')):
                media_url = f"{settings.media.base_url}/app/{media_url}"

            await send_or_edit_message(
                callback_query.message,
                result_message,
                keyboard,
                media_url
            )

        except Exception as e:
            log.exception(e)
            await callback_query.answer(settings.received_tests.result_send_error)
        finally:
            await session.close()


@router.callback_query(lambda c: c.data and c.data.startswith("start_received_test_"))
async def start_received_test(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    sent_test_id = callback_query.data.split("_")[-1]
    
    async for session in db_helper.session_getter():
        try:
            sent_test = await session.execute(select(SentTest).where(SentTest.id == sent_test_id))
            sent_test = sent_test.scalar_one_or_none()
            if not sent_test:
                await callback_query.answer(settings.received_tests.test_not_found)
                return

            test = await session.execute(select(Test).where(Test.id == sent_test.test_id))
            test = test.scalar_one_or_none()
            if not test:
                await callback_query.answer(settings.received_tests.test_not_found)
                return
            
            user_id_to_get_him_from_db = int(callback_query.from_user.id)
            user_from_db = await UserService.get_user(user_id_to_get_him_from_db)
            
            # Check if user's result already exists and pick the latest one
            latest_results = await session.execute(
                select(QuizResult)
                .where(
                    QuizResult.user_id == user_from_db.id,
                    QuizResult.test_id == test.id
                )
                .order_by(QuizResult.created_at.desc())
                .limit(1)
            )
            latest_result = latest_results.scalar_one_or_none()

            if latest_result:
                if not latest_result.score is not None:  # TODO: Double check (( ! ))
                    keyboard = [
                        [types.InlineKeyboardButton(text=settings.received_tests.start_test_button, callback_data=f"confirm_run_received_test_{test.id}")],  # sent_test_id
                    ]
                elif test.allow_play_again and latest_result.score is not None:
                    keyboard = [
                        [types.InlineKeyboardButton(text=settings.received_tests.start_test_button, callback_data=f"confirm_run_received_test_{test.id}")],  # sent_test_id
                        [types.InlineKeyboardButton(text=(settings.received_tests.send_saved_result_button + f": {latest_result.score}"), callback_data=f"send_existing_result_{sent_test_id}")]
                    ]  
                elif not test.allow_play_again and latest_result.score is not None:
                    keyboard = [
                        [types.InlineKeyboardButton(text=(settings.received_tests.send_saved_result_button + f": {latest_result.score}"), callback_data=f"send_existing_result_{sent_test_id}")],
                    ]
                else:
                    keyboard = [
                        [types.InlineKeyboardButton(text=settings.received_tests.start_test_button, callback_data=f"confirm_run_received_test_{test.id}")],  # sent_test_id
                    ]
            else:
                keyboard = [
                    [types.InlineKeyboardButton(text=settings.received_tests.start_test_button, callback_data=f"confirm_run_received_test_{test.id}")],  # sent_test_id
                ]

            keyboard.append([types.InlineKeyboardButton(text=settings.received_tests.reject_test_button, callback_data=f"reject_test_{sent_test_id}")])
            keyboard.append([types.InlineKeyboardButton(text=settings.received_tests.back_to_tests_list_button, callback_data=f"view_sender_tests_{sent_test.sender_username}")])
            keyboard.append([types.InlineKeyboardButton(text=settings.received_tests.to_main_menu_button, callback_data="back_to_start")])

            text_service = TextService()

            text = (settings.received_tests.start_test_confirm + f"\n'{test.name}'\n\n" + f"{test.description.replace('\\n', '\n')}\n\n" + settings.received_tests.start_test_confirm_2)
            media_url = test.picture if test.picture else await text_service.get_default_media(session)

            if media_url and not media_url.startswith(('http://', 'https://')):
                media_url = f"{settings.media.base_url}/app/{media_url}"

            await send_or_edit_message(
                callback_query.message,
                text,
                types.InlineKeyboardMarkup(inline_keyboard=keyboard),
                media_url
            )
            await state.set_state(ReceivedTestStates.CONFIRMING)
            await state.update_data(sent_test_id=sent_test_id)

        except Exception as e:
            log.exception(e)
            await callback_query.answer(settings.received_tests.start_test_error)
        finally:
            await session.close()


async def process_intro(callback_query: types.CallbackQuery, state: FSMContext, state_group: StatesGroup):
    if callback_query.data == "show_received_question":
        data = await state.get_data()
        data['intro_shown'] = True
        await state.update_data(data)
        await send_question(callback_query.message, state, state_group)


async def process_comment(callback_query: types.CallbackQuery, state: FSMContext, state_group: StatesGroup):
    data = await state.get_data()
    data['current_question'] += 1
    await state.update_data(data)
    await send_question(callback_query.message, state, state_group)


async def process_answer(callback_query: types.CallbackQuery, state: FSMContext, state_group: StatesGroup):
    data = await state.get_data()
    sorted_questions = data['sorted_questions']
    
    if callback_query.data == "quiz_back":
        if data['current_question'] > 0:
            data['current_question'] -= 1
            if data['answers']:
                last_answer = data['answers'].pop()
                # Remove from category scores if needed
                if data.get('category_scores'):  # Check if there is a dictionary
                    data['category_scores'][last_answer] = data['category_scores'].get(last_answer, 1) - 1
                    if data['category_scores'][last_answer] <= 0:
                        del data['category_scores'][last_answer]
            await state.update_data(data)
            await send_question(callback_query.message, state, state_group)
        return

    question_num, answer_num = map(int, callback_query.data.split("_")[1:])
    
    async for session in db_helper.session_getter():
        try:
            question_data = sorted_questions[question_num]
            question = question_data['question']  # Get the question object
            
            test = await session.execute(select(Test).where(Test.id == data['quiz_id']))
            test = test.scalar_one()
            
            score = getattr(question, f'answer{answer_num}_score')
            data['answers'].append(score)
            
            # Update category scores if this is a multi-graph test
            if test.multi_graph_results:
                if 'category_scores' not in data:
                    data['category_scores'] = {}
                # Use score as an identifier of the category and count the number of answers
                data['category_scores'][score] = data['category_scores'].get(score, 0) + 1
            
            await state.update_data(data)
            
            if question_data['comment']:
                await show_comment(callback_query.message, question_data['comment'], state, state_group)
            else:
                data['current_question'] += 1
                await state.update_data(data)
                await send_question(callback_query.message, state, state_group)

        except Exception as e:
            log.exception(e)
        finally:
            await session.close()


async def show_comment(message: types.Message, comment: str, state: FSMContext, state_group: StatesGroup):
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text=settings.quiz_text.quiz_continue_button, callback_data="continue_quiz")]
    ])
    
    data = await state.get_data()
    async for session in db_helper.session_getter():
        try:
            questions = await get_sorted_questions(session, data['quiz_id'])
            question = questions[data['current_question']]['question']  # Get the question
            comment = questions[data['current_question']]['comment']  # Get the comment

                        
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
    
    await state.set_state(state_group.SHOWING_COMMENT)


async def start_questions(message: types.Message, state: FSMContext, state_group: StatesGroup, quiz_id: str = None):
    if not quiz_id:  # If called from callback
        quiz_id = message.data.split("_")[-1]
    await send_question(message if isinstance(message, types.Message) else message.message, state, state_group)


# @router.callback_query(lambda c: c.data.startswith("confirm_run_received_test_"))
async def confirm_start_received_test(callback_query: CallbackQuery, state: FSMContext, state_group: StatesGroup, quiz_id: str = None):
    if not quiz_id:  # If called from callback
        quiz_id = callback_query.data.split("_")[-1]
    async for session in db_helper.session_getter():
        try:
            # Get and save the order of questions at start
            sorted_questions = await get_sorted_questions(session, quiz_id)
            await state.update_data(
                quiz_id=quiz_id, 
                current_question=0, 
                answers=[], 
                category_scores={}, 
                intro_shown=False,
                sorted_questions=sorted_questions  # Save the order
            )
            await send_question(callback_query.message, state, state_group)
        except Exception as e:
            log.exception(e)
        finally:
            await session.close()


async def send_question(message: types.Message, state: FSMContext, state_group: StatesGroup):
    data = await state.get_data()
    quiz_id = data['quiz_id']
    current_question = data['current_question']
    sorted_questions = data['sorted_questions']

    async for session in db_helper.session_getter():
        try:
            test = await session.execute(select(Test).where(Test.id == quiz_id))
            test = test.scalar_one_or_none()

            if current_question >= len(sorted_questions):
                await finish_received_test(message, state)
                return

            question_data = sorted_questions[current_question]
            question = question_data['question']  # Get the question object

            # Check if there is an intro text for the current question
            if question_data['intro_text'] and not data.get('intro_shown'):
                keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text=settings.quiz_text.quiz_continue_button, callback_data="show_received_question")]
                ])
                
                text_service = TextService()
                # Media priority
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
                await state.set_state(state_group.VIEWING_INTRO)
                return

            # If there is no intro or it has already been shown, show the question
            keyboard = []
            for i in range(1, 7):
                answer_text = getattr(question, f'answer{i}_text')  # Use the question object to get the answers
                if answer_text:
                    keyboard.append([types.InlineKeyboardButton(
                        text=answer_text,
                        callback_data=f"answ_{current_question}_{i}"
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

            data['intro_shown'] = False  # Drop the flag for the next question
            await state.update_data(data)
            await state.set_state(state_group.ANSWERING)

        except Exception as e:
            log.exception(e)
        finally:
            await session.close()


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
        
        # Sort results by score in descending order
        final_results.sort(key=lambda x: x['score'], reverse=True)
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


async def finish_received_test(message: types.Message, state: FSMContext):
    data = await state.get_data()
    quiz_id = data['quiz_id']
    sent_test_id = data['sent_test_id']
    total_score = sum(data['answers'])
    category_scores = data.get('category_scores', {})

    async for session in db_helper.session_getter():
        try:
            # Get test, sent test, and user information
            test = await session.execute(select(Test).where(Test.id == quiz_id))
            test = test.scalar_one()

            sent_test = await session.execute(select(SentTest).where(SentTest.id == sent_test_id))
            sent_test = sent_test.scalar_one()

            user = await session.execute(select(User).where(User.chat_id == message.chat.id))
            user = user.scalar_one()

            # Calculate and save results
            results = await calculate_results(session, test, total_score, category_scores)
            result_text = ""
            
            # Save results for each category/overall
            for result in results:
                quiz_result = QuizResult(
                    user_id=user.id,
                    test_id=test.id,
                    score=result.get('score', 0),
                    category_id=result.get('category_id'),
                    is_psychological=test.is_psychological,
                    result_text=result['text'],
                    # category_name=result.get('category_name')
                )
                session.add(quiz_result)

            # Update sent test status and results
            sent_test.status = TestStatus.COMPLETED
            sent_test.completed_at = datetime.now()
            sent_test.result_score = str(total_score)

            # Prepare result message based on test type
            if test.multi_graph_results:
                result_text = ""  # settings.quiz_text.quiz_multi_result + "\n\n"
                for result in results:
                    result_text += f"{result['category_name']}: {result['score']}\n{result['text']}\n\n"
            else:
                result_text = f"{settings.quiz_text.quiz_result}{total_score}\n\n{results[0]['text']}"

            sent_test.result_text = result_text
            await session.commit()

            # Notify sender about test completion
            await notify_sender(message.bot, sent_test.sender_id, user.username, "completed", test.name)

            # Check for remaining tests from the same sender
            remaining_tests = await session.execute(
                select(SentTest)
                .where(SentTest.receiver_username == user.username,
                      SentTest.sender_username == sent_test.sender_username,
                      SentTest.status.in_([TestStatus.DELIVERED, TestStatus.SENT]))
            )
            remaining_tests = remaining_tests.scalars().all()

            # Check for tests from other senders
            other_tests = await session.execute(
                select(SentTest)
                .where(SentTest.receiver_username == user.username,
                      SentTest.sender_username != sent_test.sender_username,
                      SentTest.status.in_([TestStatus.DELIVERED, TestStatus.SENT]))
            )
            other_tests = other_tests.scalars().all()

            # Build appropriate keyboard based on remaining tests
            keyboard = []
            if remaining_tests:
                keyboard.append([types.InlineKeyboardButton(
                    text=settings.received_tests.other_tests_from_sender_button,
                    callback_data=f"view_sender_tests_{sent_test.sender_username}"
                )])
            if other_tests:
                keyboard.append([types.InlineKeyboardButton(
                    text=settings.received_tests.tests_from_other_senders_button,
                    callback_data="view_received_tests"
                )])
            keyboard.append([types.InlineKeyboardButton(
                text=settings.received_tests.to_main_menu_button,
                callback_data="back_to_start"
            )])

            # Get appropriate media URL
            text_service = TextService()
            if results[0].get('picture'):
                media_url = results[0]['picture']
            elif test.picture:
                media_url = test.picture
            else:
                media_url = await text_service.get_default_media(session)

            if media_url and not media_url.startswith(('http://', 'https://')):
                media_url = f"{settings.media.base_url}/app/{media_url}"

            # Send final message with results
            await send_or_edit_message(
                message,
                result_text,
                types.InlineKeyboardMarkup(inline_keyboard=keyboard),
                media_url
            )

        except Exception as e:
            log.exception(e)
            await message.answer(settings.received_tests.test_end_error)
        finally:
            await session.close()
            await state.clear()


@router.callback_query(lambda c: c.data and c.data.startswith((
    "start_received_test_", "show_received_question",
    "answ_", "confirm_run_received_test_")))  # "quiz_back", "continue_quiz", "show_question"
async def process_quiz_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    
    current_state = await state.get_state()
    if current_state is None:
        pass
    
    # elif current_state == ReceivedTestStates.VIEWING_TESTS:
    #     if callback_query.data.startswith("start_received_test_"):
    #         await start_received_test(callback_query, state, ReceivedTestStates)
        # else:
        #     await show_quizzes(callback_query, state)  # TODO: Double check (( ! ))
    
    elif current_state == ReceivedTestStates.VIEWING_INTRO:
        await process_intro(callback_query, state, ReceivedTestStates)
    
    elif current_state == ReceivedTestStates.CONFIRMING:
        if callback_query.data.startswith("confirm_run_received_test_"):
            await confirm_start_received_test(callback_query, state, ReceivedTestStates)
        # else:
        #     await show_quizzes(callback_query, state)  # TODO: Double check (( ! ))
    
    elif current_state == ReceivedTestStates.VIEWING_INTRO:
        if callback_query.data.startswith("show_received_question"):
            await start_questions(callback_query, state, ReceivedTestStates)
    
    elif current_state == ReceivedTestStates.ANSWERING:
        await process_answer(callback_query, state, ReceivedTestStates)
    
    elif current_state == ReceivedTestStates.SHOWING_COMMENT:
        await process_comment(callback_query, state, ReceivedTestStates)
