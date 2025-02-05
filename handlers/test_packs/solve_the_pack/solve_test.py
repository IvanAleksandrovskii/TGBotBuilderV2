# handlers/test_packs/solve_the_pack/solve_test.py

from typing import Optional

from sqlalchemy import select

from jinja2 import Environment, FileSystemLoader

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core import log
from core.models import (
    db_helper,
    TestPackCompletion,
    Test,
    CustomTest,
)


from handlers.test_packs.solve_the_pack import SolveThePackStates
from handlers.utils import send_or_edit_message, get_default_media
from handlers.test_packs.solve_the_pack.solve_pack_menu import get_solve_test_menu

router = Router()


class PassTestMenuStates(StatesGroup):
    STARTING = State()


# Back to start for PassTestStates.STARTING
@router.callback_query(PassTestMenuStates.STARTING, F.data == "no")
async def back_to_solve_test_menu(
    callback_query: types.CallbackQuery, state: FSMContext
):
    await callback_query.answer("Назад к менюу")  # TODO: Move to config
    data = await state.get_data()
    test_pack_completion_id = data.get("test_pack_completion_id")
    await state.set_state(SolveThePackStates.SOLVING)
    await state.update_data(test_pack_completion_id=test_pack_completion_id)
    await get_solve_test_menu(callback_query.message, state)


@router.callback_query(
    F.data.startswith("solve_test_") | F.data.startswith("solve_custom_test_")
)
async def solve_test(callback_query: types.CallbackQuery, state: FSMContext):
    state_instance = await state.get_state()

    if state_instance not in [SolveThePackStates.SOLVING]:
        await callback_query.message.answer(
            "Пока вы проходили тест бот был перезагружен, пожалуйста, откройте свое прохождение "
            "тестов снова используя ссылку по которой вы начали ранее, чтобы продолжить прохождение."
        )
        from handlers.on_start import back_to_start
        await back_to_start(callback_query, state)
        return

    await callback_query.answer("Начать?")

    # Get the test pack ID from the state
    data = await state.get_data()
    test_pack_completion_id = data.get("test_pack_completion_id")

    # Get the test ID from the callback data
    parts = callback_query.data.split("_")
    test_id = parts[-1]

    default_media = await get_default_media()

    await state.set_state(PassTestMenuStates.STARTING)
    await state.update_data(test_pack_completion_id=test_pack_completion_id)
    await state.update_data(test_id=test_id)

    keyboard = []

    btn_yes = types.InlineKeyboardButton(
        text="✅ Начать",
        callback_data="yes",
    )
    btn_no = types.InlineKeyboardButton(
        text="❌ Назад",
        callback_data="no",
    )

    keyboard.append([btn_no, btn_yes])

    if callback_query.data.startswith("solve_test_"):

        await state.update_data(test_type="psychological")

        async with db_helper.db_session() as session:
            try:
                tpc = await session.get(TestPackCompletion, test_pack_completion_id)
                if any(t["id"] == test_id for t in tpc.completed_tests):
                    await callback_query.answer("Этот тест уже пройден!")
                    return

                test_query = select(Test).where(Test.id == test_id)
                test = await session.execute(test_query)
                test = test.scalar_one_or_none()

                if not test:  # TODO: Write this scenario
                    await callback_query.message.answer(
                        f"Test with id {test_id} not found"
                    )
                    return

                test_name = test.name
                custom_test_description = test.description

                # jinja environment
                env = Environment(
                    loader=FileSystemLoader(
                        "handlers/test_packs/solve_the_pack/templates"
                    )
                )
                template = env.get_template("confirm_start_test.html")

                await send_or_edit_message(
                    callback_query.message,
                    template.render(
                        test_name=test_name, test_description=custom_test_description
                    ),
                    types.InlineKeyboardMarkup(inline_keyboard=keyboard),
                    default_media,
                )

            except Exception as e:
                log.exception(f"Error in solve_test: {e}")
                await callback_query.message.answer(
                    "An error occurred. Please try again later."
                )
                return

    elif callback_query.data.startswith("solve_custom_test_"):

        await state.update_data(test_type="custom")

        async with db_helper.db_session() as session:
            try:
                custom_test_query = select(CustomTest).where(CustomTest.id == test_id)
                custom_test = await session.execute(custom_test_query)
                custom_test = custom_test.scalar_one_or_none()

                if not custom_test:  # TODO: Write this scenario
                    await callback_query.message.answer(
                        f"Custom test with id {test_id} not found"
                    )
                    return

                test_name = custom_test.name
                custom_test_description = custom_test.description

                # jinja environment
                env = Environment(
                    loader=FileSystemLoader(
                        "handlers/test_packs/solve_the_pack/templates"
                    )
                )
                template = env.get_template("confirm_start_test.html")

                await send_or_edit_message(
                    callback_query.message,
                    template.render(
                        test_name=test_name, test_description=custom_test_description
                    ),
                    types.InlineKeyboardMarkup(inline_keyboard=keyboard),
                    default_media,
                )

            except Exception as e:
                log.exception(f"Error in solve_test: {e}")
                await callback_query.message.answer(
                    "An error occurred. Please try again later."
                )
                return

    else:
        await callback_query.message.answer("Error occured")


@router.callback_query(PassTestMenuStates.STARTING, F.data == "yes")
async def start_test(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Начат тест")  # TODO: Move to config

    data = await state.get_data()
    test_pack_completion_id = data.get(
        "test_pack_completion_id"
    )  # TODO: Should be turned back to state
    test_id = data.get("test_id")
    test_type = data.get("test_type")

    async with db_helper.db_session() as session:
        try:
            if test_type == "psychological":
                # test_query = select(Test).where(Test.id == test_id)
                # test = await session.execute(test_query)
                # test = test.scalar_one_or_none()

                # if not test:  # TODO: Write this scenario
                #     await callback_query.message.answer(
                #         f"Test with id {test_id} not found"
                #     )
                #     return

                # # TODO: Write this scenario
                # await callback_query.message.answer(f"Test started! {test_id} name: {test.name}")

                from handlers.test_packs.solve_the_test.inside_the_psychological_test import (
                    confirm_start_test,
                )
                await confirm_start_test(callback_query, state, test_id)
                return

            elif test_type == "custom":
                custom_test_query = select(CustomTest).where(CustomTest.id == test_id)
                custom_test = await session.execute(custom_test_query)
                custom_test = custom_test.scalar_one_or_none()

                if not custom_test:  # TODO: Write this scenario
                    await callback_query.message.answer(
                        f"Custom test with id {test_id} not found"
                    )
                    return

                from handlers.test_packs.solve_the_test import inside_the_custom_test

                await inside_the_custom_test(callback_query, state)

            else:
                await callback_query.message.answer("Error occured")
                return

        except Exception as e:
            log.exception(f"Error in start_test: {e}")
            await callback_query.message.answer(
                "An error occurred. Please try again later."
            )
            await state.clear()
            await state.set_state(SolveThePackStates.SOLVING)
            await state.update_data(test_pack_completion_id=test_pack_completion_id)

            await get_solve_test_menu(callback_query.message, state)
            return
