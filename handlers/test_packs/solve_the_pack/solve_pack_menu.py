# handlers/test_packs/solve_the_pack/solve_pack_menu.py

# from uuid import UUID
# from sqlalchemy.orm import selectinload

from aiogram import Router, types, F
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from jinja2 import Environment, FileSystemLoader

from core import log
from core.models import (
    db_helper,
    TestPackCompletion,
)
from handlers.utils import send_or_edit_message, get_default_media
# from handlers.test_packs.solve_the_pack.notifications_for_creator import notify_creator


router = Router()


# jinja environment
env = Environment(
    loader=FileSystemLoader("handlers/test_packs/solve_the_pack/templates")
)


async def get_solve_test_menu():
    
    raise NotImplementedError
