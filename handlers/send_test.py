# handlers/send_test.py

import csv
import io
from datetime import datetime

from aiogram import Router, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile

from sqlalchemy import desc, func, select

from async_lru import alru_cache

from core import log, settings
from core.models import db_helper
from core.models.quiz import Test
from core.models.user import User
from core.models.sent_test import SentTest, TestStatus
from handlers.utils import send_or_edit_message
from services.text_service import TextService


router = Router()


# TODO: Idea add option to input for how many days the csv file sould be 
# TODO: Add AI Transcriptions for the tests results here


class SendTestStates(StatesGroup):
    CHOOSING_TEST_TYPE = State()
    CHOOSING_TEST = State()
    CONFIRMING_TESTS = State()
    ENTERING_RECEIVER = State()
    CONFIRMING = State()
    VIEWING_SENT_TESTS = State()
    VIEWING_USER_TESTS = State()


@alru_cache(maxsize=1, ttl=30)
async def get_send_test_media_url():
    try:
        async with db_helper.db_session() as session:
            text_service = TextService()
            
            log.debug("Fetching text with media for send_test")
            data = await text_service.get_text_with_media("send_test", session)
            log.debug(f"Got data: {data}")
            
            if not data:
                log.debug("No data found, getting default media")
                return await text_service.get_default_media(session)
            
            media_urls = data["media_urls"]
            log.debug(f"Got media_urls: {media_urls}")
            
            if media_urls and len(media_urls) >= 1:
                log.debug(f"Returning first media URL: {media_urls[0]}")
                return media_urls[0]
            
            log.debug("No media URLs found, getting default media")
            return await text_service.get_default_media(session)
            
    except Exception as e:
        log.exception(f"Error in get_send_test_media_url: {e}")
        return None


@router.callback_query(lambda c: c.data == "export_csv_all")
async def export_all_sent_tests_csv(callback_query: types.CallbackQuery, state: FSMContext):
    sender_id = callback_query.from_user.id
    await export_sent_tests_csv(callback_query, sender_id, all_tests=True)


@router.callback_query(lambda c: c.data == "export_csv_by_test")
async def show_export_by_test_options(callback_query: types.CallbackQuery, state: FSMContext):
    sender_id = callback_query.from_user.id
    async for session in db_helper.session_getter():
        try:
            tests = await session.execute(
                select(SentTest.test_name, SentTest.test_id, func.max(SentTest.created_at).label("last_sent"))
                .where(SentTest.sender_id == sender_id)
                .group_by(SentTest.test_name, SentTest.test_id)
                .order_by(func.max(SentTest.created_at).desc())
            )
            tests = tests.fetchall()

            keyboard = []
            for test_name, test_id, _ in tests:
                keyboard.append([types.InlineKeyboardButton(text=test_name, callback_data=f"export_csv_test_{test_id}")])
            
            keyboard.append([types.InlineKeyboardButton(text=settings.send_test.csv_export_back_button, callback_data="back_to_sent_tests")])

            text = settings.send_test.csv_choose_test_to_export

            media_url = await get_send_test_media_url()

            await send_or_edit_message(
                callback_query.message,
                text,
                types.InlineKeyboardMarkup(inline_keyboard=keyboard),
                media_url
            )

        except Exception as e:
            log.exception(e)
            await callback_query.answer(settings.send_test.csv_export_by_tests_error)
        finally:
            await session.close()


@router.callback_query(lambda c: c.data.startswith("export_csv_test_"))
async def export_sent_tests_by_test_csv(callback_query: types.CallbackQuery, state: FSMContext):
    sender_id = callback_query.from_user.id
    test_id = callback_query.data.split("_")[-1]
    await export_sent_tests_csv(callback_query, sender_id, test_id=test_id)


async def export_sent_tests_csv(callback_query: types.CallbackQuery, sender_id: int, all_tests: bool = False, test_id: str = None):
    async for session in db_helper.session_getter():
        try:
            query = select(SentTest).where(SentTest.sender_id == sender_id)
            if not all_tests and test_id:
                query = query.where(SentTest.test_id == test_id)
            
            sent_tests = await session.execute(query.order_by(desc(SentTest.created_at)))
            sent_tests = sent_tests.scalars().all()

            output = io.StringIO()
            writer = csv.writer(output)
            
            # Записываем заголовки
            writer.writerow(['sender_username', 'test_name', 'receiver_username', 'status', 'delivered_at', 'completed_at', 'result_score', 'result_text', 'created_at'])
            
            # Записываем данные
            for test in sent_tests:
                writer.writerow([
                    test.sender_username,
                    test.test_name,
                    test.receiver_username,
                    test.status.value,
                    test.delivered_at.isoformat() if test.delivered_at else '',
                    test.completed_at.isoformat() if test.completed_at else '',
                    test.result_score,
                    test.result_text,
                    test.created_at.isoformat()
                ])
            
            output_bytes = output.getvalue().encode('utf-8')
            
            # Отправляем файл 
            # TODO: EDIT FILE NAME
            filename = f"tests_{datetime.now().strftime('%Y_%m_%d__%H_%M_%S')}.csv"
            file = BufferedInputFile(output_bytes, filename=filename)
            await callback_query.message.answer_document(file)
            
            await callback_query.answer(settings.send_test.csv_export_success)
            
        except Exception as e:
            log.exception(e)
            await callback_query.answer(settings.send_test.csv_export_error)
        finally:
            await session.close()


async def export_user_tests_csv(callback_query: types.CallbackQuery, username: str):
    sender_id = callback_query.from_user.id
    async for session in db_helper.session_getter():
        try:
            sent_tests = await session.execute(
                select(SentTest)
                .where(SentTest.sender_id == sender_id, SentTest.receiver_username == username)
                .order_by(desc(SentTest.updated_at))
            )
            sent_tests = sent_tests.scalars().all()

            output = io.StringIO()
            writer = csv.writer(output)
            
            # Записываем заголовки
            writer.writerow(['test_name', 'status', 'created_at', 'delivered_at', 'completed_at', 'result_score', 'result_text'])
            
            # Записываем данные
            for test in sent_tests:
                writer.writerow([
                    test.test_name,
                    test.status.value,
                    test.created_at.isoformat(),
                    test.delivered_at.isoformat() if test.delivered_at else '',
                    test.completed_at.isoformat() if test.completed_at else '',
                    test.result_score,
                    test.result_text
                ])
            
            output_bytes = output.getvalue().encode('utf-8')
            
            # Отправляем файл
            filename = f"tests_for_{username}_{datetime.now().strftime('%Y_%m_%d__%H_%M_%S')}.csv"
            file = BufferedInputFile(output_bytes, filename=filename)
            await callback_query.message.answer_document(file)
            
            await callback_query.answer(settings.send_test.csv_send_success)
            
        except Exception as e:
            log.exception(e)
            await callback_query.answer(settings.send_test.csv_export_error)
        finally:
            await session.close()


async def get_available_tests(test_type):
    async for session in db_helper.session_getter():
        try:
            if test_type == "regular":
                tests = await session.execute(
                    Test.active()
                    .where(Test.is_psychological == False)
                    .order_by(Test.position.nulls_last(), Test.name)
                )
            elif test_type == "psyco":
                tests = await session.execute(
                    Test.active()
                    .where(Test.is_psychological == True)
                    .order_by(Test.position.nulls_last(), Test.name)
                )
            else:
                return None
            return tests.scalars().all()
        except Exception as e:
            log.exception(e)
        finally:
            await session.close()


async def notify_receiver(bot: Bot, receiver_id, sender_username, test_names):  # TODO: ADD keyboard to this message (( ? ))
    try:
        tests_str = ", ".join(test_names)
        await bot.send_message(
            receiver_id,
            settings.send_test.send_test_notification_reciver + f"{sender_username}: {tests_str}. \n\n" + settings.send_test.send_test_notification_reciver_part_2 
        )
    except Exception as e:
        log.exception("Failed to notify receiver %s: %s", receiver_id, e)


async def save_sent_test(sender_id, test_id, receiver_username):
    async for session in db_helper.session_getter():
        try:
            sender = await session.execute(select(User).where(User.chat_id == sender_id))
            sender = sender.scalar_one_or_none()
            if not sender:
                log.error("Sender with chat_id %s not found", sender_id)
                return None

            test = await session.execute(select(Test).where(Test.id == test_id))
            test = test.scalar_one_or_none()
            if not test:
                log.error("Test with id %s not found", test_id)
                return None
            
            receiver = await session.execute(select(User).where(User.username == receiver_username))
            receiver = receiver.scalar_one_or_none()
            
            sent_test = SentTest(
                sender_id=sender.chat_id,
                sender_username=sender.username,
                test_id=test.id,
                test_name=test.name,
                receiver_id=receiver.chat_id if receiver else None,
                receiver_username=receiver_username,
                status=TestStatus.DELIVERED if receiver else TestStatus.SENT,
                delivered_at=func.now() if receiver else None
            )

            session.add(sent_test)
            await session.commit()
            
            return sent_test
        except Exception as e:
            log.exception("Error in save_sent_test: %s", e)
            await session.rollback()
            return None
        finally:
            await session.close()


async def get_test_names(test_ids):
    async for session in db_helper.session_getter():
        try:
            tests = await session.execute(select(Test).where(Test.id.in_(test_ids)))
            tests = tests.scalars().all()
            return [test.name for test in tests]
        except Exception as e:
            log.exception(e)
        finally:
            await session.close()



async def show_available_tests(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    test_type = data['test_type']
    selected_tests = data.get('selected_tests', [])
    
    tests = await get_available_tests(test_type)
    
    keyboard = []
    for test in tests:
        if str(test.id) not in selected_tests:
            keyboard.append([types.InlineKeyboardButton(text=f"➕ {test.name}", callback_data=f"choose_test_{test.id}")])
    
    keyboard.append([types.InlineKeyboardButton(text=settings.send_test.send_apply_chosen_tests_button, callback_data="confirm_test_selection")])
    keyboard.append([types.InlineKeyboardButton(text=settings.send_test.send_choose_another_tests_type_button, callback_data="back_to_test_type")])
    keyboard.append([types.InlineKeyboardButton(text=settings.send_test.back_to_main_menu_button, callback_data="back_to_start")])
    
    text_service = TextService()
    async for session in db_helper.session_getter():
        text = settings.send_test.choose_another_test
        if selected_tests:
            selected_test_names = await get_test_names(selected_tests)
            text += f"\n\n" + settings.send_test.selected_tests_count + f"{len(selected_tests)}\n" + settings.send_test.selected_tests_list + f"{', '.join(selected_test_names)}"

        media_url = await get_send_test_media_url()
    
    await send_or_edit_message(callback_query.message, text, types.InlineKeyboardMarkup(inline_keyboard=keyboard), media_url)
    await state.set_state(SendTestStates.CHOOSING_TEST)


@router.callback_query(SendTestStates.CHOOSING_TEST_TYPE)
async def process_test_type_choice(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "view_sent_tests":
        await view_sent_tests(callback_query, state)
        return

    # if callback_query.data not in ["choose_regular_tests", "choose_psyco_tests", "confirm_test_selection"]:
    #     await callback_query.answer(settings.send_test.send_tests_error_try_again)
    #     await state.clear()
    #     return

    if callback_query.data == "confirm_test_selection":
        await confirm_test_selection(callback_query, state)
        return

    data = await state.get_data()
    selected_tests = data.get('selected_tests', [])
    test_type = "psyco"  # "regular" if callback_query.data == "choose_regular_tests" else 
    await state.update_data(test_type=test_type, selected_tests=selected_tests)
    
    await show_available_tests(callback_query, state)


@router.callback_query(lambda c: c.data == "send_test")
async def start_send_test(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    log.info("start_send_test handler called")
    keyboard = [
        [types.InlineKeyboardButton(text=settings.send_test.check_sent_tests_button, callback_data="view_sent_tests")],
        [types.InlineKeyboardButton(text=settings.send_test.send_psyco_tests_button, callback_data="choose_psyco_tests")],
        # [types.InlineKeyboardButton(text=settings.send_test.send_other_tests_button, callback_data="choose_regular_tests")],
        [types.InlineKeyboardButton(text=settings.send_test.send_tests_cancel_button, callback_data="back_to_start")]
    ]

    text = settings.send_test.send_tests_choose_type
    media_url = await get_send_test_media_url()
    
    await send_or_edit_message(callback_query.message, text, types.InlineKeyboardMarkup(inline_keyboard=keyboard), media_url)
    await state.set_state(SendTestStates.CHOOSING_TEST_TYPE)


@router.callback_query(lambda c: c.data == "view_sent_tests")
async def view_sent_tests(callback_query: types.CallbackQuery, state: FSMContext):
    sender_id = callback_query.from_user.id
    page = 1
    await state.update_data(current_page=page)
    await show_sent_tests_page(callback_query.message, sender_id, page, state)


async def show_sent_tests_page(message: types.Message, sender_id: int, page: int, state: FSMContext):
    async for session in db_helper.session_getter():
        try:
            # Subquery to get the last date of each user
            subquery = (
                select(SentTest.receiver_username, func.max(SentTest.created_at).label("last_sent"))
                .where(SentTest.sender_id == sender_id)
                .group_by(SentTest.receiver_username)
                .subquery()
            )

            # Main query
            query = (
                select(subquery.c.receiver_username)
                .select_from(subquery)
                .order_by(subquery.c.last_sent.desc())
                .offset((page - 1) * 20)
                .limit(20)
            )

            result = await session.execute(query)
            users = result.scalars().all()

            # Get total number of unique receivers
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
                    row.append(types.InlineKeyboardButton(text=user, callback_data=f"view_user_tests_{user}"))
                keyboard.append(row)

            navigation = []
            if page > 1:
                navigation.append(types.InlineKeyboardButton(text="◀️", callback_data="prev_page"))
            navigation.append(types.InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="current_page"))
            if page < total_pages:
                navigation.append(types.InlineKeyboardButton(text="▶️", callback_data="next_page"))
            if navigation:
                keyboard.append(navigation)

            keyboard.append([types.InlineKeyboardButton(text=settings.send_test.csv_export_all_button, callback_data="export_csv_all")])
            keyboard.append([types.InlineKeyboardButton(text=settings.send_test.csv_export_by_tests_button, callback_data="export_csv_by_test")])
            keyboard.append([types.InlineKeyboardButton(text=settings.send_test.back_button, callback_data="back_to_send_test")])

            text = settings.send_test.sent_tests_user_choose
            media_url = await get_send_test_media_url()

            await send_or_edit_message(message, text, types.InlineKeyboardMarkup(inline_keyboard=keyboard), media_url)
            await state.set_state(SendTestStates.VIEWING_SENT_TESTS)

        except Exception as e:
            log.exception(e)
            await message.answer(settings.send_test.send_tests_users_fetch_error)
        finally:
            await session.close()


@router.callback_query(SendTestStates.VIEWING_SENT_TESTS)
async def process_sent_tests_navigation(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data
    data = await state.get_data()
    current_page = data.get('current_page', 1)

    if action == "prev_page":
        current_page = max(1, current_page - 1)
    elif action == "next_page":
        current_page += 1
    elif action == "current_page":
        callback_query.answer()
        return
    elif action == "back_to_send_test":
        await start_send_test(callback_query, state)
        return
    elif action.startswith("view_user_tests_"):
        parts = action.split("_")
        username = "_".join(parts[3:])
        await view_user_tests(callback_query, username, state)
        return
    elif action == "export_csv_all":
        await export_all_sent_tests_csv(callback_query, state)
        return
    elif action == "export_csv_by_test":
        await show_export_by_test_options(callback_query, state)
        return
    elif action == "back_to_sent_tests":
        await view_sent_tests(callback_query, state)
        return

    # await state.update_data(current_page=current_page)
    # await show_sent_tests_page(callback_query.message, callback_query.from_user.id, current_page, state)


def format_test_info(test):
    status_text = {
        TestStatus.SENT: settings.send_test.test_sent,
        TestStatus.DELIVERED: settings.send_test.test_delivered,
        TestStatus.COMPLETED: settings.send_test.test_completed,
        TestStatus.REJECTED: settings.send_test.test_rejected
    }.get(test.status, settings.send_test.test_unkown_status)

    info = settings.send_test.test_name_repr + f": {test.test_name}\n"
    info += settings.send_test.test_status_repr + f": {status_text}\n"
    info += settings.send_test.test_sent + f": {test.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

    if test.status == TestStatus.DELIVERED:
        info += settings.send_test.test_delivered + f": {test.delivered_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
    elif test.status == TestStatus.COMPLETED:
        info += settings.send_test.test_delivered + f": {test.delivered_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        info += settings.send_test.test_completed + f": {test.completed_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        info += settings.send_test.test_score_result_repr + f": {test.result_score}\n"
        info += settings.send_test.test_text_result_repr + f": {test.result_text}\n"
    elif test.status == TestStatus.REJECTED:
        info += settings.send_test.test_rejected + f": {test.updated_at.strftime('%Y-%m-%d %H:%M:%S')}\n"

    return info + "\n"


def create_navigation_keyboard(current_page, total_pages, username):
    keyboard = []

    navigation = []
    if current_page > 1:
        navigation.append(types.InlineKeyboardButton(text="◀️", callback_data=f"user_tests_page_{current_page-1}_{username}"))
    navigation.append(types.InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="current_page"))
    if current_page < total_pages:
        navigation.append(types.InlineKeyboardButton(text="▶️", callback_data=f"user_tests_page_{current_page+1}_{username}"))
    
    if navigation:
        keyboard.append(navigation)

    keyboard.append([types.InlineKeyboardButton(text=settings.send_test.csv_export_user_button, callback_data=f"export_user_csv_{username}")])
    keyboard.append([types.InlineKeyboardButton(text=settings.send_test.back_to_userlist_button, callback_data="back_to_users_list")])
    keyboard.append([types.InlineKeyboardButton(text=settings.send_test.back_to_main_menu_button, callback_data="back_to_start")])

    return keyboard


async def view_user_tests(callback_query: types.CallbackQuery, username: str, state: FSMContext, page: int = 1):
    sender_id = callback_query.from_user.id
    async for session in db_helper.session_getter():
        try:
            sent_tests = await session.execute(
                select(SentTest)
                .where(SentTest.sender_id == sender_id, SentTest.receiver_username == username)
                .order_by(desc(SentTest.updated_at))
            )
            sent_tests = sent_tests.scalars().all()

            pages = []
            current_page = []
            current_length = 0

            for test in sent_tests:
                test_info = format_test_info(test)
                if current_length + len(test_info) > 800 and current_page:
                    pages.append("\n".join(current_page))
                    current_page = []
                    current_length = 0
                current_page.append(test_info)
                current_length += len(test_info)

            if current_page:
                pages.append("\n".join(current_page))

            if not pages:
                text = settings.send_test.no_sent_tests_from_username + f"{username}"
            else:
                text = settings.send_test.tests_send_to_username + f"{username}:\n\n"
                text += pages[page - 1]

            keyboard = create_navigation_keyboard(page, len(pages), username)

            media_url = await get_send_test_media_url()
            await send_or_edit_message(callback_query.message, text, types.InlineKeyboardMarkup(inline_keyboard=keyboard), media_url)
            await state.set_state(SendTestStates.VIEWING_USER_TESTS)
            await state.update_data(current_username=username, total_pages=len(pages))

        except Exception as e:
            log.exception(e)
        finally:
            await session.close()


@router.callback_query(SendTestStates.VIEWING_USER_TESTS)
async def process_user_tests_navigation(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data
    if action.startswith("user_tests_page_"):
        parts = action.split("_")
        if len(parts) >= 4:
            page = parts[3]
            username = "_".join(parts[4:])  # Обрабатываем случай, когда в username есть подчеркивания
            await view_user_tests(callback_query, username, state, int(page))
    elif action == "current_page":
        await callback_query.answer(settings.send_test.user_results_page_number)
    elif action.startswith("export_user_csv_"):
        username = action.split("_", 3)[-1]
        await export_user_tests_csv(callback_query, username)
    elif action == "back_to_users_list":
        await view_sent_tests(callback_query, state)
    else:
        await callback_query.answer(settings.send_test.send_test_unknown_action)


@router.callback_query(SendTestStates.VIEWING_USER_TESTS)
async def process_user_tests_navigation(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data
    if action == "back_to_users_list":
        await view_sent_tests(callback_query, state)


async def confirm_test_selection(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_tests = data.get('selected_tests', [])
    
    if not selected_tests:
        await callback_query.answer(settings.send_test.no_chosen_tests_to_send)
        return
    
    async for session in db_helper.session_getter():
        tests = await session.execute(select(Test).where(Test.id.in_(selected_tests)))
        tests = tests.scalars().all()
        
        test_names = ", ".join([test.name for test in tests])
        
        text = settings.send_test.tests_chosen_to_send_1 + f":\n\n{test_names}\n\n" + settings.send_test.tests_chosen_to_send_2
        
        media_url = await get_send_test_media_url()
        
        keyboard = [
            [types.InlineKeyboardButton(text=settings.send_test.confirm_send_button, callback_data="confirm_tests")],
            [types.InlineKeyboardButton(text=settings.send_test.back_button, callback_data="back_to_test_selection")]
        ]
        
        await send_or_edit_message(callback_query.message, text, types.InlineKeyboardMarkup(inline_keyboard=keyboard), media_url)
        await state.set_state(SendTestStates.CONFIRMING_TESTS)


@router.callback_query(SendTestStates.CHOOSING_TEST)
async def process_test_choice(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "back_to_test_type":
        await start_send_test(callback_query, state)
        return
    
    if callback_query.data == "confirm_test_selection":
        await confirm_test_selection(callback_query, state)
        return

    if callback_query.data == "back_to_test_selection":
        await show_available_tests(callback_query, state)
        return
    
    if callback_query.data.startswith("add_test_"):
        await add_test(callback_query, state)
        return

    test_id = callback_query.data.split("_")[-1]
    
    async for session in db_helper.session_getter():
        try:
            test = await session.execute(select(Test).where(Test.id == test_id))
            test = test.scalar_one()
            
            text = settings.send_test.send_test_description + f"\n'{test.name}':\n\n{test.description}"
            media_url = test.picture if test.picture else await get_send_test_media_url()
            
            if media_url and not media_url.startswith(('http://', 'https://')):
                media_url = f"{settings.media.base_url}/app/{media_url}"
            
            keyboard = [
                [types.InlineKeyboardButton(text=settings.send_test.send_test_add_test_button, callback_data=f"add_test_{test_id}")],
                [types.InlineKeyboardButton(text=settings.send_test.send_test_back_to_tests_list_button, callback_data="back_to_test_selection")],
                [types.InlineKeyboardButton(text=settings.send_test.cancel_button, callback_data="back_to_start")]
            ]
            
            await send_or_edit_message(
                callback_query.message, 
                text,
                types.InlineKeyboardMarkup(inline_keyboard=keyboard),
                media_url
            )
        
        except Exception as e:
            log.exception(e)
            await callback_query.answer(settings.send_test.send_test_load_info_error)
        finally:
            await session.close()


@router.callback_query(lambda c: c.data and c.data.startswith("add_test_"))
async def add_test(callback_query: types.CallbackQuery, state: FSMContext):
    test_id = callback_query.data.split("_")[-1]
    data = await state.get_data()
    selected_tests = data.get('selected_tests', [])
    
    if test_id not in selected_tests:
        selected_tests.append(test_id)
        await state.update_data(selected_tests=selected_tests)
    
    await callback_query.answer(settings.send_test.send_test_added_to_list)
    await show_available_tests(callback_query, state)


@router.callback_query(SendTestStates.CONFIRMING_TESTS)
async def process_confirm_tests(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data == "back_to_test_selection":
        await show_available_tests(callback_query, state)
        return
    
    if callback_query.data == "confirm_tests":
        text = settings.send_test.send_test_enter_username
        keyboard = [
            [types.InlineKeyboardButton(text=settings.send_test.cancel_button, callback_data="back_to_start")],
        ]

        media_url = await get_send_test_media_url()
        
        await send_or_edit_message(callback_query.message, text, types.InlineKeyboardMarkup(inline_keyboard=keyboard), media_url)
        await state.set_state(SendTestStates.ENTERING_RECEIVER)


@router.message(SendTestStates.ENTERING_RECEIVER)
async def process_receiver_input(message: types.Message, state: FSMContext):
    receiver_username = message.text.strip().lstrip('@')
    data = await state.get_data()
    selected_tests = data.get('selected_tests', [])
    
    if not selected_tests:
        await message.answer(settings.send_test.send_test_error_no_tests_selected)
        await state.clear()
        return
    
    if receiver_username == message.from_user.username:
        await message.answer(settings.send_test.send_test_error_send_youself)
        return
    
    async for session in db_helper.session_getter():
        try:
            tests = await session.execute(select(Test).where(Test.id.in_(selected_tests)))
            tests = tests.scalars().all()
            
            receiver = await session.execute(select(User).where(User.username == receiver_username))
            receiver = receiver.scalar_one_or_none()
            
            receiver_status = settings.send_test.send_test_reciver_authenticated if receiver else settings.send_test.send_test_reciver_not_authenticated
            
            # Check if sent and uncompleted tests already exist
            sender_id = message.from_user.id
            sent_tests = await session.execute(
                select(SentTest).where(
                    SentTest.sender_id == sender_id,
                    SentTest.receiver_username == receiver_username,
                    SentTest.test_id.in_(selected_tests),
                    SentTest.status.in_([TestStatus.SENT, TestStatus.DELIVERED])
                )
            )
            sent_tests = sent_tests.scalars().all()
            
            skipped_tests = [test.test_name for test in sent_tests]
            selected_tests = [str(test.id) for test in tests if test.id not in [sent.test_id for sent in sent_tests]]
            
            if not selected_tests:
                text = (settings.send_test.send_test_all_chosen_tests_uncomplete + "\n\n" + settings.send_test.send_test_all_chosen_tests_uncomplete_2)
                keyboard = [
                    [types.InlineKeyboardButton(text=settings.send_test.send_test_return_to_test_choose_button, callback_data="back_to_test_selection")],
                    [types.InlineKeyboardButton(text=settings.send_test.back_to_main_menu_button, callback_data="back_to_start")]
                ]
                await send_or_edit_message(message, text, types.InlineKeyboardMarkup(inline_keyboard=keyboard))
                await state.clear()
                return
            
            test_names = ", ".join([test.name for test in tests if str(test.id) in selected_tests])
            
            keyboard = [
                [types.InlineKeyboardButton(text=settings.send_test.button_accept, callback_data="confirm_send_tests")],
                [types.InlineKeyboardButton(text=settings.send_test.cancel_button, callback_data="back_to_start")]
            ]
            
            text = settings.send_test.send_test_last_confirm + f"{receiver_username}:\n\n{test_names}\n\n" + settings.send_test.send_test_last_confirm_2 + f"{receiver_status}" + settings.send_test.send_test_last_confirm_3 + "\n"
            
            if skipped_tests:
                text += "\n" + settings.send_test.send_test_last_confirm_sent_before + f": \n{', '.join(skipped_tests)}.\n" + settings.send_test.send_test_last_confirm_sent_before_2
            text += "\n" + settings.send_test.send_test_last_confirm_accept
            
            media_url = await get_send_test_media_url()
            
            if media_url and not media_url.startswith(('http://', 'https://')):
                media_url = f"{settings.media.base_url}/app/{media_url}"
            
            await send_or_edit_message(message, text, types.InlineKeyboardMarkup(inline_keyboard=keyboard), media_url)
            await state.set_state(SendTestStates.CONFIRMING)
            await state.update_data(receiver_username=receiver_username, selected_tests=selected_tests)
        
        except Exception as e:
            log.exception(e)
            await message.answer(settings.send_test.send_test_last_confirm_error)
            await state.clear()
        finally:
            await session.close()


@router.callback_query(SendTestStates.CONFIRMING)
async def confirm_send_tests(callback_query: types.CallbackQuery, state: FSMContext):
    if callback_query.data != "confirm_send_tests":
        await callback_query.answer(settings.send_test.send_test_confirm_error)
        return

    data = await state.get_data()
    sender_id = callback_query.from_user.id
    selected_tests = data.get('selected_tests')
    receiver_username = data.get('receiver_username')

    if not all([sender_id, selected_tests, receiver_username]):
        await callback_query.answer(settings.send_test.send_test_confirm_error_not_enough_data)
        await state.clear()
        return

    sent_tests = []
    test_names = []
    async for session in db_helper.session_getter():
        try:
            for test_id in selected_tests:
                sent_test = await save_sent_test(sender_id, test_id, receiver_username)
                if sent_test:
                    sent_tests.append(sent_test)
                    test_names.append(sent_test.test_name)
            
            sender = await session.execute(select(User).where(User.chat_id == sender_id))
            sender = sender.scalar_one()
        except Exception as e:
            log.exception("Error in confirm_send_tests: %s", e)
        finally:
            await session.close()

    if not sent_tests:
        await callback_query.answer(settings.send_test.send_test_confirm_different_error)
        await state.clear()
        return

    receiver_id = sent_tests[0].receiver_id if sent_tests[0].receiver_id else None
    if receiver_id:
        await notify_receiver(callback_query.bot, receiver_id, sender.username, test_names)
        text = settings.send_test.tests_sent_success + f"{receiver_username} " + settings.send_test.tests_sent_success_2
    else:
        text = (settings.send_test.tests_sent_unsuccess + f"{receiver_username}.\n" + settings.send_test.tests_sent_unsuccess_2)

    media_url = await get_send_test_media_url()

    keyboard = [
        [types.InlineKeyboardButton(text=settings.send_test.back_to_main_menu_button, callback_data="back_to_start")]
    ]
    
    await send_or_edit_message(callback_query.message, text, types.InlineKeyboardMarkup(inline_keyboard=keyboard), media_url)
    await state.clear()


@router.callback_query(lambda c: c.data and c.data.startswith(("choose_", "confirm_", "back_to_")))
async def process_send_test_callback(callback_query: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()

    if current_state == SendTestStates.CHOOSING_TEST_TYPE:
        await process_test_type_choice(callback_query, state)
    elif current_state == SendTestStates.CHOOSING_TEST:
        if callback_query.data == "back_to_test_type":
            await start_send_test(callback_query, state)
        elif callback_query.data == "confirm_test_selection":
            await confirm_test_selection(callback_query, state)
        else:
            await process_test_choice(callback_query, state)
    elif current_state == SendTestStates.CONFIRMING_TESTS:
        await process_confirm_tests(callback_query, state)
    elif current_state == SendTestStates.CONFIRMING:
        await confirm_send_tests(callback_query, state)
    # else:
    #     await callback_query.answer(settings.send_test.send_tests_error_try_again)
    #     await state.clear()
    #     await start_send_test(callback_query, state)
