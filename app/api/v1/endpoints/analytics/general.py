from fastapi import APIRouter, Depends, HTTPException
from typing import List, Any
from app.core.database import db_manager
from app.core.config import settings

router = APIRouter()

@router.get("/companies", summary="Get list of companies")
def get_companies(source: str = "auto"):
    """
    Returns a list of companies/firms.
    
    Args:
        source: 'auto', 'mssql' (Logo), or 'postgres' (Ops)
    """
    try:
        data = []
        
        # 1. Force MSSQL / Logo
        if source == "mssql":
            query = "SELECT NR as code, NAME as name FROM L_CAPIFIRM ORDER BY NR"
            data = db_manager.execute_ms_query(query)
            
        # 2. Force Postgres / Ops
        elif source == "postgres":
            query = "SELECT * FROM companies"
            data = db_manager.execute_pg_query(query)
            
        # 3. Auto / API Mode 
        else:
            # Try Logo First
            try:
                query = "SELECT NR as code, NAME as name FROM L_CAPIFIRM ORDER BY NR"
                data = db_manager.execute_ms_query(query)
            except Exception as e:
                # Log failure but try fallback
                print(f"Auto-Source MSSQL Attempt Failed: {e}")
                pass
            
            # Fallback to Postgres if empty or failed
            if not data:
                try:
                    query = "SELECT * FROM companies"
                    data = db_manager.execute_pg_query(query)
                except Exception as e:
                    print(f"Auto-Source PG Attempt Failed: {e}")
        
        if not data:
             # Return valid empty list, but maybe we want to know why?
             pass
             
        return data
        
    except Exception as e:
        # Meaningful error for forced modes
        if source != "auto" and source != "api":
            raise HTTPException(status_code=400, detail=f"{source} kaynağından veri çekilemedi: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", summary="Get dashboard statistics")
def get_dashboard_stats(company_id: str = None, period: str = None):
    """
    Returns basic statistics for the dashboard.
    """
    # Placeholder implementation - replace with actual queries
    return {
        "total_firms": 42, # Mock
        "active_period": period or "2024",
        "active_users": 5
    }

@router.get("/chart", summary="Get chart data")
def get_chart_data(company_id: str = None):
    """
    Returns data formatted for charts.
    """
    return [
        {"Ay": "Ocak", "Ciro": 100, "Personel": 50},
        {"Ay": "Şubat", "Ciro": 120, "Personel": 52},
        {"Ay": "Mart", "Ciro": 110, "Personel": 51},
        {"Ay": "Nisan", "Ciro": 140, "Personel": 55},
        {"Ay": "Mayıs", "Ciro": 150, "Personel": 55},
    ]
