# handlers/on_start.py

from aiogram import Router, Bot, types
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

from sqlalchemy import select

from icecream import ic

from core import log
from core.models import User, db_helper


# ic.disable()


router = Router()


class FirstGreetingStates(StatesGroup):
    GREETING = State()


# @alru_cache(ttl=settings.bot.max_users_cached_time_seconds, maxsize=settings.bot.max_users_cached)
async def get_user_from_db(chat_id: int) -> User | None:
    async for session in db_helper.session_getter():
        try:
            user_from_db = await session.execute(select(User).where(User.chat_id == chat_id))
            user_from_db = user_from_db.scalar_one_or_none()

            return user_from_db

        except Exception as e:
            log.exception("Error in get_user_from_db: %s", e)
            return None
        finally:
            await session.close()


@router.message(Command("start"))
async def start_command(message: types.Message, bot: Bot):
    """
    Обработчик команды /start с поддержкой deep linking параметров
    """
    ic(message)
    
    # Получаем аргументы после команды start
    args = message.text.split()[1:]  # Разделяем сообщение на части и берём всё после /start
    ic(args)
    
    bot_info = await bot.get_me()
    ic(bot_info)
    
    
    if args:
        # Если есть параметры, берем первый
        start_parameter = args[0]
        await message.reply(f"Получен параметр: {start_parameter}\n\
Ссылка на бота с коммандой: 'https://t.me/{bot_info.username}?start={start_parameter}'")
    else:
        # Если параметров нет
        await message.reply("Команда /start без параметров")
