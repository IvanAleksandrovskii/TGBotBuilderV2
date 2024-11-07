from aiogram import Router


router = Router()

from .on_start import router as on_start_router
from .admin import router as admin_router

from .promocode import router as promocode_router

from .universal_page import router as universal_page_router

router.include_router(on_start_router)
router.include_router(admin_router)

router.include_router(promocode_router)
router.include_router(universal_page_router)

from .dice import router as test_router
router.include_router(test_router)

from .ai_chat import router as ai_chat_router
router.include_router(ai_chat_router)
