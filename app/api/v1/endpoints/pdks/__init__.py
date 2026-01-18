from fastapi import APIRouter

from . import departments, hikvision, performance, realtime, file_upload, health, email_settings, auto_index

router = APIRouter()

router.include_router(departments.router)
router.include_router(hikvision.router)
router.include_router(performance.router)
router.include_router(realtime.router)
router.include_router(file_upload.router)
router.include_router(health.router)
router.include_router(email_settings.router)
router.include_router(auto_index.router)
