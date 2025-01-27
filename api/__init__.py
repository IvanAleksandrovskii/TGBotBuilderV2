
from fastapi import APIRouter

from .create_custom_test import router as create_custom_test_router
from .get_custom_tests import router as get_custom_tests_router
from .update_custom_test import router as update_custom_test_router
from .delete_custom_tests import router as delete_custom_tests_router

from .test_packs import router as test_packs_router

from .get_tests import router as get_tests_router


router = APIRouter(prefix="/api")
router.include_router(create_custom_test_router)
router.include_router(get_custom_tests_router)
router.include_router(update_custom_test_router)
router.include_router(delete_custom_tests_router)
router.include_router(test_packs_router)
router.include_router(get_tests_router)
