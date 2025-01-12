from aiogram import Router

router = Router()

from .send_tests_pack import router as send_tests_pack_router
router.include_router(send_tests_pack_router)
