__all__ = [
    "router",
    "start_solve_the_pack",
    "SolveThePackStates",
    "notify_creator",
]

from .start_the_pack import start_solve_the_pack, SolveThePackStates
from .notifications_for_creator import notify_creator

from aiogram import Router

router = Router()

from .start_the_pack import router as solve_the_pack_router
router.include_router(solve_the_pack_router)

from .solve_test import router as solve_test_router
router.include_router(solve_test_router)

from .solve_pack_menu import router as solve_pack_menu_router
router.include_router(solve_pack_menu_router)

from .final_all_tests_done import router as final_all_tests_done_router
router.include_router(final_all_tests_done_router)
