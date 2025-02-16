from aiogram import Router


router = Router()


from .on_start import router as on_start_router
router.include_router(on_start_router)

from .quiz import router as quiz_router
router.include_router(quiz_router)

from .admin import router as admin_router
router.include_router(admin_router)

from .back_to_start import router as back_to_start_router
router.include_router(back_to_start_router)

from .v1 import router as v1_router
router.include_router(v1_router)

from .test_packs import router as send_tests_pack_router
router.include_router(send_tests_pack_router)

from .abort import router as abort_router
router.include_router(abort_router)


from .universal_page import router as universal_page_router
router.include_router(universal_page_router)

from .reader import router as reader_router
router.include_router(reader_router)


from .fallback import router as fallback_router
router.include_router(fallback_router)
