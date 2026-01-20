"""
RetailOS API v1 Router
"""

from fastapi import APIRouter
from .endpoints import auth, products, sales, customers, reports, payment, accounting, ecommerce, websocket, duplicate_check

api_router = APIRouter()

# Alt routerlarÄ± ekle
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(sales.router, prefix="/sales", tags=["Sales"])
api_router.include_router(customers.router, prefix="/customers", tags=["Customers"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(payment.router, prefix="/payment", tags=["Payment Integration"])
api_router.include_router(accounting.router, prefix="/accounting", tags=["Accounting Integration"])
api_router.include_router(ecommerce.router, prefix="/integration", tags=["E-Commerce & Marketplace & Cargo"])
api_router.include_router(websocket.router, prefix="/ws", tags=["WebSocket Realtime Sync"])
api_router.include_router(duplicate_check.router, prefix="/duplicate-check", tags=["Duplicate Check"])
