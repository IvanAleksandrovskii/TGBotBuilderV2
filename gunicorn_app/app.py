# gunicopn_app/application.py

from gunicorn.app.base import BaseApplication

from fastapi import FastAPI


class Application(BaseApplication):
    def __init__(
        self, 
        app: FastAPI, 
        options: dict,
        ):
        self.options = options
        self.application = app
        super().__init__()
    
    def load(self):
        return self.application
    
    @property
    def config_options(self) -> dict:
        return {
            # pair
            k: v
            # For each option 
            for k, v in self.options.items()
            # If the option is in the settings and value is not None
            if k in self.cfg.settings and v is not None
        }
    
    def load_config(self) -> dict:
        for key, value in self.config_options.items():
            if key in self.cfg.settings:
                self.cfg.set(key.lower(), value)
