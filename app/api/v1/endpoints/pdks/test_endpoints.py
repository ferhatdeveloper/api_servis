"""
Test endpoint'leri - Varsayılan veritabanı kullanımı örnekleri
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy import text

from app.core.pdks_dependencies import get_db
from app.core.pdks_config import config_manager

router = APIRouter(prefix="/test", tags=["Test"])


@router.get("/default-db")
async def test_default_db(db: Session = Depends(get_db)):
    """
    Varsayılan veritabanı kullanımı örneği
    db_name belirtilmezse varsayılan veritabanı kullanılır
    """
    try:
        # Varsayılan veritabanı üzerinde sorgu çalıştır
        result = db.execute(text("SELECT DB_NAME() as current_database"))
        db_name = result.scalar()
        
        return {
            "message": "Varsayılan veritabanı başarıyla kullanıldı",
            "current_database": db_name,
            "default_database_config": config_manager.app_config.Default
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/custom-db")
async def test_custom_db(
    db_name: str = Query(..., description="Veritabanı adı"),
    db: Session = Depends(get_db)
):
    """
    Özel veritabanı kullanımı örneği (ÇALIŞMAZ - dependency injection ile bu şekilde kullanamayız)
    Bunun yerine direkt get_db(db_name=...) kullanın
    """
    return {
        "message": "Bu endpoint örnek amacıyla gösterilmiştir",
        "note": "Gerçek kullanım için endpoint içinde get_db(db_name=...) kullanın"
    }


@router.get("/with-specific-db/{db_name}")
async def test_with_specific_db(db_name: str):
    """
    Belirli bir veritabanı kullanımı örneği
    Path parametresi ile veritabanı belirtilir
    """
    # Belirli veritabanını kullan
    db: Session = next(get_db(db_name=db_name))
    
    try:
        result = db.execute(text("SELECT DB_NAME() as current_database"))
        current_db = result.scalar()
        
        return {
            "requested_database": db_name,
            "current_database": current_db,
            "success": True
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@router.get("/compare-databases")
async def compare_databases():
    """
    Birden fazla veritabanını karşılaştırma örneği
    """
    results = {}
    
    for db_name in ["MSSQLDatabase", "LOGO_Database"]:
        try:
            db: Session = next(get_db(db_name=db_name))
            result = db.execute(text("SELECT DB_NAME() as db"))
            results[db_name] = {
                "status": "success",
                "database": result.scalar()
            }
            db.close()
        except Exception as e:
            results[db_name] = {
                "status": "error",
                "message": str(e)
            }
    
    return results
