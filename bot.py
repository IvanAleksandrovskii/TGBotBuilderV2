# bot.py

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties


from core import log, settings
from handlers import router as main_router


async def start_bot():
    """Start bot"""
    log.info("Initializing bot...")
    bot = Bot(token=settings.bot.token, default=DefaultBotProperties(parse_mode="HTML"))

    # Очищаем старые апдейты перед запуском
    await bot.delete_webhook(drop_pending_updates=True)

    dp = Dispatcher()
    dp.include_router(main_router)
    log.info("Starting bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start_bot())
