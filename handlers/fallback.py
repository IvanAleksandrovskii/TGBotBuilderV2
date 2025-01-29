# handlers/fallback.py

from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from .back_to_start import back_to_start

router = Router()


@router.callback_query()
async def fallback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer("Fallback callback query")
    
    await callback_query.message.answer(
        "Sorry, bot was restarted or some error happened, "
        "turning you back to start"
        )  # TODO: Move to config
    await back_to_start(callback_query, state)
