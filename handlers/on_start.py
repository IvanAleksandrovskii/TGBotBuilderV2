# handlers/on_start.py

from aiogram import Router, Bot, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from icecream import ic


# ic.disable()


router = Router()


@router.message(Command("start"))
async def start_command(message: types.Message):
    """
    Обработчик команды /start с поддержкой deep linking параметров
    """
    ic(message)
    
    # Получаем аргументы после команды start
    args = message.text.split()[1:]  # Разделяем сообщение на части и берём всё после /start
    ic(args)
    
    
    if args:
        # Если есть параметры, берем первый
        start_parameter = args[0]
        await message.reply(f"Получен параметр: {start_parameter}")
    else:
        # Если параметров нет
        await message.reply("Команда /start без параметров")
