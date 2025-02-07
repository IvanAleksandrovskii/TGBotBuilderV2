# handlers/test_packs/solve_the_pack/inside_the_psychological_test.py

from collections import defaultdict
from datetime import datetime
from random import shuffle

from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from sqlalchemy import select  # , func, or_

from core import log, settings
from core.models import db_helper
from core.models import Test, QuizResult, User, Result, Question, TestPackCompletion
from services.text_service import TextService

from services.user_services import UserService

from handlers.utils import send_or_edit_message

# from handlers.test_packs.solve_the_pack.solve_pack_menu import (
#     get_solve_test_menu,
#     SolveThePackStates,
# )


router = Router()


class PassingTestStates(StatesGroup):
    VIEWING_INTRO = State()
    ANSWERING = State()
    SHOWING_COMMENT = State()
    SHOWING_RESULT = State()


async def fsm_state_setter(state: FSMContext, new_state: StatesGroup) -> FSMContext:
    state_data = await state.get_data()
    await state.set_state(new_state)
    await state.set_data(state_data)
    return state


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
            shuffle(order_questions)
        sorted_questions.extend(order_questions)

    return sorted_questions


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


async def confirm_start_test(
    callback_query: types.CallbackQuery, state: FSMContext, quiz_id: str
):
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
                start_time=datetime.utcnow().isoformat(),  # Add start time tracking
            )
            # Вызов send_question с объектом callback_query
            await send_question(callback_query, state)
        except Exception as e:
            log.exception(e)


async def send_question(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quiz_id = data["quiz_id"]
    current_question = data["current_question"]
    sorted_questions = data["sorted_questions"]

    async for session in db_helper.session_getter():
        try:
            test = await session.execute(select(Test).where(Test.id == quiz_id))
            test = test.scalar_one_or_none()

            if current_question >= len(sorted_questions):
                await finish_test(callback_query, state)
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
                                callback_data="show_q",
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

                await send_or_edit_message(
                    callback_query, intro_text, keyboard, media_url
                )

                data["intro_shown"] = True
                await state.update_data(data)
                await fsm_state_setter(state, PassingTestStates.VIEWING_INTRO)
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
                                callback_data=f"ans_{current_question}_{i}",
                            )
                        ]
                    )

            if test.allow_back and current_question > 0:
                keyboard.append(
                    [
                        types.InlineKeyboardButton(
                            text=settings.quiz_text.quiz_question_previous_button,
                            callback_data="move_back",
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

            await send_or_edit_message(
                callback_query, question_text, reply_markup, media_url
            )

            data["intro_shown"] = False  # Drop the flag for the next question
            await state.update_data(data)
            await fsm_state_setter(state, PassingTestStates.ANSWERING)

        except Exception as e:
            log.exception(e)
        finally:
            await session.close()


async def process_intro(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data["intro_shown"] = True
    await state.update_data(data)
    # Вызов send_question с объектом callback_query
    await send_question(callback_query, state)


async def process_comment(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    data["current_question"] += 1
    await state.update_data(data)
    # Вызов send_question с объектом callback_query
    await send_question(callback_query, state)


async def process_answer(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    sorted_questions = data["sorted_questions"]

    if callback_query.data == "move_back":
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
            await send_question(callback_query, state)
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
                await show_comment(callback_query, question_data["comment"], state)
            else:
                data["current_question"] += 1
                await state.update_data(data)
                await send_question(callback_query, state)

        except Exception as e:
            log.exception(e)


async def show_comment(
    callback_query: types.CallbackQuery, comment: str, state: FSMContext
):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=settings.quiz_text.quiz_continue_button,
                    callback_data="continue_test",
                )
            ]
        ]
    )

    data = await state.get_data()
    async for session in db_helper.session_getter():
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

    await fsm_state_setter(state, PassingTestStates.SHOWING_COMMENT)


async def finish_test(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    quiz_id = data["quiz_id"]
    total_score = sum(data["answers"])
    category_scores = data.get("category_scores", {})

    test_pack_completion_id = data.get("test_pack_completion_id")
    await fsm_state_setter(state, PassingTestStates.SHOWING_RESULT)

    result_text = ""

    # Calculate time spent
    start_time = datetime.fromisoformat(data["start_time"])
    end_time = datetime.utcnow()
    time_spent = end_time - start_time
    minutes = int(time_spent.total_seconds() // 60)
    seconds = int(time_spent.total_seconds() % 60)

    result_picture = None
    test_picture = None

    # TODO: Make everywhere 1 big query
    async for session in db_helper.session_getter():
        try:
            # Get test, sent test, and user information
            test = await session.execute(select(Test).where(Test.id == quiz_id))
            test = test.scalar_one_or_none()

            query = select(TestPackCompletion).where(
                TestPackCompletion.id == test_pack_completion_id
            )

            test_pack_completion = await session.execute(query)
            test_pack_completion = test_pack_completion.scalar_one_or_none()

            query = select(User).where(User.chat_id == callback_query.from_user.id)
            user = await session.execute(query)
            user = user.scalar_one_or_none()

            if not test or not test_pack_completion or not user:
                await callback_query.answer(
                    "An error occurred. Please try again later."
                )
                return

            # Calculate and save results
            results = await calculate_results(
                session, test, total_score, category_scores
            )

            # Save results for each category/overall
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

            # Prepare result message and media  # TODO: Fix result generation and add the max scores (?)
            # if test.multi_graph_results:
            #     result_text = ""
            #     for result in results:
            #         result_text += f"Набрано баллов в категории {result['category_name']}: {result['score']}\n{result['text']}\n\n"
            # else:
            #     result_text = f"Набрано баллов: {total_score}\n{results[0]['text']}"

            if test.multi_graph_results:
                result_text = f"Время прохождения: {minutes} мин {seconds} сек\n\n"  # Add time spent
                for result in results:
                    result_text += f"Набрано баллов в категории {result['category_name']}: {result['score']}\n{result['text']}\n\n"
            else:
                result_text = f"Время прохождения: {minutes} мин {seconds} сек\n\n"  # Add time spent
                result_text += f"Набрано баллов: {total_score}\n{results[0]['text']}"

            # Удаляем тест из `pending_tests`
            original_len = len(test_pack_completion.pending_tests)
            test_pack_completion.pending_tests = [
                t
                for t in test_pack_completion.pending_tests
                if t["id"] != str(test.id)  # TODO: Double check (( ! ))
            ]
            log.info(
                f"Удалено тестов: {original_len - len(test_pack_completion.pending_tests)} из pending_tests"
            )

            # Создаем запись для completed_tests
            new_completed = {
                "type": "test",
                "id": str(test.id),
                "name": test.name,
                "completed_at": datetime.utcnow().isoformat(),
                "result": result_text,
            }

            # Обновляем `completed_tests` через копию списка (важно для SQLAlchemy!)
            if not any(
                t["id"] == str(test.id) for t in test_pack_completion.completed_tests
            ):
                updated_completed_tests = test_pack_completion.completed_tests.copy()
                updated_completed_tests.append(new_completed)
                test_pack_completion.completed_tests = (
                    updated_completed_tests  # Явно обновляем JSON
                )
                log.info(f"Тест {test.id} добавлен в completed_tests")

            # Принудительно обновляем объект в SQLAlchemy
            session.add(test_pack_completion)

            test_picture = test.picture
            if results:
                result_picture = results[0].get("picture")

            await session.commit()
            log.info(
                f"Изменения сохранены в БД для TestPackCompletion {test_pack_completion_id}"
            )

            # Build keyboard
            keyboard = []

            keyboard.append(
                [
                    types.InlineKeyboardButton(
                        text="Далее",
                        callback_data="to_completion_menu",
                    )
                ]
            )

            # Get appropriate media URL
            text_service = TextService()

            # result_media = results[0].get("picture") if results else None
            if result_picture is not None:
                media_url = result_picture

            elif test_picture is not None:
                media_url = test_picture
            else:
                media_url = await text_service.get_default_media(session)

            if media_url and not media_url.startswith(("http://", "https://")):
                media_url = f"{settings.media.base_url}/app/{media_url}"

            # Send final message with results
            await send_or_edit_message(
                callback_query,
                result_text,
                types.InlineKeyboardMarkup(inline_keyboard=keyboard),
                media_url,
            )

        except Exception as e:
            log.exception(e)
            await callback_query.answer(settings.received_tests.test_end_error)


@router.callback_query(
    F.data.startswith(
        ("ans_", "move_back", "show_q", "continue_test", "to_completion_menu")
    )
)
async def process_quiz_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()

    current_state = await state.get_state()
    if current_state == PassingTestStates.SHOWING_RESULT:  # TODO: Double check (( ! ))
        from handlers.test_packs.solve_the_pack.solve_pack_menu import (
            get_solve_test_menu,
        )
        from handlers.test_packs.solve_the_pack import (
            SolveThePackStates,
        )

        state_data = await state.get_data()
        test_pack_completion_id = state_data["test_pack_completion_id"]
        await state.set_state(SolveThePackStates.SOLVING)
        await state.update_data(test_pack_completion_id=test_pack_completion_id)
        await get_solve_test_menu(callback_query.message, state)
        return

    elif current_state == PassingTestStates.VIEWING_INTRO:
        await process_intro(callback_query, state)

    elif current_state == PassingTestStates.ANSWERING:
        await process_answer(callback_query, state)

    elif current_state == PassingTestStates.SHOWING_COMMENT:
        await process_comment(callback_query, state)

    else:
        from handlers.on_start import back_to_start_from_message

        await back_to_start_from_message(callback_query.message, state)
