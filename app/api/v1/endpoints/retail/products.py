"""
RetailOS - Products Endpoints
Ürün Listeleme ve Detay API
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.async_database import get_db
from app.core.security_jwt import get_current_active_user
from app.models.retail.product import Product
from app.models.user import User

router = APIRouter()

@router.get("/")
async def get_products(
    skip: int = Query(0, description="Atlanacak kayıt"),
    limit: int = Query(100, description="Listelenecek kayıt sayısı"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    **Ürün Listesi**

    Sistemdeki aktif ürünleri listeler.
    Sayfalama desteği (skip/limit) mevcuttur.
    """
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
    """
    **Ürün Detayı**

    ID ile belirli bir ürünün detaylarını getirir.
    """
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
    """
    **Barkod ile Ürün Ara**

    Barkod okuyucu veya manuel giriş ile ürün sorgular.
    """
    result = await db.execute(
        select(Product).where(Product.barcode == barcode)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return product
