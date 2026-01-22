from fastapi import APIRouter
from app.core.database import db_manager
from app.services.logo_service import logo_service

router = APIRouter()

@router.get("/products")
async def get_products():
    # Can merge local DB products with real-time Logo stock
    query = "SELECT * FROM products WHERE is_active = TRUE"
    products = db_manager.execute_pg_query(query)
    return products

@router.get("/stock/{item_code}")
async def get_logo_stock(item_code: str):
    return await logo_service.get_logo_stock_status(item_code)
