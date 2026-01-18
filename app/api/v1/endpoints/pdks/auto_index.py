"""
Otomatik Indexleme API
Sık sorgulanan verileri tespit edip index oluşturur
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.core.pdks_database import engine, get_db
from app.utils.pdks.auto_indexer import AutoIndexer

router = APIRouter(prefix="/auto-index", tags=["Auto Indexing"])

@router.get("/analyze/{table_name}")
async def analyze_table(
    table_name: str,
    db: Session = Depends(get_db)
):
    """
    Tablo performansını analiz et ve index önerileri al
    """
    try:
        indexer = AutoIndexer(engine)
        
        # Performans analizi
        perf_data = indexer.analyze_table_performance(table_name)
        
        # Index önerileri
        suggestions = indexer.suggest_indexes(table_name)
        
        return {
            "table": table_name,
            "performance": perf_data,
            "suggested_indexes": suggestions,
            "total_suggestions": len(suggestions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create/{table_name}")
async def create_auto_indexes(
    table_name: str,
    min_distinct: float = Query(10, description="Minimum distinct değer sayısı"),
    auto_create: bool = Query(False, description="Otomatik oluştur")
):
    """
    Önerilen index'leri oluştur
    """
    try:
        indexer = AutoIndexer(engine)
        
        if auto_create:
            # Tüm önerilen index'leri oluştur
            result = indexer.create_suggested_indexes(table_name)
            return {
                "status": "success",
                "table": table_name,
                "created": result['total_created'],
                "failed": result['total_failed'],
                "details": result['created']
            }
        else:
            # Sadece önerileri göster
            suggestions = indexer.suggest_indexes(table_name, min_distinct)
            return {
                "status": "suggestions_only",
                "table": table_name,
                "suggestions": suggestions,
                "total": len(suggestions)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyze-all")
async def analyze_all_tables():
    """
    Tüm tabloları analiz et ve genel index önerileri al
    """
    try:
        indexer = AutoIndexer(engine)
        
        inspector = indexer.inspector
        tables = inspector.get_table_names()
        
        analysis = []
        
        for table in tables:
            try:
                # Her tablo için index önerileri
                suggestions = indexer.suggest_indexes(table)
                
                if suggestions:
                    analysis.append({
                        'table': table,
                        'suggestions': suggestions,
                        'count': len(suggestions)
                    })
            except Exception as e:
                analysis.append({
                    'table': table,
                    'error': str(e)
                })
        
        total_suggestions = sum(a.get('count', 0) for a in analysis)
        
        return {
            "status": "success",
            "total_tables": len(tables),
            "tables_with_suggestions": len([a for a in analysis if a.get('count', 0) > 0]),
            "total_suggestions": total_suggestions,
            "details": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-all")
async def create_all_suggested_indexes():
    """
    Tüm tablolarda önerilen index'leri oluştur
    """
    try:
        indexer = AutoIndexer(engine)
        
        result = indexer.create_suggested_indexes()
        
        return {
            "status": "success",
            "created": result['total_created'],
            "failed": result['total_failed'],
            "details": {
                "created_indexes": result['created'],
                "failed_indexes": result['failed']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/slow-queries")
async def get_slow_queries():
    """
    Yavaş çalışan sorguları listele ve index önerileri al
    """
    try:
        indexer = AutoIndexer(engine)
        
        slow_queries = indexer.get_missing_indexes_from_queries()
        
        return {
            "status": "success",
            "slow_queries_found": len(slow_queries),
            "queries": slow_queries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check_auto_index():
    """Otomatik indexleme sistem durumu"""
    try:
        # Extension kontrolü
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "message": "Auto indexing system is ready"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
