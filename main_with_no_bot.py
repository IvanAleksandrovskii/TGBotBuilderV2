# main.py

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    
    log.info("Starting up the FastAPI application...")
    await client_manager.start()
    
    yield
    
    log.info("Shutting down the FastAPI application...")
    
    await db_helper.dispose()
    await async_sqladmin_db_helper.dispose()
    await client_manager.dispose_all_clients()
    log.info("Application shutdown complete")


main_app = FastAPI(
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)


from api import router as api_router
main_app.include_router(api_router)


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
