# handlers/test_packs/create_pack.py

from sqlalchemy import select

from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from handlers.v1.utils import send_or_edit_message

from .send_tests_pack import get_gefault_media
from core import log
from core.models import db_helper
from core.models.quiz import Test
from core.models.test_pack import TestPack

router = Router()


class SendTestsPackState(StatesGroup):
    NAMING_PACK = State()
    CHOOSING_TESTS = State()
    SENDING_TESTS = State()


@router.callback_query(F.data == "tests_pack_create_new")
async def tests_pack_create_new(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    
    await callback_query.answer("Command called")
    
    async with db_helper.db_session() as session:
        try:
            test_packs_query = select(TestPack).where(TestPack.creator_id == callback_query.from_user.id)
            test_packs = await session.execute(test_packs_query)
            test_packs = test_packs.scalars().all()
            
            if len(test_packs) >= 5:
                await callback_query.message.answer("You already have 5 test packs created. Please delete one of them first.")
                return
            
        except Exception as e:
            log.exception(f"Error in tests_pack_create_new: {e}")
    
    await state.set_state(SendTestsPackState.NAMING_PACK)

    default_media = await get_gefault_media()
    
    button_0 = InlineKeyboardButton(text="🔙 Back", callback_data="send_tests_pack")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_0]])
    
    text = (
        "Write a name for your test pack: (Write the chat)"
    )
    await send_or_edit_message(callback_query, text, keyboard, default_media)


from async_lru import alru_cache


@alru_cache(maxsize=1, ttl=60)
async def get_tests() -> list[Test]:
    async with db_helper.db_session() as session:
        try:
            tests = await session.execute(Test.active().where(Test.is_psychological).order_by(Test.position.nulls_last(), Test.name))
            tests = tests.scalars().all()
        except Exception as e:
            log.exception(f"Error in get_tests: {e}")
            tests = []
    return tests


@router.message(SendTestsPackState.NAMING_PACK, F.text)
async def naming_pack(message: types.Message, state: FSMContext) -> None:
    # Установка следующего состояния
    await state.set_state(SendTestsPackState.CHOOSING_TESTS)
    # Сохранение данных в state
    await state.update_data(pack_name=message.text)
    
    default_media = await get_gefault_media()
    text = (
        f"Pack name: {message.text}" 
        "\n\n"
        "Choose a test to add to the pack:"
        "\n\n"
    )
    
    tests = await get_tests()
    # await state.update_data(tests=tests)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    if tests:
        for test in tests:
            btn = InlineKeyboardButton(text=f"➕ {test.name}", callback_data=f"test_pack_add_test_{test.id}")
            keyboard.inline_keyboard.append([btn])
    else:
        text += "\n\nNo tests found. ERROR"
    button_back = InlineKeyboardButton(text="🔙 Back", callback_data="send_tests_pack")
    keyboard.inline_keyboard.append([button_back])
    
    await send_or_edit_message(message, text, keyboard, default_media)


@router.message(SendTestsPackState.NAMING_PACK)
async def wrong_naming_pack(message: types.Message) -> None:
    await message.answer("Please, write a name for your test pack to the chat.")


@router.callback_query(SendTestsPackState.CHOOSING_TESTS)
async def choosing_tests(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    await callback_query.answer("Command called")
    
    media = await get_gefault_media()
    all_tests = await get_tests()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    state_data = await state.get_data()  # Это вернёт dict со всеми данными
    log.debug(f"State data: {state_data}")
    
    if callback_query.data == "test_pack_save":  # TODO: Add link (to pass the pack) to the result
        state_data = await state.get_data()
        await state.clear()
        if "tests" not in state_data:
            await callback_query.answer("Please, select at least one test.")
            return
        
        selected_tests = state_data["tests"]
        selected_tests_objects = [test for test in all_tests if str(test.id) in selected_tests]
        
        # Создаём и сохраняем пак тестов
        async with db_helper.db_session() as session:
            try:
                # Создаём новый пак
                test_pack = TestPack(
                    name=state_data["pack_name"],
                    creator_id=callback_query.from_user.id,
                    creator_username=callback_query.from_user.username,
                    tests=selected_tests_objects
                )
                
                # Добавляем в сессию и сохраняем
                session.add(test_pack)
                await session.commit()
                
                text = (
                    f"✅ Test pack '{test_pack.name}' successfully created!\n"
                    f"Test pack ID: {test_pack.id}\n\n"
                    f"Tests included: \n{', '.join([test.name for test in selected_tests_objects])}"
                )
                
            except Exception as e:
                log.exception(f"Error saving test pack: {e}")
                text = "❌ Error saving test pack. Please try again."
                await session.rollback()
        
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="Back", callback_data="send_tests_pack")])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="Main Menu", callback_data="back_to_start")])
        
        await send_or_edit_message(callback_query.message, text, keyboard, media)
        return 
    
    if callback_query.data == "test_pack_back_to_selection":
        if "tests" not in state_data:
            state_data["tests"] = []

    if callback_query.data.startswith("test_pack_yes_add_test_"):
        parts = callback_query.data.split("_")
        test_id = parts[-1]
        
        if "tests" not in state_data:
            state_data["tests"] = [test_id]
        else:
            state_data["tests"].append(test_id)
        await state.update_data(tests=state_data["tests"])
    
    if callback_query.data.startswith("test_pack_add_test_"):
        parts = callback_query.data.split("_")
        test_id = parts[-1]
        
        async with db_helper.db_session() as session:
            test = await session.execute(select(Test).where(Test.id == test_id))
            test = test.scalar_one()
        
        text = f"{test.name}:\n{test.description}\n\n"
        
        text += f"Add test {test.name} to the pack?"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="Yes", callback_data=f"test_pack_yes_add_test_{test.id}")],
            [types.InlineKeyboardButton(text="No", callback_data=f"test_pack_back_to_selection")]
        ])
        
        await send_or_edit_message(callback_query.message, text, keyboard, media)
        return
    
    text = ""
    if state_data["tests"]:
        added_tests_names = [test.name for test in all_tests if str(test.id) in state_data["tests"]]
        text += f"Tests selected: \n{', '.join(added_tests_names)}\n\n"
        
    text += f"Choose a test to add to the pack:"
    tests = [test for test in all_tests if str(test.id) not in state_data["tests"]]
    
    for test in tests:
        btn = InlineKeyboardButton(text=f"➕ {test.name}", callback_data=f"test_pack_add_test_{test.id}")
        keyboard.inline_keyboard.append([btn])
    
    if state_data["tests"]:
        button_apply = InlineKeyboardButton(text="✅ Apply", callback_data="test_pack_save")
        keyboard.inline_keyboard.append([button_apply])
    
    if len(tests) == 0:
        text += "\n\nNo more tests found."
    
    button_back = InlineKeyboardButton(text="🔙 Back", callback_data="send_tests_pack")
    keyboard.inline_keyboard.append([button_back])
    await send_or_edit_message(callback_query.message, text, keyboard, media)
