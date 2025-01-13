
from fastapi import APIRouter

from .create_custom_test import router as create_custom_test_router


router = APIRouter(prefix="/api")
router.include_router(create_custom_test_router)
