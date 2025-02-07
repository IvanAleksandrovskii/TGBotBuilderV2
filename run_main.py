# run_main.py

from main_with_no_bot import main_app
from gunicorn_app.app import Application
from gunicorn_app.app_options import get_app_options


if __name__ == "__main__":
    options = get_app_options()
    Application(main_app, options).run()
