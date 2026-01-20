"""
RetailOS - Product Schemas
ÃœrÃ¼n Pydantic modelleri (API request/response)
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# Base Schema
class ProductBase(BaseModel):
    """ÃœrÃ¼n Base Schema"""
    product_code: str = Field(..., max_length=100, description="ÃœrÃ¼n kodu")
    product_name: str = Field(..., max_length=200, description="ÃœrÃ¼n adÄ±")
    category_id: Optional[int] = Field(None, description="Kategori ID")
    barcode: Optional[str] = Field(None, max_length=100, description="Barkod")
    unit: str = Field(default="ADET", max_length=20, description="Birim")
    tax_rate: Decimal = Field(default=Decimal("20.00"), description="TAX oranÄ±")
    list_price: Decimal = Field(default=Decimal("0.00"), ge=0, description="Liste fiyatÄ±")
    sale_price: Decimal = Field(default=Decimal("0.00"), ge=0, description="SatÄ±ÅŸ fiyatÄ±")
    is_active: bool = Field(default=True, description="Aktif mi?")
    
    @validator('product_code')
    def product_code_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('ÃœrÃ¼n kodu boÅŸ olamaz')
        return v.strip().upper()
    
    @validator('barcode')
    def barcode_format(cls, v):
        if v:
            v = v.strip()
            if len(v) not in [8, 13]:  # EAN-8 veya EAN-13
                raise ValueError('Barkod 8 veya 13 haneli olmalÄ±')
        return v


# Create Schema
class ProductCreate(ProductBase):
    """ÃœrÃ¼n OluÅŸturma Schema"""
    firma_id: int = Field(..., description="Firma ID")


# Update Schema
class ProductUpdate(BaseModel):
    """ÃœrÃ¼n GÃ¼ncelleme Schema"""
    product_name: Optional[str] = Field(None, max_length=200)
    category_id: Optional[int] = None
    barcode: Optional[str] = Field(None, max_length=100)
    unit: Optional[str] = Field(None, max_length=20)
    tax_rate: Optional[Decimal] = None
    list_price: Optional[Decimal] = Field(None, ge=0)
    sale_price: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


# Response Schema
class Product(ProductBase):
    """ÃœrÃ¼n Response Schema"""
    id: int
    firma_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True  # Pydantic v2


# List Response
class ProductList(BaseModel):
    """ÃœrÃ¼n Liste Response"""
    total: int = Field(..., description="Toplam kayÄ±t sayÄ±sÄ±")
    items: List[Product] = Field(..., description="ÃœrÃ¼n listesi")
    page: int = Field(default=1, description="Sayfa numarasÄ±")
    page_size: int = Field(default=50, description="Sayfa boyutu")


# Barcode Search Response
class ProductBarcode(BaseModel):
    """Barkod Arama Response"""
    id: int
    product_code: str
    product_name: str
    barcode: str
    sale_price: Decimal
    stock_quantity: Optional[Decimal] = Field(default=None)
    tax_rate: Decimal
    
    class Config:
        from_attributes = True
