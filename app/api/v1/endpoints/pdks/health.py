"""
Health check endpoints
"""
from fastapi import APIRouter, status, HTTPException
from app.core.pdks_core_database import database_manager
from app.core.pdks_config import config_manager

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
async def health_check():
    """Genel sistem durumu kontrolü"""
    connection_status = database_manager.get_connection_status()
    
    return {
        "status": "healthy" if connection_status["connected"] > 0 else "degraded",
        "service": "EXFIN FastAPI",
        "realtime": config_manager.app_config.RealtimeEnabled,
        "databases": {
            "total": connection_status["total"],
            "connected": connection_status["connected"],
            "failed": len(connection_status["failed"])
        }
    }


@router.get("/databases")
async def check_databases():
    """Veritabanı bağlantı durumları"""
    status_map = {}
    
    for db_name in config_manager.databases.keys():
        try:
            from sqlalchemy import text
            engine = database_manager.get_engine(db_name)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            status_map[db_name] = {
                "status": "connected",
                "type": config_manager.databases[db_name].Type
            }
        except Exception as e:
            status_map[db_name] = {
                "status": "disconnected",
                "error": str(e)
            }
    
    return status_map
