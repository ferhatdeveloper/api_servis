"""
Performans ve Optimizasyon Endpoint'leri
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.pdks_database import get_db
from app.utils.pdks.database_utils import DatabaseUtils

router = APIRouter(prefix="/performance", tags=["Performance"])


@router.post("/create-index")
async def create_index(
    table: str = Query(..., description="Tablo adı"),
    column: str = Query(..., description="Sütun adı"),
    index_name: Optional[str] = Query(None, description="Index adı (opsiyonel)"),
    db: Session = Depends(get_db)
):
    """
    Performans için index oluştur
    """
    utils = DatabaseUtils()
    success = utils.create_index(db, table, column, index_name)
    
    if success:
        return {
            "status": "success",
            "message": f"Index oluşturuldu: {table}({column})",
            "table": table,
            "column": column
        }
    else:
        raise HTTPException(status_code=500, detail="Index oluşturma başarısız")


@router.post("/create-composite-index")
async def create_composite_index(
    table: str = Query(..., description="Tablo adı"),
    columns: List[str] = Query(..., description="Sütun listesi"),
    index_name: str = Query(..., description="Index adı"),
    db: Session = Depends(get_db)
):
    """
    Birden fazla sütun için composite index oluştur
    """
    utils = DatabaseUtils()
    success = utils.create_composite_index(db, table, columns, index_name)
    
    if success:
        return {
            "status": "success",
            "message": f"Composite index oluşturuldu: {table}({', '.join(columns)})",
            "table": table,
            "columns": columns,
            "index_name": index_name
        }
    else:
        raise HTTPException(status_code=500, detail="Index oluşturma başarısız")


@router.post("/add-column")
async def add_column(
    table: str = Query(..., description="Tablo adı"),
    column_name: str = Query(..., description="Sütun adı"),
    column_type: str = Query("VARCHAR(255)", description="Sütun tipi"),
    default_value: Optional[str] = Query(None, description="Varsayılan değer"),
    db: Session = Depends(get_db)
):
    """
    Tabloya yeni sütun ekle
    """
    utils = DatabaseUtils()
    success = utils.add_column(db, table, column_name, column_type, default_value)
    
    if success:
        return {
            "status": "success",
            "message": f"Sütun eklendi: {column_name} to {table}",
            "table": table,
            "column": column_name,
            "type": column_type
        }
    else:
        raise HTTPException(status_code=500, detail="Sütun ekleme başarısız")


@router.get("/table-info/{table}")
async def get_table_info(
    table: str,
    db: Session = Depends(get_db)
):
    """
    Tablo bilgilerini getir
    """
    utils = DatabaseUtils()
    info = utils.get_table_info(db, table)
    
    if "error" in info:
        raise HTTPException(status_code=404, detail=info["error"])
    
    return info


@router.post("/analyze/{table}")
async def analyze_table(
    table: str,
    db: Session = Depends(get_db)
):
    """
    Tablo istatistiklerini güncelle (ANALYZE)
    """
    utils = DatabaseUtils()
    utils.analyze_table(db, table)
    
    return {
        "status": "success",
        "message": f"Tablo analiz edildi: {table}",
        "table": table
    }


@router.post("/optimize/{table}")
async def optimize_table(
    table: str,
    db: Session = Depends(get_db)
):
    """
    Tablo optimizasyonu (VACUUM ANALYZE)
    """
    utils = DatabaseUtils()
    success = utils.optimize_table(db, table)
    
    if success:
        return {
            "status": "success",
            "message": f"Tablo optimize edildi: {table}",
            "table": table
        }
    else:
        raise HTTPException(status_code=500, detail="Optimizasyon başarısız")


@router.get("/table-size/{table}")
async def get_table_size(
    table: str,
    db: Session = Depends(get_db)
):
    """
    Tablo boyut bilgileri
    """
    utils = DatabaseUtils()
    size_info = utils.get_table_size(db, table)
    
    if "error" in size_info:
        raise HTTPException(status_code=404, detail=size_info["error"])
    
    return size_info


@router.post("/explain-query")
async def explain_query(
    query: str = Query(..., description="SQL sorgusu"),
    db: Session = Depends(get_db)
):
    """
    Query plan analizi (EXPLAIN ANALYZE)
    """
    utils = DatabaseUtils()
    plan = utils.explain_query(db, query)
    
    if "error" in plan:
        raise HTTPException(status_code=400, detail=plan["error"])
    
    return plan
