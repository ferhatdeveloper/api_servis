"""RetailOS - Reports Endpoints"""
from fastapi import APIRouter, Depends
from retail.core.security import get_current_active_user

router = APIRouter()

@router.get("/daily-sales")
async def get_daily_sales(current_user = Depends(get_current_active_user)):
    return {"message": "Daily sales report"}
