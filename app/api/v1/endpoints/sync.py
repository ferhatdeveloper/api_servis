from fastapi import APIRouter, Header, HTTPException, Query
from typing import Optional, List, Dict, Any
from app.services.sync_service import sync_service
from loguru import logger

router = APIRouter()

@router.post("/{report_code}/refresh")
async def refresh_report_snapshot(
    report_code: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """Manually trigger a data snapshot refresh for a report"""
    success = await sync_service.generate_and_save_snapshot(report_code, firma=x_firma, period=x_period)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to refresh snapshot")
    return {"status": "success", "message": f"Snapshot for {report_code} updated."}

@router.get("/{report_code}/snapshot")
async def get_report_snapshot(
    report_code: str,
    x_firma: Optional[str] = Header(None),
    x_period: Optional[str] = Header(None)
):
    """Retrieve the latest cached snapshot for a report (Offline-First support)"""
    snapshot = await sync_service.get_latest_snapshot(report_code, firma=x_firma, period=x_period)
    if not snapshot:
        raise HTTPException(status_code=404, detail="No snapshot found for this report.")
    return snapshot
