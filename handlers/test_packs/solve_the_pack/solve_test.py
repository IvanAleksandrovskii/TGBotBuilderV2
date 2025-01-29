# handlers/test_packs/solve_the_pack/solve_test.py

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from core import log
from core.models import db_helper
from core.models.test_pack_completion import TestPackCompletion
from core.models.test_pack import TestPack

from handlers.test_packs.solve_the_pack import SolveThePackStates
from handlers.utils import send_or_edit_message

router = Router()


@router.callback_query(F.data.startswith("solve_test_") | F.data.startswith("solve_custom_test_"))
async def solve_test(callback_query: types.CallbackQuery, state: FSMContext):
    state_instance = await state.get_state()
    
    if state_instance not in [SolveThePackStates.SOLVING]:
        await callback_query.message.answer(
            "There is an error occured. Please press -> /abort and open the test pack again using link."
        )
        return
    
    await callback_query.answer("Начат тест")
    
    # Get the test pack ID from the state
    data = await state.get_data()
    test_pack_completion_id = data.get("test_pack_completion_id")

    # Get the test ID from the callback data
    parts = callback_query.data.split("_")
    test_id = parts[-1]

    if callback_query.data.startswith("solve_test_"):
        await callback_query.message.answer(f"Начат тест: {test_id}")
        
        
    elif callback_query.data.startswith("solve_custom_test_"):
        await callback_query.message.answer(f"Начат кастомный тест: {test_id}")
        
        
    else:
        await callback_query.message.answer("Error occured")
