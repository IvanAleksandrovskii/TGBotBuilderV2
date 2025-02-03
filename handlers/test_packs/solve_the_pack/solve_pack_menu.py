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
from handlers.test_packs.solve_the_pack.start_the_pack import SolveThePackStates

# from handlers.test_packs.solve_the_pack.notifications_for_creator import notify_creator


router = Router()


# jinja environment
env = Environment(
    loader=FileSystemLoader("handlers/test_packs/solve_the_pack/templates")
)


async def get_solve_test_menu(
    message: types.Message | types.CallbackQuery, state: FSMContext
):
    if isinstance(message, types.CallbackQuery):
        message = message.message

    state_instance = await state.get_state()

    if state_instance not in [
        SolveThePackStates.SOLVING,
        SolveThePackStates.ANSWERING_TEST,
        SolveThePackStates.COMPLETING,
    ]:
        await message.answer(
            "You are not in solving state. Telegram error happaned, bot made a restart. "
            "Please press -> /abort and open the test pack again using the link."
        )  # TODO: Move to config
        return

    data = await state.get_data()
    test_pack_completion_id = data.get("test_pack_completion_id")

    state.set_state(SolveThePackStates.SOLVING)
    await state.update_data(test_pack_completion_id=test_pack_completion_id)

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
    
    if test_pack_completion.pending_tests == []:
        from .final_all_tests_done import finish_the_pack
        await finish_the_pack(message, state)
        return

    completed_tests = [t for t in test_pack_completion.completed_tests if t["type"] == "test"]
    completed_custom_tests = [t for t in test_pack_completion.completed_tests if t["type"] == "custom"]

    completed_tests_names_list = [test["name"] for test in completed_tests]
    completed_custom_tests_names_list = [test["name"] for test in completed_custom_tests]

    pending_tests = test_pack_completion.pending_tests
    tests_to_complete = [t for t in pending_tests if t["type"] == "test"]
    custom_tests_to_complete = [t for t in pending_tests if t["type"] == "custom"]

    # Фильтрации тестов:
    completed_tests_ids = {t["id"] for t in completed_tests}
    completed_custom_tests_ids = {t["id"] for t in completed_custom_tests}

    tests_to_complete = [t for t in tests_to_complete if t["id"] not in completed_tests_ids]
    custom_tests_to_complete = [t for t in custom_tests_to_complete if t["id"] not in completed_custom_tests_ids]


    # 3) Теперь можно проверить их длину:
    if len(tests_to_complete) + len(custom_tests_to_complete) == 0:  # TODO: Make it finalize the completion here
        await message.answer(
            "No tests to complete. Error happened. Please press -> /abort"
        )
        return

    # 4) Формируем клавиатуру
    keyboard = []

    for test_data in tests_to_complete:
        keyboard.append(
            [
                types.InlineKeyboardButton(
                    text=test_data["name"],
                    callback_data=f"solve_test_{test_data.get('test_id', test_data.get('id'))}",  # TODO: Fix to make only one check
                )
            ]
        )

    for test_data in custom_tests_to_complete:
        keyboard.append(
            [
                types.InlineKeyboardButton(
                    text=test_data["name"],
                    callback_data=f"solve_custom_test_{test_data.get('test_id', test_data.get('id'))}",  # TODO: Fix to make only one check
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
            completed_tests_names_list=completed_tests_names_list,
            completed_custom_tests_names_list=completed_custom_tests_names_list,
        ),
        types.InlineKeyboardMarkup(inline_keyboard=keyboard),
        default_media,
    )
