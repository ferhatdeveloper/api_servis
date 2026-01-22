from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.core.database import db_manager
from datetime import datetime

router = APIRouter()

class CustomReportBase(BaseModel):
    name: str
    description: Optional[str] = None
    sql_query: str
    view_name: Optional[str] = None

class CustomReport(CustomReportBase):
    id: int
    created_at: datetime

@router.get("/", response_model=List[CustomReport])
async def list_custom_reports():
    """List all saved custom reports"""
    query = "SELECT id, name, description, sql_query, view_name, created_at FROM custom_reports ORDER BY created_at DESC"
    results = db_manager.execute_pg_query(query)
    # Convert to Pydantic models
    return [CustomReport(**row) for row in results]

@router.post("/", response_model=CustomReport)
async def create_custom_report(report: CustomReportBase):
    """Save a new custom report (SQL)"""
    query = """
        INSERT INTO custom_reports (name, description, sql_query, view_name)
        VALUES (%s, %s, %s, %s)
        RETURNING id, name, description, sql_query, view_name, created_at
    """
    params = (report.name, report.description, report.sql_query, report.view_name)
    result = db_manager.execute_pg_query(query, params)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create report")
    return CustomReport(**result[0])

@router.delete("/{id}")
async def delete_custom_report(id: int):
    """Delete a custom report"""
    query = "DELETE FROM custom_reports WHERE id = %s RETURNING id"
    result = db_manager.execute_pg_query(query, (id,))
    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"status": "success", "message": "Report deleted"}

@router.post("/{id}/execute")
async def execute_custom_report(id: int):
    """Execute the SQL query of a custom report"""
    # 1. Get Query
    report_res = db_manager.execute_pg_query("SELECT sql_query FROM custom_reports WHERE id = %s", (id,))
    if not report_res:
        raise HTTPException(status_code=404, detail="Report not found")
    
    sql = report_res[0]['sql_query']
    
    # 2. Execute on Logo MSSQL (Assumed target, could be PG based on context)
    # Usually these are Logo Reports -> MSSQL
    # But if it's a "View", it might be PG?
    # Context: "logoda bir rapor çektiğimde... sql kodlarını verebilir misin... sistemde listeleyebilmem lazım"
    # User implies Logo Reports. So execute on MSSQL.
    
    try:
        data = db_manager.execute_ms_query(sql)
        # Limit rows for safety?
        return {"data": data[:1000] if data else [], "count": len(data) if data else 0, "truncated": len(data) > 1000 if data else False}
    except Exception as e:
         raise HTTPException(status_code=400, detail=f"Execution Error: {str(e)}")
