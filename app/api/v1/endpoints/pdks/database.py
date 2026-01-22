"""
Veritabanı işlemleri endpoints
"""
from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.core.pdks_dependencies import get_db
from app.core.pdks_config import config_manager
from app.core.pdks_core_database import database_manager

router = APIRouter(prefix="/database", tags=["Database"])


@router.get("/list")
async def list_databases():
    """Kullanılabilir veritabanlarını listele"""
    databases = []
    connection_status = database_manager.get_connection_status()
    
    for db_name, db_config in config_manager.databases.items():
        is_connected = db_name in database_manager.successful_connections
        databases.append({
             "name": db_name,
             "type": db_config.Type,
             "database": db_config.Database,
             "server": getattr(db_config, 'Server', 'N/A'),
             "description": getattr(db_config, 'Description', ''),
             "is_default": db_name == config_manager.app_config.Default,
             "is_connected": is_connected,
             "error": database_manager.failed_connections.get(db_name) if not is_connected else None
         })
    
    return {
        "databases": databases,
        "default": config_manager.app_config.Default,
        "total": connection_status["total"],
        "connected": connection_status["connected"],
        "failed": len(connection_status["failed"])
    }


@router.get("/query/{db_name}")
async def execute_query(
    db_name: str,
    query: str = Query(..., description="SQL sorgusu")
):
    """
    SQL sorgusu çalıştır (GÜVENLİK UYARISI: Üretim ortamında kullanmayın)
    """
    if not config_manager.app_config.DeveloperMode:
        return {
            "error": "Bu endpoint sadece developer mode'da çalışır"
        }
    
    # Belirli veritabanı için oturum oluştur
    db: Session = next(get_db(db_name=db_name))
    
    try:
        from sqlalchemy import text
        
        # Query tipini kontrol et (INSERT/UPDATE/DELETE için commit gerekli)
        query_upper = query.strip().upper()
        is_modifying_query = any(
            query_upper.startswith(cmd) 
            for cmd in ['INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        )
        
        result = db.execute(text(query))
        
        # Modifying query ise commit yap
        if is_modifying_query:
            db.commit()
        
        # SELECT query için sonuçları formatla
        if query_upper.startswith('SELECT'):
            columns = result.keys()
            rows = []
            for row in result:
                rows.append(dict(zip(columns, row)))
            
            return {
                "status": "success",
                "database": db_name,
                "rows_count": len(rows),
                "data": rows
            }
        else:
            # INSERT/UPDATE/DELETE için RETURNING clause varsa sonuçları döndür
            try:
                columns = result.keys()
                rows = []
                for row in result:
                    rows.append(dict(zip(columns, row)))
                
                return {
                    "status": "success",
                    "database": db_name,
                    "rows_count": len(rows),
                    "data": rows
                }
            except:
                # RETURNING yoksa sadece başarı mesajı
                return {
                    "status": "success",
                    "database": db_name,
                    "rows_count": result.rowcount if hasattr(result, 'rowcount') else 0,
                    "data": []
                }
    
    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "database": db_name,
            "message": str(e)
        }
    finally:
        db.close()


@router.get("/status")
async def get_connection_status():
    """Tüm veritabanı bağlantı durumlarını göster"""
    return database_manager.get_connection_status()
