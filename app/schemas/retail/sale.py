"""
RetailOS - Sale Schemas
SatÄ±ÅŸ Pydantic modelleri (API request/response)
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# Sale Item Schemas
class SaleItemBase(BaseModel):
    """SatÄ±ÅŸ Kalemi Base Schema"""
    product_id: int = Field(..., description="ÃœrÃ¼n ID")
    variant_id: Optional[int] = Field(None, description="Varyant ID")
    quantity: Decimal = Field(..., gt=0, description="Miktar")
    unit_price: Decimal = Field(..., ge=0, description="Birim fiyat")
    discount_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100, description="Ä°ndirim oranÄ±")
    tax_rate: Decimal = Field(default=Decimal("20.00"), ge=0, description="TAX oranÄ±")


class SaleItemCreate(SaleItemBase):
    """SatÄ±ÅŸ Kalemi OluÅŸturma"""
    pass


class SaleItem(SaleItemBase):
    """SatÄ±ÅŸ Kalemi Response"""
    item_id: int
    sale_id: int
    product_code: str
    product_name: str
    variant_name: Optional[str]
    unit: str
    discount_amount: Decimal
    net_price: Decimal
    tax_amount: Decimal
    line_total: Decimal
    
    class Config:
        from_attributes = True


# Sale Schemas
class SaleBase(BaseModel):
    """SatÄ±ÅŸ Base Schema"""
    store_id: int = Field(..., description="MaÄŸaza ID")
    customer_id: Optional[int] = Field(None, description="MÃ¼ÅŸteri ID")
    payment_method: str = Field(default="Nakit", max_length=50, description="Ã–deme yÃ¶ntemi")
    
    @validator('payment_method')
    def payment_method_valid(cls, v):
        valid_methods = ["Nakit", "Kredi KartÄ±", "Banka KartÄ±", "AÃ§Ä±k Hesap", "Havale/EFT"]
        if v not in valid_methods:
            raise ValueError(f'GeÃ§ersiz Ã¶deme yÃ¶ntemi. GeÃ§erli deÄŸerler: {", ".join(valid_methods)}')
        return v


class SaleCreate(SaleBase):
    """SatÄ±ÅŸ OluÅŸturma Schema"""
    firma_id: int = Field(..., description="Firma ID")
    items: List[SaleItemCreate] = Field(..., min_items=1, description="SatÄ±ÅŸ kalemleri")
    discount_amount: Optional[Decimal] = Field(default=Decimal("0.00"), ge=0)
    notes: Optional[str] = None


class SaleUpdate(BaseModel):
    """SatÄ±ÅŸ GÃ¼ncelleme Schema"""
    customer_id: Optional[int] = None
    payment_status: Optional[str] = None
    notes: Optional[str] = None


class Sale(SaleBase):
    """SatÄ±ÅŸ Response Schema"""
    sale_id: int
    firma_id: int
    invoice_no: str
    invoice_date: datetime
    invoice_type: str
    customer_name: Optional[str]
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    payment_status: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class SaleDetail(Sale):
    """SatÄ±ÅŸ Detay Response (Kalemlerle)"""
    items: List[SaleItem] = Field(default_factory=list)
    cashier_id: Optional[int]
    salesperson_id: Optional[int]
    points_earned: int = 0
    notes: Optional[str]


class SaleList(BaseModel):
    """SatÄ±ÅŸ Liste Response"""
    total: int = Field(..., description="Toplam kayÄ±t sayÄ±sÄ±")
    items: List[Sale] = Field(..., description="SatÄ±ÅŸ listesi")
    page: int = Field(default=1, description="Sayfa numarasÄ±")
    page_size: int = Field(default=50, description="Sayfa boyutu")
    total_amount: Optional[Decimal] = Field(None, description="Toplam tutar")


# Payment Schemas
class PaymentCreate(BaseModel):
    """Ã–deme OluÅŸturma"""
    sale_id: int = Field(..., description="SatÄ±ÅŸ ID")
    payment_method: str = Field(..., max_length=50)
    amount: Decimal = Field(..., gt=0)
    reference_no: Optional[str] = Field(None, max_length=100)


# Cancel Schema
class SaleCancel(BaseModel):
    """SatÄ±ÅŸ Ä°ptal"""
    cancel_reason: str = Field(..., min_length=10, max_length=500, description="Ä°ptal nedeni")
    
    @validator('cancel_reason')
    def cancel_reason_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Ä°ptal nedeni boÅŸ olamaz')
        return v.strip()


# Statistics
class SaleStatistics(BaseModel):
    """SatÄ±ÅŸ Ä°statistikleri"""
    total_sales: int = Field(..., description="Toplam satÄ±ÅŸ adedi")
    total_amount: Decimal = Field(..., description="Toplam tutar")
    average_basket: Decimal = Field(..., description="Ortalama sepet")
    total_customers: int = Field(..., description="Toplam mÃ¼ÅŸteri")
    period_start: datetime
    period_end: datetime
