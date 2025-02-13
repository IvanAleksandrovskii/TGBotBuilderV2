# handlers/fallback.py

from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from .back_to_start import back_to_start

from services.decorators import handle_as_task, TaskPriority


router = Router()


@router.callback_query()
@handle_as_task(priority=TaskPriority.NORMAL)
async def fallback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Что-то пошло не так")

    await callback_query.message.answer(
        "Извините, что-то пошло не так, загружаю главное меню..."
    )  # TODO: Move to config
    await back_to_start(callback_query, state)
