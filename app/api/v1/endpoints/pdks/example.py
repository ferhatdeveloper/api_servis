"""
Örnek router - Veritabanı seçimi nasıl yapılır
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy import text

from app.core.pdks_dependencies import get_db
from app.core.pdks_config import config_manager
from app.core.pdks_core_database import database_manager

router = APIRouter(prefix="/example", tags=["Example"])


@router.get("/databases/{db_name}")
async def get_database_info(db_name: str):
    """
    Belirli bir veritabanının bilgilerini al
    """
    # Belirli veritabanına bağlan
    db: Session = next(get_db(db_name=db_name))
    
    try:
        # Veritabanı tipine göre sorgu çalıştır
        db_type = config_manager.databases[db_name].Type
        
        if db_type == "MSSQL":
            # SQL Server için tablo listesi
            result = db.execute(text("""
                SELECT TABLE_NAME 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_TYPE = 'BASE TABLE'
                ORDER BY TABLE_NAME
            """))
            
            tables = [row[0] for row in result]
            
        elif db_type == "PostgreSQL":
            # PostgreSQL için tablo listesi
            result = db.execute(text("""
                SELECT tablename 
                FROM pg_catalog.pg_tables 
                WHERE schemaname != 'pg_catalog' AND schemaname != 'information_schema'
                ORDER BY tablename
            """))
            
            tables = [row[0] for row in result]
            
        elif db_type == "MySQL":
            # MySQL için tablo listesi
            result = db.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result]
            
        else:
            tables = []
        
        return {
            "database": db_name,
            "type": db_type,
            "total_tables": len(tables),
            "tables": tables
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Veritabanı hatası: {str(e)}")
    finally:
        db.close()


@router.get("/all-connections")
async def get_all_connections():
    """Tüm aktif veritabanı bağlantılarını göster"""
    return database_manager.get_connection_status()


@router.get("/query")
async def execute_simple_query(
    db_name: Optional[str] = Query(None, description="Veritabanı adı (boş bırakılırsa varsayılan kullanılır)"),
    query: str = Query(..., description="SQL sorgusu")
):
    """
    SQL sorgusu çalıştır - Tüm veritabanı tipleri desteklenir
    
    Örnek kullanım:
    - db_name boşsa varsayılan veritabanı kullanılır (Default: MSSQLDatabase)
    - query parametresi ile SQL sorgusu çalıştırılır
    
    GET /api/example/query?query=SELECT * FROM Users
    GET /api/example/query?db_name=LOGO_Database&query=SELECT * FROM FATBAS_TXT
    """
    if not config_manager.app_config.DeveloperMode:
        return {"error": "Bu endpoint sadece developer mode'da çalışır"}
    
    # Veritabanı seç (db_name boşsa varsayılan kullanılır)
    # Oturum oluştur
    db: Session = next(get_db(db_name=db_name))
    
    try:
        result = db.execute(text(query))
        
        # Sonuçları formatla
        columns = result.keys()
        rows = []
        for row in result:
            rows.append(dict(zip(columns, row)))
        
        return {
            "status": "success",
            "database": selected_db,
            "rows_count": len(rows),
            "data": rows
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
