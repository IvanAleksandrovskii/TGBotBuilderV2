from aiogram import Router


router = Router()

from .on_start import router as on_start_router
from .broadcast import router as admin_router

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

from .ai_chat_with_memory import router as ai_chat_with_memory_router
router.include_router(ai_chat_with_memory_router)

from .reader import router as reader_router
router.include_router(reader_router)

from .quiz import router as quiz_router
router.include_router(quiz_router)

from .direct_broadcast import router as direct_broadcast_router
router.include_router(direct_broadcast_router)

from .send_test import router as send_test_router
router.include_router(send_test_router)
