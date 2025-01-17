from aiogram import Router

router = Router()

from .send_tests_pack import router as send_tests_pack_router
router.include_router(send_tests_pack_router)

from .create_pack import router as create_pack_router
router.include_router(create_pack_router)

from .packs_list import router as packs_list_router
router.include_router(packs_list_router)

from .check_results import router as check_results_router
router.include_router(check_results_router)

from .solve_the_pack import router as solve_the_pack_router
router.include_router(solve_the_pack_router)

# from .custom_tests import router as custom_tests_router
# router.include_router(custom_tests_router)
