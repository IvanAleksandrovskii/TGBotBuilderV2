# main_with_multy_workers.py

import os
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
from gunicorn_app.bot_webhook_manager import BotWebhookManager


# TODO: Make possible to start up with multiple workers


bot_manager = BotWebhookManager()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    log.info("Starting up the FastAPI application...")

    # Инициализируем webhook только на воркере с WORKER_ID == 0
    worker_id = int(os.environ.get("WORKER_ID", "0"))
    if worker_id == 0:
        log.info(f"Initializing bot on worker {worker_id}")
        await bot_manager.setup(
            token=settings.bot.token,
            webhook_host=settings.media.base_url,
            webhook_path=settings.webhook.path,
            router=main_router
        )
        await bot_manager.start_webhook()
    else:
        log.info(f"Skipping bot initialization on worker {worker_id}")

    await client_manager.start()

    yield

    log.info("Shutting down the FastAPI application...")
    if worker_id == 0:
        await bot_manager.stop_webhook()

    await db_helper.dispose()
    await async_sqladmin_db_helper.dispose()
    await client_manager.dispose_all_clients()
    log.info(f"Application shutdown complete on worker {worker_id}")

main_app = FastAPI(
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

# Эндпоинт для вебхуков Telegram
@main_app.post("/webhook/bot/", tags=["tg"])
async def handle_webhook(request: Request):
    worker_id = int(os.environ.get("WORKER_ID", "0"))
    if worker_id != 0:
        log.warning(f"Webhook request received on non-bot worker {worker_id}")
        return Response(status_code=404)
    return await bot_manager.handle_webhook_request(request)


# Add debug endpoint
@main_app.get("/debug/worker-info")
async def get_worker_info():
    """Debug endpoint to check worker ID"""
    return {"worker_id": os.environ.get("WORKER_ID", "unknown"), "pid": os.getpid()}


from api import router as api_router

main_app.include_router(api_router)


# Mount media storage
main_app.mount(
    "/app/media/", StaticFiles(directory=settings.media.root[4:]), name="media"
)
main_app.mount(
    "/app/media/quiz/",
    StaticFiles(directory=settings.media.quiz_media[4:]),
    name="quiz_media",
)

# SQLAdmin
admin = Admin(
    main_app,
    engine=async_sqladmin_db_helper.engine,
    authentication_backend=sqladmin_authentication_backend,
)

# Register admin views
setup_admin(admin)


# Favicon.ico errors silenced
@main_app.get("/favicon.ico", include_in_schema=False)
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

        if isinstance(
            exc, ValueError
        ) and "badly formed hexadecimal UUID string" in str(exc):
            return Response(status_code=204)

        log.error("Unhandled exception: %s", str(exc))
        return JSONResponse(
            status_code=500, content={"message": "Internal server error"}
        )


class NoFaviconFilter(logging.Filter):
    def filter(self, record):
        return not any(
            x in record.getMessage() for x in ["favicon.ico", "apple-touch-icon"]
        )


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
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = "upgrade-insecure-requests"
    return response


if __name__ == "__main__":
    uvicorn.run(
        "main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=settings.run.debug,
        forwarded_allow_ips="*",  # Added this for htts fix
        proxy_headers=True,
    )
