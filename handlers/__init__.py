from aiogram import Router


router = Router()

from .back_to_start import router as back_to_start_router
router.include_router(back_to_start_router)

from .v1 import router as v1_router
router.include_router(v1_router)

from .test_packs import router as send_tests_pack_router
router.include_router(send_tests_pack_router)

from .abort import router as abort_router
router.include_router(abort_router)


from .fallback import router as fallback_router
router.include_router(fallback_router)
