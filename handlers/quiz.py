# handlers/quiz.py

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import func, select
from sqlalchemy.sql.expression import and_
import random
from collections import defaultdict

from core.models import Test, Question, QuizResult, User, Result
from core.models import db_helper
from core import log, settings
from services.text_service import TextService
from services.button_service import ButtonService
from handlers.utils import send_or_edit_message

from services.decorators import handle_as_task, TaskPriority


router = Router()


class BaseQuizStates(StatesGroup):
    VIEWING_INTRO = State()
    ANSWERING = State()
    SHOWING_COMMENT = State()


class QuizStates(BaseQuizStates):
    VIEWING_TESTS = State()
    CONFIRMING = State()


@router.callback_query(F.data == "show_psycho_tests")
@handle_as_task(priority=TaskPriority.NORMAL)
async def show_psycho_tests(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.clear()  # Clear the state before showing the list of psycological tests

    # Check if the menu opened with direct message (not the group chat)
    str_chat_id = str(callback_query.message.chat.id)
    if str_chat_id.startswith("-"):
        text = "Нельзя пройти тесты в групповом чате. Вы можете сделать это внутри личной переписки с ботом."
        await callback_query.message.answer(text)
        return

    async with db_helper.db_session() as session:
        try:

            tests = await session.execute(
                Test.active()
                .where(Test.is_psychological == True)
                .order_by(Test.position.nulls_last(), Test.name)
            )  # Only psycological tests
            tests = tests.scalars().all()

            keyboard = []
            for test in tests:
                keyboard.append(
                    [
                        types.InlineKeyboardButton(
                            text=test.name, callback_data=f"start_quiz_{test.id}"
                        )
                    ]
                )

            button_service = ButtonService()
            custom_buttons = await button_service.get_buttons_by_marker(
                "show_psycho_tests", session
            )
            for button in custom_buttons:
                if button.url:
                    keyboard.append(
                        [types.InlineKeyboardButton(text=button.text, url=button.url)]
                    )
                elif button.callback_data:
                    keyboard.append(
                        [
                            types.InlineKeyboardButton(
                                text=button.text, callback_data=button.callback_data
                            )
                        ]
                    )

            keyboard.append(
                [
                    types.InlineKeyboardButton(
                        text=settings.quiz_text.quiz_back_to_start,
                        callback_data="back_to_start",
                    )
                ]
            )

            reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

            text_service = TextService()
            content = await text_service.get_text_with_media(
                "show_psycho_tests", session
            )
            text = (
                content["text"]
                if content
                else settings.quiz_text.psycological_rests_list_menu
            )
            media_url = (
                content["media_urls"][0]
                if content and content["media_urls"]
                else await text_service.get_default_media(session)
            )

            if media_url and not media_url.startswith(("http://", "https://")):
                media_url = f"{settings.media.base_url}/app/{media_url}"

            await send_or_edit_message(
                callback_query.message, text, reply_markup, media_url
            )
            await state.set_state(QuizStates.VIEWING_TESTS)

        except Exception as e:
            log.exception(e)


@router.callback_query(F.data == "show_quizzes")
@handle_as_task(priority=TaskPriority.NORMAL)
async def show_quizzes(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await state.clear()  # Clear the state before showing the list of tests

    # Check if the menu opened with direct message (not the group chat)
    str_chat_id = str(callback_query.message.chat.id)
    if str_chat_id.startswith("-"):
        text = "Нельзя пройти тесты в групповом чате. Вы можете сделать это внутри личной переписки с ботом."
        await callback_query.message.answer(text)
        return

    async with db_helper.db_session() as session:
        try:
            tests = await session.execute(
                Test.active()
                .where(Test.is_psychological == False)
                .order_by(Test.position.nulls_last(), Test.name)
            )  # Only non psycological tests
            tests = tests.scalars().all()

            keyboard = []
            for test in tests:
                keyboard.append(
                    [
                        types.InlineKeyboardButton(
                            text=test.name, callback_data=f"start_quiz_{test.id}"
                        )
                    ]
                )

            button_service = ButtonService()
            custom_buttons = await button_service.get_buttons_by_marker(
                "show_quizzes", session
            )
            for button in custom_buttons:
                if button.url:
                    keyboard.append(
                        [types.InlineKeyboardButton(text=button.text, url=button.url)]
                    )
                elif button.callback_data:
                    keyboard.append(
                        [
                            types.InlineKeyboardButton(
                                text=button.text, callback_data=button.callback_data
                            )
                        ]
                    )

            keyboard.append(
                [
                    types.InlineKeyboardButton(
                        text=settings.quiz_text.quiz_back_to_start,
                        callback_data="back_to_start",
                    )
                ]
            )

            reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

            text_service = TextService()
            content = await text_service.get_text_with_media("show_quizzes", session)
            text = content["text"] if content else settings.quiz_text.quizes_list_menu
            media_url = (
                content["media_urls"][0]
                if content and content["media_urls"]
                else await text_service.get_default_media(session)
            )

            if media_url and not media_url.startswith(("http://", "https://")):
                media_url = f"{settings.media.base_url}/app/{media_url}"

            await send_or_edit_message(
                callback_query.message, text, reply_markup, media_url
            )
            await state.set_state(QuizStates.VIEWING_TESTS)

        except Exception as e:
            log.exception(e)


# @router.callback_query(lambda c: c.data and c.data.startswith("start_quiz_"))
# async def start_quiz(callback_query: types.CallbackQuery, state: FSMContext):
#     await state.clear()
#     quiz_id = callback_query.data.split("_")[-1]

#     async with db_helper.db_session() as session:
#         try:
#             test = await session.execute(select(Test).where(Test.id == quiz_id))
#             test = test.scalar_one_or_none()

#             if not test:
#                 await callback_query.answer(settings.quiz_text.quiz_not_found)
#                 return

#             user = await session.execute(
#                 select(User).where(User.chat_id == callback_query.from_user.id)
#             )
#             user = user.scalar_one_or_none()

#             if not user:
#                 await callback_query.answer(settings.quiz_text.user_not_found)
#                 return

#             # Check if user's result already exists and pick the latest one
#             latest_results = await session.execute(
#                 select(QuizResult)
#                 .where(QuizResult.user_id == user.id, QuizResult.test_id == test.id)
#                 .order_by(QuizResult.created_at.desc())
#                 .limit(1)
#             )
#             latest_result = latest_results.scalar_one_or_none()

#             has_passed_test = False
#             if not test.allow_play_again:
#                 # Check if the user has already played the test
#                 result_count = await session.execute(
#                     select(func.count())
#                     .select_from(QuizResult)
#                     .where(QuizResult.user_id == user.id, QuizResult.test_id == test.id)
#                 )
#                 has_passed_test = result_count.scalar() > 0

#             if test.is_psychological:
#                 keyboard = types.InlineKeyboardMarkup(
#                     inline_keyboard=[
#                         [
#                             types.InlineKeyboardButton(
#                                 text=settings.quiz_text.psycological_menu_button_for_end_quiz,
#                                 callback_data="show_psycho_tests",
#                             )
#                         ],
#                     ]
#                 )
#             else:
#                 keyboard = types.InlineKeyboardMarkup(
#                     inline_keyboard=[
#                         [
#                             types.InlineKeyboardButton(
#                                 text=settings.quiz_text.quiz_list_menu_button_for_end_quiz,
#                                 callback_data="show_quizzes",
#                             )
#                         ],
#                     ]
#                 )

#             if latest_result:

#                 await state.update_data(latest_result=latest_result)
#                 # await state.update_data(quiz_id=quiz_id)

#                 keyboard.inline_keyboard.append(
#                     [
#                         types.InlineKeyboardButton(
#                             text="💾 Посмотреть результат",
#                             callback_data="check_existing_test_result",
#                         )
#                     ]
#                 )

#             keyboard.inline_keyboard.append(
#                 [
#                     types.InlineKeyboardButton(
#                         text=settings.quiz_text.quiz_back_to_start,
#                         callback_data="back_to_start",
#                     )
#                 ]
#             )

#             # TODO: Add old result check if has passed the test and the result exists

#             if not has_passed_test:
#                 keyboard.inline_keyboard.insert(
#                     0,
#                     [
#                         types.InlineKeyboardButton(
#                             text=settings.quiz_text.quiz_start_approve,
#                             callback_data=f"confirm_start_{quiz_id}",
#                         )
#                     ],
#                 )

#             text_service = TextService()
#             media_url = (
#                 test.picture
#                 if test.picture
#                 else await text_service.get_default_media(session)
#             )
#             if media_url and not media_url.startswith(("http://", "https://")):
#                 media_url = f"{settings.media.base_url}/app/{media_url}"

#             log.info("Generated media URL: %s", media_url)

#             description = f"<b>{test.name}</b>\n\n"
#             if has_passed_test:
#                 description += settings.quiz_text.forbidden_to_play_again_quiz_text

#             if not has_passed_test:
#                 description += test.description.replace("\\n", "\n")

#             await send_or_edit_message(
#                 callback_query.message, description, keyboard, media_url
#             )

#             if not has_passed_test:
#                 await state.set_state(QuizStates.CONFIRMING)
#                 await state.update_data(quiz_id=quiz_id)
#             else:
#                 await state.clear()

#         except Exception as e:
#             log.exception(e)


async def start_quiz(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    quiz_id = callback_query.data.split("_")[-1]
    tg_user_id = callback_query.from_user.id

    async with db_helper.db_session() as session:
        try:
            # Подзапрос на последний QuizResult для конкретного теста
            latest_result_subquery = (
                select(
                    QuizResult.id.label("lr_id"),
                    QuizResult.user_id.label("lr_user_id"),
                    QuizResult.test_id.label("lr_test_id"),
                    QuizResult.is_psychological.label("lr_is_psychological"),
                    QuizResult.category_id.label("lr_category_id"),
                    QuizResult.score.label("lr_score"),
                    QuizResult.result_text.label("lr_result_text"),
                    QuizResult.is_active.label("lr_is_active"),
                    QuizResult.updated_at.label("lr_updated_at"),
                    QuizResult.created_at.label("lr_created_at"),
                )
                .where(
                    and_(
                        QuizResult.user_id == User.id,
                        QuizResult.test_id
                        == quiz_id,  # Теперь фильтруем по конкретному тесту
                    )
                )
                .order_by(QuizResult.created_at.desc())
                .limit(1)
            ).subquery("latest_result")

            # Подзапрос на количество результатов для конкретного теста
            result_count_subquery = (
                select(func.count().label("count"))
                .select_from(QuizResult)
                .where(
                    and_(
                        QuizResult.user_id == User.id,
                        QuizResult.test_id == quiz_id,  # Фильтруем по конкретному тесту
                    )
                )
            ).scalar_subquery()

            # Основной запрос
            query = (
                select(
                    Test.id.label("test_id"),
                    Test.name.label("test_name"),
                    Test.description.label("test_description"),
                    Test.picture.label("test_picture"),
                    Test.is_psychological.label("test_is_psychological"),
                    Test.allow_play_again.label("test_allow_play_again"),
                    User.id.label("user_id"),
                    latest_result_subquery.c.lr_id,
                    latest_result_subquery.c.lr_is_psychological,
                    latest_result_subquery.c.lr_category_id,
                    latest_result_subquery.c.lr_score,
                    latest_result_subquery.c.lr_result_text,
                    latest_result_subquery.c.lr_is_active,
                    latest_result_subquery.c.lr_updated_at,
                    latest_result_subquery.c.lr_created_at,
                    result_count_subquery.label("result_count"),
                )
                .select_from(Test)
                .join(User, User.chat_id == tg_user_id, isouter=True)
                .outerjoin(
                    latest_result_subquery,
                    User.id == latest_result_subquery.c.lr_user_id,
                )
                .where(Test.id == quiz_id)
            )

            # Выполняем запрос и получаем результат
            result = await session.execute(query)
            row = result.mappings().first()

            if not row:
                await callback_query.answer(settings.quiz_text.quiz_not_found)
                return

            test_data = {
                "id": row["test_id"],
                "name": row["test_name"],
                "description": row["test_description"],
                "picture": row["test_picture"],
                "is_psychological": row["test_is_psychological"],
                "allow_play_again": row["test_allow_play_again"],
            }

            db_user_id = row["user_id"]
            result_count = row["result_count"] or 0

            latest_result = None
            if row["lr_id"] is not None:
                latest_result = {
                    "id": row["lr_id"],
                    "is_psychological": row["lr_is_psychological"],
                    "category_id": row["lr_category_id"],
                    "score": row["lr_score"],
                    "result_text": row["lr_result_text"],
                    "is_active": row["lr_is_active"],
                    "updated_at": row["lr_updated_at"],
                    "created_at": row["lr_created_at"],
                }

            if not db_user_id:
                await callback_query.answer(settings.quiz_text.user_not_found)
                return

            has_passed_test = False
            if not test_data["allow_play_again"]:
                has_passed_test = result_count > 0

            if test_data["is_psychological"]:
                keyboard = types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text=settings.quiz_text.psycological_menu_button_for_end_quiz,
                                callback_data="show_psycho_tests",
                            )
                        ],
                    ]
                )
            else:
                keyboard = types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text=settings.quiz_text.quiz_list_menu_button_for_end_quiz,
                                callback_data="show_quizzes",
                            )
                        ],
                    ]
                )

            if latest_result:
                await state.update_data(latest_result=latest_result)
                keyboard.inline_keyboard.append(
                    [
                        types.InlineKeyboardButton(
                            text="💾 Посмотреть результат",
                            callback_data="check_existing_test_result",
                        )
                    ]
                )

            keyboard.inline_keyboard.append(
                [
                    types.InlineKeyboardButton(
                        text=settings.quiz_text.quiz_back_to_start,
                        callback_data="back_to_start",
                    )
                ]
            )

            if not has_passed_test:
                keyboard.inline_keyboard.insert(
                    0,
                    [
                        types.InlineKeyboardButton(
                            text=settings.quiz_text.quiz_start_approve,
                            callback_data=f"confirm_start_{quiz_id}",
                        )
                    ],
                )

            text_service = TextService()
            media_url = (
                test_data["picture"]
                if test_data["picture"]
                else await text_service.get_default_media(session)
            )
            if media_url and not media_url.startswith(("http://", "https://")):
                media_url = f"{settings.media.base_url}/app/{media_url}"

            log.info("Generated media URL: %s", media_url)

            description = f"<b>{test_data['name']}</b>\n\n"
            if has_passed_test:
                description += settings.quiz_text.forbidden_to_play_again_quiz_text
            else:
                description += test_data["description"].replace("\\n", "\n")

            await send_or_edit_message(
                callback_query.message, description, keyboard, media_url
            )

            if not has_passed_test:
                await state.set_state(QuizStates.CONFIRMING)
                await state.update_data(quiz_id=quiz_id)
            else:
                await state.clear()

        except Exception as e:
            log.exception(e)


@router.callback_query(F.data == "check_existing_test_result")
async def check_existing_test_result(
    callback_query: types.CallbackQuery, state: FSMContext
):
    await callback_query.answer()
    data = await state.get_data()
    latest_result = data["latest_result"]
    # quiz_id = data["quiz_id"]

    # media_url = None  # TODO: Add media

    text = "Ваш результат:\n\n"
    text += latest_result["result_text"]

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text="⬅️ Назад к тесту",
                    callback_data="destroy_latest_result_message",
                ),
                types.InlineKeyboardButton(
                    text="🏠 Назад в меню",
                    callback_data="back_to_start",
                ),
            ],
        ]
    )

    await callback_query.message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "destroy_latest_result_message")
async def destroy_latest_result_message(
    callback_query: types.CallbackQuery, state: FSMContext
):
    await callback_query.answer("Очистка сообщения...")
    await callback_query.message.delete()


async def get_sorted_questions(session, test_id):
    """Get questions sorted by order and category."""
    questions = await session.execute(
        Question.active().where(Question.test_id == test_id).order_by(Question.order)
    )
    questions = questions.scalars().all()

    # Group questions by order
    questions_by_order = defaultdict(list)
    for question in questions:
        # Create a copy of the question with its data
        question_data = {
            "question": question,
            "intro_text": question.intro_text,
            "comment": question.comment,
            "picture": question.picture,
            "order": question.order,
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


# @router.callback_query(QuizStates.VIEWING_INTRO)
async def process_intro(
    callback_query: types.CallbackQuery, state: FSMContext, state_group: StatesGroup
):
    if callback_query.data == "show_question":
        data = await state.get_data()
        data["intro_shown"] = True
        await state.update_data(data)
        await send_question(callback_query.message, state, state_group)


# @router.callback_query(lambda c: c.data and c.data.startswith("confirm_start_"))
async def confirm_start_quiz(
    callback_query: types.CallbackQuery,
    state: FSMContext,
    state_group: StatesGroup,
    quiz_id: str = None,
):
    if not quiz_id:  # If called from callback
        quiz_id = callback_query.data.split("_")[-1]
    async with db_helper.db_session() as session:
        try:
            # Get and save the order of questions at start
            sorted_questions = await get_sorted_questions(session, quiz_id)
            await state.update_data(
                quiz_id=quiz_id,
                current_question=0,
                answers=[],
                category_scores={},
                intro_shown=False,
                sorted_questions=sorted_questions,  # Save the order
            )
            await send_question(callback_query.message, state, state_group)
        except Exception as e:
            log.exception(e)


# @router.callback_query(lambda c: c.data and c.data.startswith("start_questions_"))
async def start_questions(
    callback_query: types.CallbackQuery,
    state: FSMContext,
    state_group: StatesGroup,
    quiz_id: str = None,
):
    if not quiz_id:  # If called from callback
        quiz_id = callback_query.data.split("_")[-1]
    await send_question(
        callback_query.message,
        state,
        state_group,
    )


async def send_question(
    message: types.Message, state: FSMContext, state_group: StatesGroup
):
    data = await state.get_data()
    quiz_id = data["quiz_id"]
    current_question = data["current_question"]
    sorted_questions = data["sorted_questions"]

    async with db_helper.db_session() as session:
        try:
            test = await session.execute(select(Test).where(Test.id == quiz_id))
            test = test.scalar_one_or_none()

            if current_question >= len(sorted_questions):
                await finish_quiz(message, state)
                return

            question_data = sorted_questions[current_question]
            question = question_data["question"]  # Get the question object

            # Check if there is an intro text for the current question
            if question_data["intro_text"] and not data.get("intro_shown"):
                keyboard = types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text=settings.quiz_text.quiz_continue_button,
                                callback_data="show_question",
                            )
                        ]
                    ]
                )

                text_service = TextService()
                # Media priority
                if question_data["picture"]:
                    media_url = question_data["picture"]
                elif test.picture:
                    media_url = test.picture
                else:
                    media_url = await text_service.get_default_media(session)

                if media_url and not media_url.startswith(("http://", "https://")):
                    media_url = f"{settings.media.base_url}/app/{media_url}"

                intro_text = question_data["intro_text"].replace("\\n", "\n")

                await send_or_edit_message(message, intro_text, keyboard, media_url)

                data["intro_shown"] = True
                await state.update_data(data)
                await state.set_state(state_group.VIEWING_INTRO)
                return

            # If there is no intro or it has already been shown, show the question
            keyboard = []
            for i in range(1, 7):
                answer_text = getattr(
                    question, f"answer{i}_text"
                )  # Use the question object to get the answers
                if answer_text:
                    keyboard.append(
                        [
                            types.InlineKeyboardButton(
                                text=answer_text,
                                callback_data=f"answer_{current_question}_{i}",
                            )
                        ]
                    )

            if test.allow_back and current_question > 0:
                keyboard.append(
                    [
                        types.InlineKeyboardButton(
                            text=settings.quiz_text.quiz_question_previous_button,
                            callback_data="quiz_back",
                        )
                    ]
                )

            reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)

            text_service = TextService()

            if question_data["picture"]:
                media_url = question_data["picture"]
            elif test.picture:
                media_url = test.picture
            else:
                media_url = await text_service.get_default_media(session)

            if media_url and not media_url.startswith(("http://", "https://")):
                media_url = f"{settings.media.base_url}/app/{media_url}"

            log.info("Generated media URL for question: %s", media_url)

            question_text = (
                settings.quiz_text.question_text_begging_1
                + f"{current_question + 1}"
                + settings.quiz_text.question_text_begging_2
                + f"{len(sorted_questions)}:\n\n{question.question_text.replace('\\n', '\n')}"
            )

            await send_or_edit_message(message, question_text, reply_markup, media_url)

            data["intro_shown"] = False  # Drop the flag for the next question
            await state.update_data(data)
            await state.set_state(state_group.ANSWERING)

        except Exception as e:
            log.exception(e)


# @router.callback_query(QuizStates.ANSWERING)
async def process_answer(
    callback_query: types.CallbackQuery, state: FSMContext, state_group: StatesGroup
):
    data = await state.get_data()
    sorted_questions = data["sorted_questions"]

    if callback_query.data == "quiz_back":
        if data["current_question"] > 0:
            data["current_question"] -= 1
            if data["answers"]:
                last_answer = data["answers"].pop()
                # Remove from category scores if needed
                if data.get("category_scores"):  # Check if there is a dictionary
                    data["category_scores"][last_answer] = (
                        data["category_scores"].get(last_answer, 1) - 1
                    )
                    if data["category_scores"][last_answer] <= 0:
                        del data["category_scores"][last_answer]
            await state.update_data(data)
            await send_question(callback_query.message, state, state_group)
        return

    question_num, answer_num = map(int, callback_query.data.split("_")[1:])

    async with db_helper.db_session() as session:
        try:
            question_data = sorted_questions[question_num]
            question = question_data["question"]  # Get the question object

            test = await session.execute(select(Test).where(Test.id == data["quiz_id"]))
            test = test.scalar_one()

            score = getattr(question, f"answer{answer_num}_score")
            data["answers"].append(score)

            # Update category scores if this is a multi-graph test
            if test.multi_graph_results:
                if "category_scores" not in data:
                    data["category_scores"] = {}
                # Use score as an identifier of the category and count the number of answers
                data["category_scores"][score] = (
                    data["category_scores"].get(score, 0) + 1
                )

            await state.update_data(data)

            if question_data["comment"]:
                await show_comment(
                    callback_query.message, question_data["comment"], state, state_group
                )
            else:
                data["current_question"] += 1
                await state.update_data(data)
                await send_question(callback_query.message, state, state_group)

        except Exception as e:
            log.exception(e)


async def show_comment(
    callback_query: types.CallbackQuery,
    comment: str,
    state: FSMContext,
    state_group: StatesGroup,
):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=settings.quiz_text.quiz_continue_button,
                    callback_data="continue_quiz",
                )
            ]
        ]
    )

    data = await state.get_data()
    async with db_helper.db_session() as session:
        try:
            questions = await get_sorted_questions(session, data["quiz_id"])
            question = questions[data["current_question"]][
                "question"
            ]  # Get the question
            comment = questions[data["current_question"]]["comment"]  # Get the comment

            test = await session.execute(select(Test).where(Test.id == data["quiz_id"]))
            test = test.scalar_one()

            text_service = TextService()

            # Priority: question -> test -> default media
            if question.picture:
                media_url = question.picture
            elif test.picture:
                media_url = test.picture
            else:
                media_url = await text_service.get_default_media(session)

            if media_url and not media_url.startswith(("http://", "https://")):
                media_url = f"{settings.media.base_url}/app/{media_url}"

            comment_text = (
                settings.quiz_text.question_comment_header
                + f"\n\n{comment.replace('\\n', '\n')}"
            )

            await send_or_edit_message(
                callback_query, comment_text, keyboard, media_url
            )
        except Exception as e:
            log.exception(e)

    await state.set_state(state_group.SHOWING_COMMENT)


# @router.callback_query(QuizStates.SHOWING_COMMENT)
async def process_comment(
    callback_query: types.CallbackQuery, state: FSMContext, state_group: StatesGroup
):
    data = await state.get_data()
    data["current_question"] += 1
    await state.update_data(data)
    await send_question(callback_query.message, state, state_group)


async def calculate_results(session, test, total_scores, category_scores):
    """Calculate results based on test type and scoring method."""
    if test.multi_graph_results:
        final_results = []
        # Get all distinct category IDs
        all_categories = await session.execute(
            select(Result.category_id)
            .distinct()
            .where(Result.test_id == test.id)
            .where(Result.category_id.isnot(None))
        )
        all_categories = [cat[0] for cat in all_categories.fetchall()]

        # Process each category including 0 score
        for category_id in all_categories:
            count = category_scores.get(
                category_id, 0
            )  # If category not found, set score to 0
            results = await session.execute(
                select(Result).where(
                    Result.test_id == test.id,
                    Result.category_id == category_id,
                    Result.min_score <= count,
                    Result.max_score >= count,
                )
            )
            category_result = results.scalar_one_or_none()
            if category_result:
                final_results.append(
                    {
                        "category_id": category_id,
                        "category_name": test.get_category_name(category_id),
                        "score": count,
                        "text": category_result.text,
                        "picture": category_result.picture,
                    }
                )

        # Sort results by score in descending order
        final_results.sort(key=lambda x: x["score"], reverse=True)
        return final_results

    else:
        # For traditional single-result tests
        results = await session.execute(
            select(Result).where(
                Result.test_id == test.id,
                Result.category_id.is_(
                    None
                ),  # Regular results without categories for regular non multi-graph tests
                Result.min_score <= total_scores,
                Result.max_score >= total_scores,
            )
        )
        result = results.scalar_one_or_none()
        return [
            {
                "score": total_scores,
                "text": (
                    result.text
                    if result
                    else settings.quiz_text.quiz_result_error_undefined
                ),
                "picture": result.picture if result else None,
            }
        ]


async def finish_quiz(message: types.Message, state: FSMContext):
    data = await state.get_data()
    quiz_id = data["quiz_id"]
    total_score = sum(data["answers"])
    category_scores = data.get("category_scores", {})

    chat_id = message.chat.id

    # print("-----------------" * 4)
    # print(f"chat_id: {chat_id}")

    async with db_helper.db_session() as session:
        try:
            test = await session.execute(select(Test).where(Test.id == quiz_id))
            test = test.scalar_one()

            user = await session.execute(select(User).where(User.chat_id == chat_id))
            user = user.scalar_one()

            # Calculate results
            results = await calculate_results(
                session, test, total_score, category_scores
            )

            # Save results
            for result in results:
                quiz_result = QuizResult(
                    user_id=user.id,
                    test_id=test.id,
                    score=result.get("score", 0),
                    category_id=result.get("category_id"),
                    is_psychological=test.is_psychological,
                    result_text=result["text"],
                )
                session.add(quiz_result)
            await session.commit()

            # Prepare result message and media
            if test.multi_graph_results:
                result_message = settings.quiz_text.quiz_multi_result + "\n\n"
                for result in results:
                    result_message += f"{result['category_name']}: {result['score']}\n{result['text']}\n\n"
            else:
                result_message = (
                    settings.quiz_text.quiz_result
                    + f"{total_score}\n\n{results[0]['text']}"
                )

            # Prepare keyboard based on test type
            if test.is_psychological:
                keyboard = types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text=settings.quiz_text.psycological_menu_button_for_end_quiz,
                                callback_data="show_psycho_tests",
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text=settings.quiz_text.quiz_back_to_start,
                                callback_data="back_to_start",
                            )
                        ],
                    ]
                )
            else:
                keyboard = types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text=settings.quiz_text.quiz_list_menu_button_for_end_quiz,
                                callback_data="show_quizzes",
                            )
                        ],
                        [
                            types.InlineKeyboardButton(
                                text=settings.quiz_text.quiz_back_to_start,
                                callback_data="back_to_start",
                            )
                        ],
                    ]
                )

            # Get appropriate media URL
            text_service = TextService()
            media_url = (
                (results[0].get("picture") if results else None)
                or test.picture
                or await text_service.get_default_media(session)
            )

            if media_url and not media_url.startswith(("http://", "https://")):
                media_url = f"{settings.media.base_url}/app/{media_url}"

            await send_or_edit_message(message, result_message, keyboard, media_url)

        except Exception as e:
            log.exception(e)
        finally:
            await state.clear()


@router.callback_query(
    F.data.startswith(
        (
            "show_quizzes",
            "start_quiz_",
            "confirm_start_",
            "start_questions_",
            "answer_",
            "quiz_back",
            "continue_quiz",
            "show_question",
        )
    )
)
@handle_as_task(priority=TaskPriority.NORMAL)
async def process_quiz_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    current_state = await state.get_state()
    if current_state is None:
        await show_psycho_tests(
            callback_query, state
        )  # TODO: Showing psycological tests now, DOUBLE CHECK (( ! ))

    elif current_state == QuizStates.VIEWING_TESTS:
        if callback_query.data.startswith("start_quiz_"):
            await start_quiz(callback_query, state)
        # else:
        #     await show_quizzes(callback_query, state)  # TODO: Double check (( ! ))

    elif current_state == QuizStates.VIEWING_INTRO:
        await process_intro(callback_query, state, QuizStates)

    elif current_state == QuizStates.CONFIRMING:
        if callback_query.data.startswith("confirm_start_"):
            await confirm_start_quiz(callback_query, state, QuizStates)
        # else:
        #     await show_quizzes(callback_query, state)  # TODO: Double check (( ! ))

    elif current_state == QuizStates.VIEWING_INTRO:
        if callback_query.data.startswith("start_questions_"):
            await start_questions(callback_query, state, QuizStates)

    elif current_state == QuizStates.ANSWERING:
        await process_answer(callback_query, state, QuizStates)

    elif current_state == QuizStates.SHOWING_COMMENT:
        await process_comment(callback_query, state, QuizStates)

    # else:
    # await callback_query.answer(settings.quiz_text.quiz_error)  # TODO: Fix to show psycological tests
    #     await state.clear()
    #     await show_quizzes(callback_query, state)
