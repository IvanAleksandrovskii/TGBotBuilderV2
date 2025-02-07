# gunicorn_app/bot_options.py

from core import settings


def get_bot_options(
    host: str = settings.run.host,
    # port: int = settings.run.port,
    port: int = 8080,
    workers: int = 1,
    timeout: int = settings.run.timeout,
) -> dict:
    return {
        "bind": f"{host}:{port}",
        "workers": workers,
        "worker_class": "uvicorn.workers.UvicornWorker",
        "timeout": timeout,
    }
