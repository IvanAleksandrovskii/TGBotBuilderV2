# gunicorn_app/application_whith_multy_workers.py

from gunicorn.app.base import BaseApplication
from fastapi import FastAPI
import os


class Application(BaseApplication):
    def __init__(self, app: FastAPI, options: dict):
        self.options = options
        self.application = app
        super().__init__()

    def load(self):
        return self.application

    @staticmethod
    def worker_init(worker):
        worker.worker_id = worker.nr
        os.environ["WORKER_ID"] = str(worker.nr)

    @property
    def config_options(self) -> dict:
        options = self.options.copy()
        options["worker_init"] = self.worker_init
        return {
            k: v for k, v in options.items() if k in self.cfg.settings and v is not None
        }

    def load_config(self):
        for key, value in self.config_options.items():
            if key in self.cfg.settings:
                self.cfg.set(key.lower(), value)
