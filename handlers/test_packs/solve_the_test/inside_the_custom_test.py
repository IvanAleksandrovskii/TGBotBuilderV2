# handlers/test_packs/solve_the_pack/inside_the_custom_test.py

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core import log
from core.models import (
    db_helper,
    CustomTest,
    CustomQuestion,
)
from handlers.test_packs.solve_the_pack.solve_pack_menu import get_solve_test_menu


router = Router()


class PassCustomTestStates(StatesGroup):
    PASSING = State()
    QUESTION = State()


@router.callback_query(PassCustomTestStates.PASSING)
async def inside_the_custom_test(
    callback_query: types.CallbackQuery, state: FSMContext
):
    await callback_query.answer("Command called")

    data = await state.get_data()
    test_id = data.get("test_id")  # UUID custom-теста
    test_pack_completion_id = data.get("test_pack_completion_id")

    await state.set_state(PassCustomTestStates.PASSING)
    await state.update_data(
        test_pack_completion_id=test_pack_completion_id,
        test_id=test_id,
        test_type="custom",
    )

    # 1) Загружаем test + вопросы
    async with db_helper.db_session() as session:
        custom_test_query = (
            select(CustomTest)
            .where(CustomTest.id == test_id)
            .options(selectinload(CustomTest.custom_questions))
        )
        result = await session.execute(custom_test_query)
        custom_test = result.scalar_one_or_none()

        if not custom_test:
            await callback_query.message.answer("Тест не найден!")
            # Вернёмся в меню
            await get_solve_test_menu(callback_query.message, state)
            return

        # 2) Сортируем вопросы (например, по порядку в БД или как-то ещё)
        questions = custom_test.custom_questions
        # Если нужна сортировка, делаем:
        # questions = sorted(questions, key=lambda q: q.id) # или другой порядок

    # 3) Сохраняем список вопросов и текущий индекс в state
    # Будем хранить user_answers временно до окончания
    await state.update_data(
        custom_test_name=custom_test.name,
        allow_back=custom_test.allow_back,  # сохраняем настройку возврата назад
        questions=[q.id for q in questions],
        current_index=0,
        user_answers=[],  # здесь будем копить ответы
    )

    # 4) Переходим к состоянию "QUESTION" и вызываем функцию, задающую 1-й вопрос
    await state.set_state(PassCustomTestStates.QUESTION)
    await ask_next_question(callback_query.message, state)


async def ask_next_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions_ids = data["questions"]
    current_index = data["current_index"]

    if current_index >= len(questions_ids):
        # Все вопросы пройдены -> сохранить результат
        await finalize_custom_test(message, state)
        return

    question_id = questions_ids[current_index]

    async with db_helper.db_session() as session:
        q = await session.execute(
            select(CustomQuestion).where(CustomQuestion.id == question_id)
        )
        question = q.scalar_one()

    text = question.question_text

    if question.is_quiz_type:
        # Собираем варианты ответа
        kb_buttons = []
        for i in range(1, 7):
            ans_text = getattr(question, f"answer{i}_text", None)
            ans_score = getattr(question, f"answer{i}_score", None)
            if ans_text is not None:
                kb_buttons.append(
                    [
                        types.InlineKeyboardButton(
                            text=ans_text,
                            callback_data=f"custom_answer_{i}",
                        )
                    ]
                )
        # Если разрешён возврат назад и не на первом вопросе – добавляем кнопку "Назад"
        if data.get("allow_back", False) and current_index > 0:
            kb_buttons.append(
                [types.InlineKeyboardButton(text="Назад", callback_data="custom_back")]
            )

        markup = types.InlineKeyboardMarkup(inline_keyboard=kb_buttons)
        await message.answer(f"Вопрос (multiple choice): {text}", reply_markup=markup)

    else:
        # Свободный ответ: просим написать ответ, добавляем инструкцию для возврата, если включено
        if data.get("allow_back", False) and current_index > 0:
            text += "\n\n(Чтобы вернуться к предыдущему вопросу, отправьте /back)"
        await message.answer(
            f"Вопрос (свободный ответ): {text}\n\nНапишите свой ответ:"
        )


@router.callback_query(
    PassCustomTestStates.QUESTION, F.data.startswith("custom_answer_")
)
async def handle_choice_answer(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Ответ принят", show_alert=False)

    # Get answer choice
    parts = callback_query.data.split("_")
    answer_index = int(parts[-1])  # 1..6

    # Get state data with safety checks
    data = await state.get_data()
    questions_ids = data.get("questions", [])
    current_index = data.get("current_index", 0)

    # Bounds checking
    if not questions_ids:
        await callback_query.message.answer("Ошибка: вопросы не найдены.")
        await finalize_custom_test(callback_query.message, state)
        return

    if current_index >= len(questions_ids):
        # We've somehow gone past the end of questions
        await callback_query.message.answer("Все вопросы уже отвечены.")
        await finalize_custom_test(callback_query.message, state)
        return

    # Get current question_id with safety check
    question_id = questions_ids[current_index]

    # Load question from DB with error handling
    from core.models.custom_test import CustomQuestion

    async with db_helper.db_session() as session:
        q_db = await session.execute(
            select(CustomQuestion).where(CustomQuestion.id == question_id)
        )
        question = q_db.scalar_one_or_none()

    if not question:
        await callback_query.message.answer("Ошибка: вопрос не найден в базе данных.")
        # Skip this question and move to next
        await state.update_data(current_index=current_index + 1)
        await ask_next_question(callback_query.message, state)
        return

    # Get answer data with validation
    ans_text = getattr(question, f"answer{answer_index}_text", "")
    ans_score = getattr(question, f"answer{answer_index}_score", 0)
    question_text = question.question_text

    if not ans_text:  # Additional validation
        await callback_query.message.answer(
            "Ошибка: выбранный вариант ответа недоступен."
        )
        return

    # Get user_answers with safety check
    user_answers = data.get("user_answers", [])

    # Save the answer
    user_answers.append(
        {
            "question_text": question_text,
            "answer_text": ans_text,
            "score": ans_score,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

    # Update state and move to next question
    await state.update_data(current_index=current_index + 1, user_answers=user_answers)

    # Move to next question
    await ask_next_question(callback_query.message, state)


@router.message(PassCustomTestStates.QUESTION, F.text)
async def handle_free_text_answer(message: types.Message, state: FSMContext):
    """
    Handles user's free-text answer for non-quiz type questions.
    Includes bounds checking and error handling.
    """
    data = await state.get_data()
    questions_ids = data.get("questions", [])
    current_index = data.get("current_index", 0)

    # Bounds checking
    if not questions_ids:
        await message.answer("Error: No questions found in the test.")
        await finalize_custom_test(message, state)
        return

    if current_index >= len(questions_ids):
        # We've somehow gone past the end of questions
        await message.answer("All questions have been answered.")
        await finalize_custom_test(message, state)
        return

    # Get current question_id with safety check
    question_id = questions_ids[current_index]

    # Load question from DB with error handling
    from core.models.custom_test import CustomQuestion

    async with db_helper.db_session() as session:
        q_db = await session.execute(
            select(CustomQuestion).where(CustomQuestion.id == question_id)
        )
        question = q_db.scalar_one_or_none()

    if not question:
        await message.answer("Error: Question not found in database.")
        # Skip this question and move to next
        await state.update_data(current_index=current_index + 1)
        await ask_next_question(message, state)
        return

    question_text = question.question_text

    # Handle the answer
    user_answers = data.get("user_answers", [])

    # Save the answer with additional validation
    answer_text = message.text.strip()
    if not answer_text:
        await message.answer("Please provide a non-empty answer.")
        return

    user_answers.append(
        {
            "question_text": question_text,
            "answer_text": answer_text,
            "score": None,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )

    # Update state and move to next question
    await state.update_data(current_index=current_index + 1, user_answers=user_answers)

    await ask_next_question(message, state)


@router.message(PassCustomTestStates.QUESTION)
async def handle_free_text_answer_incorrect(message: types.Message, state: FSMContext):
    await message.answer("Ответ напишите текстом в чат.")


async def finalize_custom_test(message: types.Message, state: FSMContext):
    data = await state.get_data()
    test_pack_completion_id = data.get("test_pack_completion_id")
    test_id = data.get("test_id")
    test_name = data.get("custom_test_name", "Неизвестный тест")

    if not all([test_pack_completion_id, test_id]):
        await message.answer("Ошибка: не хватает данных для сохранения результата.")
        return

    user_answers = data.get("user_answers", [])

    # Подсчитаем суммарный score
    total_score = sum(
        ans.get("score", 0) for ans in user_answers if ans.get("score") is not None
    )

    # Собираем структуру результата
    result_entry = {
        "test_name": test_name,
        "completed_at": datetime.utcnow().isoformat(),
        "total_score": total_score,
        "score": total_score,
        "free_answers": [ans for ans in user_answers if ans.get("score") is None],
        "test_answers": [ans for ans in user_answers if ans.get("score") is not None],
    }

    from core.models.test_pack_completion import TestPackCompletion

    async with db_helper.db_session() as session:
        try:
            tpc = await session.get(TestPackCompletion, test_pack_completion_id)
            if not tpc:
                log.error(
                    f"Ошибка: TestPackCompletion {test_pack_completion_id} не найден!"
                )
                return

            # Логируем перед обновлением
            log.info(
                f"Начинаем обновление TestPackCompletion {test_pack_completion_id}"
            )

            # Удаляем тест из `pending_tests`
            original_len = len(tpc.pending_tests)
            tpc.pending_tests = [t for t in tpc.pending_tests if t["id"] != test_id]
            log.info(
                f"Удалено тестов: {original_len - len(tpc.pending_tests)} из pending_tests"
            )

            # Создаем запись для completed_tests
            new_completed = {
                "type": "custom",
                "id": test_id,
                "name": test_name,
                "result": result_entry,
                "completed_at": datetime.utcnow().isoformat(),
            }

            # Обновляем `completed_tests` через копию списка (важно для SQLAlchemy!)
            if not any(t["id"] == test_id for t in tpc.completed_tests):
                updated_completed_tests = tpc.completed_tests.copy()
                updated_completed_tests.append(new_completed)
                tpc.completed_tests = updated_completed_tests  # Явно обновляем JSON
                log.info(f"Тест {test_id} добавлен в completed_tests")

            # Принудительно обновляем объект в SQLAlchemy
            session.add(tpc)
            await session.commit()
            log.info(
                f"Изменения сохранены в БД для TestPackCompletion {test_pack_completion_id}"
            )

        except Exception as e:
            log.error(
                f"Ошибка при обновлении TestPackCompletion {test_pack_completion_id}: {str(e)}"
            )
            await message.answer(f"Произошла ошибка при сохранении теста: {str(e)}")

    await message.answer(
        f"Тест '{test_name}' завершён!\nВаш итоговый балл: {total_score}"
    )

    # Возвращаем в меню
    from handlers.test_packs.solve_the_pack.start_the_pack import SolveThePackStates

    await state.set_state(SolveThePackStates.SOLVING)
    await state.update_data(test_pack_completion_id=test_pack_completion_id)
    await get_solve_test_menu(message, state)


@router.callback_query(PassCustomTestStates.QUESTION, F.data == "custom_back")
async def handle_back(callback_query: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    if current_index == 0:
        await callback_query.answer("Невозможно вернуться назад", show_alert=True)
        return

    # Удаляем последний сохранённый ответ и переходим к предыдущему вопросу
    user_answers = data.get("user_answers", [])
    if user_answers:
        user_answers.pop()
    new_index = current_index - 1
    await state.update_data(current_index=new_index, user_answers=user_answers)
    await callback_query.answer("Возвращаемся к предыдущему вопросу")
    await ask_next_question(callback_query.message, state)
