# handlers/test_packs/solve_the_pack/solve_pack_menu.py

# from uuid import UUID
# from sqlalchemy.orm import selectinload
from sqlalchemy import select

from aiogram import Router, types, F
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from jinja2 import Environment, FileSystemLoader

from core import log
from core.models import (
    db_helper,
    TestPackCompletion,
)
from handlers.utils import send_or_edit_message, get_default_media

# from handlers.test_packs.solve_the_pack.notifications_for_creator import notify_creator


router = Router()


# jinja environment
env = Environment(
    loader=FileSystemLoader("handlers/test_packs/solve_the_pack/templates")
)


@router.callback_query(F.data == "back_to_solve_test_menu")
async def get_solve_test_menu(message: types.Message, state: FSMContext):

    state_instance = await state.get_state()

    from handlers.test_packs.solve_the_pack.start_the_pack import SolveThePackStates

    if state_instance not in [
        SolveThePackStates.SOLVING,
        SolveThePackStates.ANSWERING_TEST,
        SolveThePackStates.COMPLETING,
    ]:
        await message.answer(
            "You are not in solving state. Telegram error happaned, bot made a restart. "
            "Please press -> /abort and open the test pack again using link."
        )
        return

    data = await state.get_data()
    test_pack_completion_id = data.get("test_pack_completion_id")

    async with db_helper.db_session() as session:
        try:
            test_pack_completion_query = select(TestPackCompletion).where(
                TestPackCompletion.id == test_pack_completion_id
            )
            test_pack_completion = await session.execute(test_pack_completion_query)
            test_pack_completion = test_pack_completion.scalar_one_or_none()

            if not test_pack_completion:
                await message.answer("Test pack completion not found, ERROR")
                return
        except Exception as e:
            log.exception(f"Error in get_solve_test_menu: {e}")
            await message.answer("An error occurred. Please try again later.")

    # Структура tests_to_complete:
    # {
    # "tests_to_complete": {
    #     "tests": [{
    #         "test_name": "Test name",
    #         "test_id": "test_id",
    #     },],
    # "custom_tests": [{
    #         "test_name": "Test name",
    #         "test_id": "test_id",
    #     },],
    # }

    # Структура progress_data:
    # progress_data = {
    #     "progress_data": {
    #         "completed_tests": {
    #             "test_<UUID>": {
    #                 "test_name": "Test name",
    #                 "completed_at": "ISO datetime",
    #                 "result_text": "текст результата"
    #             }
    #         },
    #         "completed_custom_tests": {
    #             "custom_<UUID>": {
    #                 "test_name": "Test name",
    #                 "completed_at": "ISO datetime",
    #                 "total_score": 0,
    #                 "score": 0,
    #                 "free_answers": [
    #                     {
    #                         "question_text": "Text of the question",
    #                         "answer_text": "пользовательский ввод",
    #                         "timestamp": "ISO datetime"
    #                     },
    #                 ],
    #                 "test_answers": [
    #                     {
    #                         "question_text": "Text of the question",
    #                         "answer_text": "Answer text",
    #                         "score": 0,
    #                         "timestamp": "ISO datetime"
    #                     },
    #                 ]
    #             }
    #         }
    #     }
    # }

    progress_data: dict = test_pack_completion.progress_data
    completed_tests: dict = progress_data.get("progress_data", {}).get(
        "completed_tests", {}
    )
    completed_custom_tests: dict = progress_data.get("progress_data", {}).get(
        "completed_custom_tests", {}
    )

    completed_tests_names_list: list[str] = []
    for test_id, test in completed_tests.items():
        completed_tests_names_list.append(test["test_name"])

    completed_custom_tests_names_list: list[str] = []
    for test_id, test in completed_custom_tests.items():
        completed_custom_tests_names_list.append(test["test_name"])

    all_tests_to_complete: dict = test_pack_completion.tests_to_complete

    # 1) Забираем вложенный словарь (или пустой) из tests_to_complete
    tests_object = all_tests_to_complete.get("tests_to_complete", {})

    # 2) Из этого словаря достаём списки
    tests_to_complets = tests_object.get("tests", [])
    custom_tests_to_complets = tests_object.get("custom_tests", [])

    # 3) Теперь можно проверить их длину:
    if len(tests_to_complets) + len(custom_tests_to_complets) == 0:
        await message.answer(
            "No tests to complete. Error happened. Please press -> /abort"
        )
        return

    # 4) Формируем клавиатуру
    keyboard = []

    for test_data in tests_to_complets:
        keyboard.append(
            [
                types.InlineKeyboardButton(
                    text=test_data["name"],
                    callback_data=f"solve_test_{test_data['id']}",
                )
            ]
        )

    for test_data in custom_tests_to_complets:
        keyboard.append(
            [
                types.InlineKeyboardButton(
                    text=test_data["name"],
                    callback_data=f"solve_custom_test_{test_data['id']}",
                )
            ]
        )

    # jinja environment
    env = Environment(
        loader=FileSystemLoader("handlers/test_packs/solve_the_pack/templates")
    )
    template = env.get_template("solve_test_pack_menu.html")
    
    default_media = await get_default_media()

    await send_or_edit_message(
        message,
        template.render(
            completed_tests=completed_custom_tests_names_list,
            completed_custom_tests=completed_custom_tests_names_list,
        ),
        types.InlineKeyboardMarkup(inline_keyboard=keyboard),
        default_media,
    )
