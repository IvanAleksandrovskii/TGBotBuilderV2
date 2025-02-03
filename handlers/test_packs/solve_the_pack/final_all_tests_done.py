# handlers/test_packs/solve_the_pack/final_all_tests_done.py

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext

from sqlalchemy import select

from core import log
from core.models import db_helper
from core.models.test_pack_completion import CompletionStatus, TestPackCompletion
from handlers.test_packs.solve_the_pack.notifications_for_creator import notify_creator
from handlers.test_packs.solve_the_pack.start_the_pack import SolveThePackStates


router = Router()


async def finish_the_pack(message: types.Message, state: FSMContext) -> None:
    state_data = await state.get_data()

    await state.set_state(SolveThePackStates.COMPLETING)
    await state.set_data(state_data)

    test_pack_completion_id = state_data["test_pack_completion_id"]

    async with db_helper.db_session() as session:
        try:
            query = select(TestPackCompletion).where(
                TestPackCompletion.id == test_pack_completion_id
            )
            result = await session.execute(query)
            test_pack_completion = result.scalar_one_or_none()

            if test_pack_completion is None:
                log.error(
                    f"Failed to get test pack completion with id {test_pack_completion_id}"
                )
                await message.answer("An error occurred. Please try again later.")
                return

            test_pack_completion.status = CompletionStatus.COMPLETED
            await session.commit()

        except Exception as e:
            log.exception(e)
            await message.answer("An error occurred. Please try again later.")
            return

    await message.answer(
        "Все тесты пройдены! Теперь пришлите мне ваше резюме и (или) "
        "сопроводительное письмо, необходимо все прислать одним сообщением"
    )


@router.message(SolveThePackStates.COMPLETING)
async def recive_resume(message: types.Message, state: FSMContext):
    await message.answer("recive_resume called")
