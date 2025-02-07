# run_bot.py

from bot import bot_app
from gunicorn_app.app import Application
from gunicorn_app.bot_options import get_bot_options


if __name__ == "__main__":
    options = get_bot_options()
    Application(bot_app, options).run()
