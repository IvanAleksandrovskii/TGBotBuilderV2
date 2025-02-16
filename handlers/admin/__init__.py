__all__ = [
    "router"
]

from aiogram import Router


router = Router()

from .broadcast import router as broadcast_router
router.include_router(broadcast_router)

from .broadcast_direct import router as broadcast_direct_router
router.include_router(broadcast_direct_router)
