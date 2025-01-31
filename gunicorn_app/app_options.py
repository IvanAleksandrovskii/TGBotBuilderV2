# gunicorn_app/application_options.py

from core import settings


def get_app_options(
    host: str = settings.run.host,
    port: int = settings.run.port,
    workers: int = settings.run.workers,
    timeout: int = settings.run.timeout,
) -> dict:
    return {
        "bind": f"{host}:{port}",
        "workers": workers,
        "worker_class": "uvicorn.workers.UvicornWorker",
        "timeout": timeout,
        "preload_app": False,  # Важно для правильной инициализации воркеров
    }
