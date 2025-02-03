__all__ = [
    "router",
    "inside_the_custom_test",
]

from .inside_the_custom_test import inside_the_custom_test

from aiogram import Router

router = Router()


from .inside_the_custom_test import router as inside_the_custom_test_router
router.include_router(inside_the_custom_test_router)


from .inside_the_psychological_test import router as inside_the_psychological_test_router
router.include_router(inside_the_psychological_test_router)
