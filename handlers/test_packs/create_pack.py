# handlers/test_packs/create_pack.py

from async_lru import alru_cache

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
from core.models.custom_test import CustomTest
from core.models.test_pack import TestPack

router = Router()


class SendTestsPackState(StatesGroup):
    NAMING_PACK = State()
    CHOOSING_TESTS = State()


@router.callback_query(F.data == "tests_pack_create_new")
async def tests_pack_create_new(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    """
    Хендлер, вызываемый по нажатию кнопки «создать новый пак».
    Проверяет, не превышено ли количество паков (максимум 5),
    и переводит пользователя в состояние ввода названия пака.
    """
    await callback_query.answer("Command called")

    async with db_helper.db_session() as session:
        try:
            test_packs_query = select(TestPack).where(TestPack.creator_id == callback_query.from_user.id)
            test_packs = await session.execute(test_packs_query)
            test_packs = test_packs.scalars().all()

            if len(test_packs) >= 5:
                await callback_query.message.answer(
                    "You already have 5 test packs created. Please delete one of them first."
                )
                return
        except Exception as e:
            log.exception(f"Error in tests_pack_create_new: {e}")

    # Переводим пользователя в состояние ввода названия тест-пака
    await state.set_state(SendTestsPackState.NAMING_PACK)

    default_media = await get_gefault_media()
    button_back = InlineKeyboardButton(text="🔙 Back", callback_data="send_tests_pack")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[button_back]])

    text = "Write a name for your test pack: (Write into the chat)"
    await send_or_edit_message(callback_query, text, keyboard, default_media)


@alru_cache(maxsize=1, ttl=60)
async def get_tests() -> list[Test]:
    """
    Возвращает список доступных активных тестов, отсортированных по position и названию.
    Результат кешируется на 60 секунд.
    """
    async with db_helper.db_session() as session:
        try:
            query = Test.active().where(Test.is_psychological).order_by(Test.position.nulls_last(), Test.name)
            tests_result = await session.execute(query)
            tests = tests_result.scalars().all()
        except Exception as e:
            log.exception(f"Error in get_tests: {e}")
            tests = []
    return tests


@alru_cache(maxsize=20, ttl=60)
async def get_custom_tests(chat_id: int) -> list[CustomTest]:
    """
    Возвращает список пользовательских тестов для заданного chat_id.
    Результат кешируется на 60 секунд.
    """
    async with db_helper.db_session() as session:
        try:
            query = CustomTest.active().where(CustomTest.creator_id == chat_id)
            custom_tests_result = await session.execute(query)
            custom_tests = custom_tests_result.scalars().all()
        except Exception as e:
            log.exception(f"Error in get_custom_tests: {e}")
            custom_tests = []
    return custom_tests


@router.message(SendTestsPackState.NAMING_PACK, F.text)
async def naming_pack(message: types.Message, state: FSMContext) -> None:
    """
    Хендлер для состояния NAMING_PACK, принимает текстовое сообщение — название нового пака.
    Переводит пользователя в состояние выбора тестов.
    """
    await state.set_state(SendTestsPackState.CHOOSING_TESTS)
    await state.update_data(pack_name=message.text)

    default_media = await get_gefault_media()
    text = (
        f"Pack name: {message.text}"
        "\n\nChoose a test to add to the pack:"
        "\n\n"
    )

    tests = await get_tests()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Кнопки с «обычными» тестами
    if tests:
        for test in tests:
            btn = InlineKeyboardButton(
                text=f"➕ {test.name}",
                callback_data=f"test_pack_add_test_{test.id}",
            )
            keyboard.inline_keyboard.append([btn])
    else:
        text += "\n\nNo tests found. ERROR"

    # Кнопки с кастомными тестами
    custom_tests = await get_custom_tests(message.chat.id)
    if custom_tests:
        for custom_test in custom_tests:
            btn = InlineKeyboardButton(
                text=f"➕ {custom_test.name}",
                callback_data=f"test_pack_add_custom_test_{custom_test.id}",
            )
            keyboard.inline_keyboard.append([btn])

    button_back = InlineKeyboardButton(text="🔙 Back", callback_data="send_tests_pack")
    keyboard.inline_keyboard.append([button_back])

    await send_or_edit_message(message, text, keyboard, default_media)


@router.message(SendTestsPackState.NAMING_PACK)
async def wrong_naming_pack(message: types.Message) -> None:
    """
    Если пользователь ввёл что-то в состоянии NAMING_PACK, но это не текст,
    отправляем сообщение о необходимости ввести название для пака.
    """
    await message.answer("Please, write a name for your test pack to the chat.")


@router.callback_query(SendTestsPackState.CHOOSING_TESTS)
async def choosing_tests(callback_query: types.CallbackQuery, state: FSMContext) -> None:
    """
    Основной хендлер для состояния CHOOSING_TESTS:
    - Добавляет выбранный тест/кастомный тест в "пак",
    - Предлагает сохранить пак,
    - Или даёт возможность добавить ещё тестов.
    """
    await callback_query.answer("Command called")

    media = await get_gefault_media()
    all_tests = await get_tests()
    all_custom_tests = await get_custom_tests(callback_query.message.chat.id)

    # Получаем данные из state
    state_data = await state.get_data()
    log.debug(f"State data: {state_data}")

    # Инициализируем списки, если ещё не были
    if "tests" not in state_data:
        state_data["tests"] = []
    if "custom_tests" not in state_data:
        state_data["custom_tests"] = []

    # Добавление кастомного теста
    if callback_query.data.startswith("test_pack_add_custom_test_"):
        await confirm_custom_test_adding(callback_query, media)
        return
    
    # Добавление кастомного теста (подтверждение «Yes»)
    if callback_query.data.startswith("yes_add_custom_test_"):
        custom_test_id = callback_query.data.split("_")[-1]
        state_data["custom_tests"].append(custom_test_id)
        await state.update_data(custom_tests=state_data["custom_tests"])

    # Сохранение пака
    if callback_query.data == "test_pack_save":
        await save_test_pack(callback_query, state, all_tests, all_custom_tests)
        return

    # Добавление обычного теста (подтверждение «Yes»)
    if callback_query.data.startswith("test_pack_yes_add_test_"):
        test_id = callback_query.data.split("_")[-1]
        state_data["tests"].append(test_id)
        await state.update_data(tests=state_data["tests"])

    # Пользователь нажал «➕ {test.name}», показываем подтверждение добавления
    if callback_query.data.startswith("test_pack_add_test_"):
        await confirm_test_adding(callback_query, media)
        return

    # Генерируем сообщение и клавиатуру для повторного выбора тестов
    await send_choosing_tests_menu(
        callback_query,
        state_data,
        all_tests,
        all_custom_tests,
        media
    )


async def confirm_test_adding(callback_query: types.CallbackQuery, media: types.InputMedia) -> None:
    """
    Уточняет у пользователя, действительно ли он хочет добавить выбранный тест в пак.
    Показывает название и описание теста.
    """
    test_id = callback_query.data.split("_")[-1]
    async with db_helper.db_session() as session:
        test = await session.execute(select(Test).where(Test.id == test_id))
        test = test.scalar_one()

    text = f"{test.name}:\n{test.description}\n\nAdd test '{test.name}' to the pack?"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Yes", callback_data=f"test_pack_yes_add_test_{test.id}")],
        [types.InlineKeyboardButton(text="No", callback_data="test_pack_back_to_selection")]
    ])

    await send_or_edit_message(callback_query.message, text, keyboard, media)


async def confirm_custom_test_adding(callback_query: types.CallbackQuery, media: types.InputMedia) -> None:
    """
    Уточняет у пользователя, действительно ли он хочет добавить выбранный тест в пак.
    Показывает название и описание теста.
    """
    custom_test_id = callback_query.data.split("_")[-1]
    async with db_helper.db_session() as session:
        custom_test = await session.execute(select(CustomTest).where(CustomTest.id == custom_test_id))
        custom_test = custom_test.scalar_one()

    text = f"{custom_test.name}:\n{custom_test.description}\n\nAdd test '{custom_test.name}' to the pack?"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Yes", callback_data=f"yes_add_custom_test_{custom_test.id}")],
        [types.InlineKeyboardButton(text="No", callback_data="test_pack_back_to_selection")]
    ])

    await send_or_edit_message(callback_query.message, text, keyboard, media)


async def send_choosing_tests_menu(
    callback_query: types.CallbackQuery,
    state_data: dict,
    all_tests: list[Test],
    all_custom_tests: list[CustomTest],
    media: types.InputMedia
) -> None:
    """
    Формирует список уже добавленных тестов/кастомных тестов и предоставляет кнопки
    для добавления оставшихся. Также даёт возможность сохранить уже набранный «пак».
    """
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    text_parts = []

    # Собираем имена выбранных обычных тестов
    if state_data["tests"]:
        added_tests_names = [
            test.name for test in all_tests if str(test.id) in state_data["tests"]
        ]
        text_parts.append(f"Tests selected: \n{', '.join(added_tests_names)}")

    # Собираем имена выбранных кастомных тестов
    if state_data["custom_tests"]:
        added_custom_tests_names = [
            custom_test.name for custom_test in all_custom_tests
            if str(custom_test.id) in state_data["custom_tests"]
        ]
        text_parts.append(f"Custom tests selected: \n{', '.join(added_custom_tests_names)}")

    # «Шапка» перед новым списком
    text_parts.append("Choose a test to add to the pack:")

    # Список тестов, которые ещё не добавлены в пак
    remaining_tests = [t for t in all_tests if str(t.id) not in state_data["tests"]]
    for test in remaining_tests:
        btn = InlineKeyboardButton(text=f"➕ {test.name}", callback_data=f"test_pack_add_test_{test.id}")
        keyboard.inline_keyboard.append([btn])

    # Список кастомных тестов, ещё не добавленных в пак
    for custom_test in all_custom_tests:
        if str(custom_test.id) not in state_data["custom_tests"]:
            btn = InlineKeyboardButton(
                text=f"➕ {custom_test.name}",
                callback_data=f"test_pack_add_custom_test_{custom_test.id}"
            )
            keyboard.inline_keyboard.append([btn])

    # Если что-то уже выбрано — показываем кнопку «Сохранить»
    if state_data["tests"] or state_data["custom_tests"]:
        button_apply = InlineKeyboardButton(text="✅ Apply", callback_data="test_pack_save")
        keyboard.inline_keyboard.append([button_apply])

    # Если тестов больше нет
    if not remaining_tests and not any(
        str(ct.id) not in state_data["custom_tests"] for ct in all_custom_tests
    ):
        text_parts.append("\nNo more tests found.")

    button_back = InlineKeyboardButton(text="🔙 Back", callback_data="send_tests_pack")
    keyboard.inline_keyboard.append([button_back])

    # Соединяем все части текста в один блок
    text = "\n\n".join(text_parts)
    await send_or_edit_message(callback_query.message, text, keyboard, media)


async def save_test_pack(
    callback_query: types.CallbackQuery,
    state: FSMContext,
    all_tests: list[Test],
    all_custom_tests: list[CustomTest]
) -> None:
    """
    Сохраняет новый тест-пак в БД, очищает состояние, выводит пользователю ссылку на пак.
    """
    state_data = await state.get_data()
    # Если пользователь не добавил ни одного теста
    if not state_data.get("tests") and not state_data.get("custom_tests"):
        await callback_query.answer("Please, select at least one test.")
        return

    selected_tests = state_data.get("tests", [])
    selected_tests_objects = [t for t in all_tests if str(t.id) in selected_tests]

    selected_custom_tests = state_data.get("custom_tests", [])
    selected_custom_tests_objects = [ct for ct in all_custom_tests if str(ct.id) in selected_custom_tests]

    await state.clear()

    async with db_helper.db_session() as session:
        try:
            test_pack = TestPack(
                name=state_data["pack_name"],
                creator_id=callback_query.from_user.id,
                creator_username=callback_query.from_user.username,
                tests=selected_tests_objects,
                custom_tests=selected_custom_tests_objects
            )

            session.add(test_pack)
            await session.commit()

            bot_username = (await callback_query.bot.get_me()).username
            text = (
                f"✅ Test pack '{test_pack.name}' successfully created!\n"
                f"Test pack LINK: \n <code>https://t.me/{bot_username}?start={test_pack.id}</code>\n\n"
                f"Tests included: \n{', '.join([t.name for t in selected_tests_objects])}"
                f"\nCustom tests included: \n{', '.join([ct.name for ct in selected_custom_tests_objects])}"
            )
        except Exception as e:
            log.exception(f"Error saving test pack: {e}")
            await session.rollback()
            text = "❌ Error saving test pack. Please try again."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Back", callback_data="send_tests_pack")],
        [InlineKeyboardButton(text="Main Menu", callback_data="back_to_start")]
    ])

    media = await get_gefault_media()
    await send_or_edit_message(callback_query.message, text, keyboard, media)
