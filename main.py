# main.py

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from fastapi.responses import ORJSONResponse, JSONResponse
from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles
import uvicorn

from core.models import db_helper

# from sqladmin import Admin
# from core.admin import async_sqladmin_db_helper, sqladmin_authentication_backend
# from core.admin.models import setup_admin

from core import settings, log

from handlers import router as main_router


# TODO: Add signit signal handler for graceful shutdown
# TODO: Add admin panel, storages 


# Initialize bot and dispatcher
def setup_bot():
    session = AiohttpSession(timeout=60)
    bot = Bot(token=settings.bot.token, session=session)
    dp = Dispatcher()
    dp.include_router(main_router)
    return bot, dp

# Global variables for bot and dispatcher
bot = None
dp = None
polling_task = None

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global bot, dp, polling_task
    # Startup
    log.info("Starting up the FastAPI application...")

    # Initialize bot and dispatcher
    bot, dp = setup_bot()
    
    # Start polling in a separate task
    polling_task = asyncio.create_task(dp.start_polling(bot))

    yield

    # Shutdown
    log.info("Shutting down the FastAPI application...")

    await db_helper.dispose()
    # await async_sqladmin_db_helper.dispose()

    # Stop polling
    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass

    # Close bot session
    if bot:
        await bot.session.close()

    log.info("Bot stopped successfully")


main_app = FastAPI(
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

# Mount media storage
# main_app.mount("/media/", StaticFiles(directory=settings.media.root[4:]), name="media")

# SQLAdmin
# admin = Admin(main_app, engine=async_sqladmin_db_helper.engine, authentication_backend=sqladmin_authentication_backend)

# Register admin views
# setup_admin(admin)


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


if __name__ == '__main__':
    uvicorn.run("main:main_app",
        host=settings.run.host,
        port=settings.run.port,
        reload=settings.run.debug,
    )
