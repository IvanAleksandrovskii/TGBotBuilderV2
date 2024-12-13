# main.py

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator


from aiogram import Bot, Dispatcher
from aiogram.types import WebhookInfo, Update
from aiogram.client.bot import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

from fastapi.responses import ORJSONResponse, JSONResponse
from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles
import uvicorn

from sqladmin import Admin

from core import log, settings
from core.models import db_helper

from core.admin import async_sqladmin_db_helper, sqladmin_authentication_backend
from core.admin.models import setup_admin
from core.models import client_manager

from handlers import router as main_router


# TODO: Make nginx to balance the load and let to start with multiple gunicorn worlers to pass the Telegram API limits

class BotWebhookManager:
    def __init__(self):
        self.bot = None
        self.dp = None
        self.webhook_url = None
        self.webhook_handler = None
        
    async def setup(self, token: str, webhook_host: str, webhook_path: str, router):
        """Initialize bot and webhook configuration"""
        session = AiohttpSession(timeout=60)
        self.bot = Bot(token=token, session=session, default=DefaultBotProperties(parse_mode='HTML'))
        self.dp = Dispatcher()
        self.dp.include_router(router)
        
        # URL for webhook
        self.webhook_url = f"{webhook_host}{webhook_path}"
        
    async def start_webhook(self):
        """Set webhook for the bot"""
        await self.bot.delete_webhook(drop_pending_updates=True)
        await self.bot.set_webhook(
            url=self.webhook_url,
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
        
        webhook_info: WebhookInfo = await self.bot.get_webhook_info()
        if not webhook_info.url:
            raise RuntimeError("Webhook setup failed!")
        
        logging.info(f"Webhook was set to URL: {webhook_info.url}")
        
    async def stop_webhook(self):
        """Remove webhook and cleanup"""
        if self.bot:
            await self.bot.delete_webhook()
            await self.bot.session.close()

    async def handle_webhook_request(self, request: Request):
        """Handle incoming webhook request from FastAPI"""
        try:
            # Get data from request
            data = await request.json()
            
            # Create Update object from received data
            update = Update(**data)
            
            # Process update
            await self.dp.feed_webhook_update(self.bot, update)
            
            return Response(status_code=200)
        except Exception as e:
            log.error(f"Error processing webhook update: {e}", exc_info=True)
            return Response(status_code=500)

# Global bot manager instance
bot_manager = BotWebhookManager()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log.info("Starting up the FastAPI application...")
    
    await bot_manager.setup(
        token=settings.bot.token,
        webhook_host=settings.media.base_url,
        webhook_path=settings.webhook.path,
        router=main_router
    )
    await bot_manager.start_webhook()
    
    await client_manager.start()
    
    yield
    
    log.info("Shutting down the FastAPI application...")
    await bot_manager.stop_webhook()
    await db_helper.dispose()
    await async_sqladmin_db_helper.dispose()
    
    log.info("Application shutdown complete")
    
    await client_manager.dispose_all_clients()

main_app = FastAPI(
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

@main_app.post("/webhook/bot/")
async def handle_webhook(request: Request):
    """Endpoint для обработки вебхуков от Telegram"""
    return await bot_manager.handle_webhook_request(request)


# Mount media storage
main_app.mount("/app/media/", StaticFiles(directory=settings.media.root[4:]), name="media")

main_app.mount("/app/media/quiz/", StaticFiles(directory=settings.media.quiz_media[4:]), name="quiz_media")

# SQLAdmin
admin = Admin(main_app, engine=async_sqladmin_db_helper.engine, authentication_backend=sqladmin_authentication_backend)

# Register admin views
setup_admin(admin)


# Favicon.ico errors silenced
@main_app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return Response(status_code=204)


# Global exception handler
@main_app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        if request.url.path == "/favicon.ico":
            return Response(status_code=204)

        if isinstance(exc, ValueError) and "badly formed hexadecimal UUID string" in str(exc):
            return Response(status_code=204)

        log.error("Unhandled exception: %s", str(exc))
        return JSONResponse(
            status_code=500,
            content={"message": "Internal server error"}
        )


class NoFaviconFilter(logging.Filter):
    def filter(self, record):
        return not any(x in record.getMessage() for x in ['favicon.ico', 'apple-touch-icon'])


logging.getLogger("uvicorn.access").addFilter(NoFaviconFilter())

# CORS
main_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# This is fix for sqladmin with https
@main_app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "upgrade-insecure-requests"
    return response


if __name__ == '__main__':
    uvicorn.run("main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=settings.run.debug,
        forwarded_allow_ips='*',  # Added this for htts fix
        proxy_headers=True 
    )
