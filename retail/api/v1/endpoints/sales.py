"""RetailOS - Sales Endpoints"""
from fastapi import APIRouter, Depends
from retail.core.security import get_current_active_user

router = APIRouter()

@router.get("/")
async def get_sales(current_user = Depends(get_current_active_user)):
    return {"message": "Sales endpoint"}

@router.post("/")
async def create_sale(current_user = Depends(get_current_active_user)):
    return {"message": "Create sale"}
