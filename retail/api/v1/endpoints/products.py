"""
RetailOS - Products Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from retail.core.database import get_db
from retail.core.security import get_current_active_user
from retail.models.product import Product
from retail.models.user import User

router = APIRouter()

@router.get("/")
async def get_products(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """ÃœrÃ¼n listesi"""
    result = await db.execute(
        select(Product)
        .where(Product.is_active == True)
        .offset(skip)
        .limit(limit)
    )
    products = result.scalars().all()
    return products

@router.get("/{product_id}")
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """ÃœrÃ¼n detayÄ±"""
    result = await db.execute(
        select(Product).where(Product.id == product_id)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product

@router.get("/barcode/{barcode}")
async def get_product_by_barcode(
    barcode: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Barkod ile Ã¼rÃ¼n ara"""
    result = await db.execute(
        select(Product).where(Product.barcode == barcode)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product
