from aiogram import Router


router = Router()

from .on_start import router as on_start_router
from .admin import router as admin_router

from .promocode import router as promocode_router

router.include_router(on_start_router)
router.include_router(admin_router)

router.include_router(promocode_router)
