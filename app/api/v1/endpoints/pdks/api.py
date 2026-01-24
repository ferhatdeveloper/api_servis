"""
PDKS Ana API Router
Modülleri birleştiren merkezi router yapılandırması.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.pdks_dependencies import get_db
from app.api.v1.endpoints.pdks import health, realtime, database, example, test_endpoints, departments, performance, auto_index, file_upload, hikvision, email_settings

# Ana router
router = APIRouter(prefix="/api", tags=["API"])

# Alt router'ları dahil et
router.include_router(health.router)
router.include_router(realtime.router)
router.include_router(database.router)
router.include_router(example.router)
router.include_router(test_endpoints.router)
router.include_router(departments.router)
router.include_router(performance.router)
router.include_router(auto_index.router)
router.include_router(file_upload.router)
router.include_router(hikvision.router)
router.include_router(email_settings.router)


@router.get("/")
async def root():
    """
    **Kök Dizin**

    Servis durumu ve versiyon bilgisini döner.
    """
    return {
        "message": "EXFIN FastAPI Servisi",
        "version": "1.0.0",
        "status": "active"
    }


@router.get("/info")
async def info():
    """
    **Sistem Bilgileri**

    Aktif veritabanı, çalışma modu ve özellik durumlarını raporlar.
    """
    from app.core import config_manager
    
    return {
        "default_database": config_manager.app_config.Default,
        "developer_mode": config_manager.app_config.DeveloperMode,
        "realtime_enabled": config_manager.app_config.RealtimeEnabled,
        "available_databases": list(config_manager.databases.keys())
    }
