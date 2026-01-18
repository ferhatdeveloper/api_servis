"""
Health check endpoints
"""
from fastapi import APIRouter, status, HTTPException
from app.core.pdks_database import engine, get_db
# config_manager missing in OPS, logic adapted to use available resources
# or simplified.
from sqlalchemy import text

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/")
async def health_check():
    """Genel sistem durumu kontrolü"""
    # Simply check engine connection
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_connected = True
    except:
        db_connected = False
    
    return {
        "status": "healthy" if db_connected else "degraded",
        "service": "EXFIN PDKS API Module",
        "realtime": True, # Assume enabled
        "databases": {
            "total": 1,
            "connected": 1 if db_connected else 0,
            "failed": 0 if db_connected else 1
        }
    }


@router.get("/databases")
async def check_databases():
    """Veritabanı bağlantı durumları"""
    status_map = {}
    
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status_map["PostgreSQL"] = {
            "status": "connected",
            "type": "PostgreSQL"
        }
    except Exception as e:
        status_map["PostgreSQL"] = {
            "status": "disconnected",
            "error": str(e)
        }
    
    return status_map
