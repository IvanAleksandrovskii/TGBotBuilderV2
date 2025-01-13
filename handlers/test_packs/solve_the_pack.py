# handlers/test_packs/solve_the_pack.py

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
# from handlers.v1.utils import send_or_edit_message

router = Router()


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
        one_time_keyboard=True
    )
    return keyboard


@router.message(Command("solve_the_pack"))
async def solve_the_pack(message: types.Message) -> None:
    await message.answer(
        "Привет! Нажми на кнопку ниже, чтобы поделиться контактом (это нужно, чтобы отправитель смог понять, кто вы и связать вас с ним):",
        reply_markup=get_contact_keyboard()
    )


# Обработчик получения контакта
@router.message(F.contact)
async def handle_contact(message: types.Message):
    # Получаем информацию о контакте
    phone = message.contact.phone_number
    first_name = message.contact.first_name
    last_name = message.contact.last_name if message.contact.last_name else "Не указано"
    user_id = message.contact.user_id
    username = message.from_user.username if message.from_user.username else "Не указано"
    vcard = message.contact.vcard if message.contact.vcard else "Не указано"

    # Отправляем сообщение с информацией о полученном контакте
    await message.answer(
        f"Спасибо! Получен контакт:\n"
        f"Телефон: {phone}\n"
        f"Имя: {first_name}\n"
        f"Фамилия: {last_name}\n"
        f"ID пользователя: {user_id}\n"
        f"Username: @{username}\n"
        f"VCard: {vcard}",
        reply_markup=types.ReplyKeyboardRemove()
    )
