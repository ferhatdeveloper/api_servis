"""
RetailOS - Sales Endpoints
Perakende Satış Modülü API
"""
from fastapi import APIRouter, Depends
from app.core.security_jwt import get_current_active_user

router = APIRouter()

@router.get("/")
async def get_sales(current_user = Depends(get_current_active_user)):
    """
    **Satış Listesi**

    Kullanıcıya ait veya yetkisi dahilindeki satış işlemlerini listeler.
    """
    return {"message": "Sales endpoint"}

@router.post("/")
async def create_sale(current_user = Depends(get_current_active_user)):
    """
    **Yeni Satış**

    Perakende satış işlemi başlatır.
    """
    return {"message": "Create sale"}
