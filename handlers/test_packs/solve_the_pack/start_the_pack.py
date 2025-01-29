# handlers/test_packs/solve_the_pack.py

from uuid import UUID

from sqlalchemy.orm import selectinload

from aiogram import Router, types, F
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from jinja2 import Environment, FileSystemLoader

from core import log
from core.models import (
    db_helper,
    TestPack,
    )
from handlers.utils import ( 
    send_or_edit_message,
    get_default_media
    )
from handlers.test_packs.solve_the_pack.notifications_for_creator import notify_creator


router = Router()


# jinja environment
env = Environment(loader=FileSystemLoader('handlers/test_packs/solve_the_pack/templates'))


class SolveThePackStates(StatesGroup):  # Do not forget, got this states in on_start for the start forbidden check
    WELCOME = State()
    SOLVING = State()
    ANSWERING_TEST = State()
    COMPLETING = State()


# Создаем клавиатуру с кнопкой запроса контакта
def get_contact_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="Поделиться контактом 📱",
                    request_contact=True
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard


async def start_solve_the_pack(message: types.Message, test_pack_id: UUID, state: FSMContext) -> None:
    default_media = await get_default_media()
    welcome_text = env.get_template("welcome.html").render()
    await send_or_edit_message(message, welcome_text, None, default_media)
    
    # TODO: Check if user has the same test pack but not completed it yet
    # TODO: Check if test pack is not completed or user has already completed it
    
    test_pack = None
    async with db_helper.db_session() as session:
        try:
            test_packs_query = (
                TestPack.active()
                .where(TestPack.id == test_pack_id)
                .options(selectinload(TestPack.tests), selectinload(TestPack.custom_tests))
            )
            test_pack = await session.execute(test_packs_query)
            test_pack = test_pack.scalar_one_or_none()
        
        except Exception as e:  
            log.exception(f"Error in start_solve_the_pack: {e}")
            await message.answer("An error occurred while fetching test pack.")
            state.clear()
            return
    
    if test_pack:
        await state.set_state(SolveThePackStates.WELCOME)
        await state.update_data(test_pack_id=test_pack_id)
        await state.update_data(test_pack_name=test_pack.name)
        await state.update_data(test_pack_creator_id=int(test_pack.creator_id))
        
        tests_names_string = ""
        
        if len(test_pack.tests) > 0:
            tests_names_string += "<strong>Психологические тесты:</strong>\n"
            for test in test_pack.tests:
                tests_names_string += f"  - {test.name}\n"
            tests_names_string += "\n"
        
        if len(test_pack.custom_tests) > 0:
            tests_names_string += "<strong>Пользовательские тесты:</strong>\n"
            for custom_test in test_pack.custom_tests:
                tests_names_string += f"  - {custom_test.name}\n"
            tests_names_string += "\n"
    
        text = env.get_template("start_the_test.html").render(
            test_names_string=tests_names_string
        )
    
        await message.answer(
            text=text,  
            reply_markup=get_contact_keyboard()
        )
    else:
        await message.answer("Test pack not found. Ask the creator to share the new link. Press -> /start to use the bot.")  # TODO: Move to config


# Обработчик получения контакта
@router.message(SolveThePackStates.WELCOME, F.contact)  # TODO: Продолжить... 
async def handle_contact(message: types.Message, state: FSMContext):
    
    # Get the test pack ID from the state
    data = await state.get_data()
    test_pack_id = data['test_pack_id']
    test_pack_name = data['test_pack_name']
    test_pack_creator_id = data['test_pack_creator_id']
    
    # Set state to solving
    await state.set_state(SolveThePackStates.SOLVING)
    
    # Получаем информацию о контакте
    phone = message.contact.phone_number
    first_name = message.contact.first_name
    last_name = message.contact.last_name if message.contact.last_name else "Не указано"
    user_id = message.contact.user_id
    username = message.from_user.username if message.from_user.username else "Не указано"
    
    # Notify creator
    await notify_creator(
        message, 
        test_pack_creator_id, 
        f"started solving the test pack {test_pack_name}\n\nUsed Contact:\n"
        f" - Username: {f"@{username}" if username else "Не указано"}\n"
        f" - Phone: {phone}\n"
        f" - First name: {first_name}\n"
        f" - Last name: {last_name}\n"
        )
    
    """
    TODO: Создать модель для хранения данных о прохождении тестов и о пользователях
    Сделать систему нотификаций создателя тестпака о прохождении тестов и о результатах тестов, 
    а так же сбор резюме у пользователей и их пересылка их создателю
    """
    
    # TODO: Сделать меню выбора тестов для прохождения
    
    # Отправляем сообщение с информацией о полученном контакте
    # await message.answer(
    #     f"Спасибо! Получен контакт:\n"
    #     f"Телефон: {phone}\n"
    #     f"Имя: {first_name}\n"
    #     f"Фамилия: {last_name}\n"
    #     f"ID пользователя: {user_id}\n"
    #     f"Username: @{username}\n"
        
    #     f"Test pack ID: {test_pack_id}",
        
    #     reply_markup=types.ReplyKeyboardRemove()
    # )
