import asyncio
import logging
from aiogram.exceptions import TelegramRetryAfter
from aiogram.types import WebhookInfo


class BotWebhookManager:
    def __init__(self):
        self.bot = None
        self.dp = None
        self.webhook_url = None

    async def setup(self, token: str, webhook_host: str, webhook_path: str, router):
        """Инициализировать бота и настройки вебхука"""
        from aiogram.client.session.aiohttp import AiohttpSession
        from aiogram import Bot, Dispatcher

        session = AiohttpSession(timeout=60)
        self.bot = Bot(token=token, session=session)
        self.dp = Dispatcher()
        self.dp.include_router(router)
        self.webhook_url = f"{webhook_host}{webhook_path}"

    async def start_webhook(self):
        """Устанавливает webhook с обработкой ошибок flood control"""
        try:
            current_info: WebhookInfo = await self.bot.get_webhook_info()
            if current_info.url == self.webhook_url:
                logging.info(
                    "Webhook уже установлен на нужный URL, повторная настройка не требуется."
                )
                return
        except Exception as e:
            logging.warning(f"Не удалось получить текущий webhook: {e}")

        # Удаляем предыдущий webhook
        await self.bot.delete_webhook(drop_pending_updates=True)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                await self.bot.set_webhook(
                    url=self.webhook_url,
                    allowed_updates=["message", "callback_query"],
                    drop_pending_updates=True,
                )
                break  # Успех – выходим из цикла
            except TelegramRetryAfter as e:
                wait_time = e.retry_after * (attempt + 1)  # экспоненциальная задержка
                logging.info(
                    f"Telegram rate limit reached. Retrying after {wait_time} seconds (attempt {attempt+1} of {max_retries})."
                )
                await asyncio.sleep(wait_time)
            except Exception as e:
                logging.error(f"Ошибка при установке webhook: {e}", exc_info=True)
                break

        # Проверяем, что webhook установлен корректно
        webhook_info: WebhookInfo = await self.bot.get_webhook_info()
        if webhook_info.url != self.webhook_url:
            raise RuntimeError("Webhook setup failed!")
        logging.info(f"Webhook установлен на URL: {webhook_info.url}")

    async def stop_webhook(self):
        """Удаляет webhook и очищает ресурсы"""
        logging.info("Остановка webhook...")
        if self.bot:
            await self.bot.delete_webhook()
            await self.bot.session.close()

    async def handle_webhook_request(self, request):
        """Обработка входящего запроса"""
        from fastapi import Response, Request

        try:
            data = await request.json()
            from aiogram.types import Update

            update = Update(**data)
            await self.dp.feed_webhook_update(self.bot, update)
            return Response(status_code=200)
        except Exception as e:
            logging.error(f"Ошибка обработки webhook: {e}", exc_info=True)
            return Response(status_code=500)
