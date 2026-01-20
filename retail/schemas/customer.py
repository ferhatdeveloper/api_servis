"""
RetailOS - Customer Schemas
MÃ¼ÅŸteri Pydantic modelleri (API request/response)
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal


# Base Schema
class CustomerBase(BaseModel):
    """MÃ¼ÅŸteri Base Schema"""
    customer_code: str = Field(..., max_length=50, description="MÃ¼ÅŸteri kodu")
    customer_name: str = Field(..., max_length=200, description="MÃ¼ÅŸteri adÄ±")
    customer_type: str = Field(default="Bireysel", max_length=50, description="MÃ¼ÅŸteri tipi")
    phone1: Optional[str] = Field(None, max_length=50, description="Telefon 1")
    email: Optional[EmailStr] = Field(None, description="E-posta")
    city: Optional[str] = Field(None, max_length=100, description="Åehir")
    
    @validator('customer_code')
    def customer_code_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('MÃ¼ÅŸteri kodu boÅŸ olamaz')
        return v.strip().upper()


# Create Schema
class CustomerCreate(CustomerBase):
    """MÃ¼ÅŸteri OluÅŸturma Schema"""
    firma_id: int = Field(..., description="Firma ID")
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    tax_office: Optional[str] = Field(None, max_length=100)
    tax_number: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    credit_limit: Optional[Decimal] = Field(default=Decimal("0.00"), ge=0)


# Update Schema
class CustomerUpdate(BaseModel):
    """MÃ¼ÅŸteri GÃ¼ncelleme Schema"""
    customer_name: Optional[str] = Field(None, max_length=200)
    phone1: Optional[str] = Field(None, max_length=50)
    phone2: Optional[str] = Field(None, max_length=50)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    credit_limit: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None


# Response Schema
class Customer(CustomerBase):
    """MÃ¼ÅŸteri Response Schema"""
    customer_id: int
    firma_id: int
    loyalty_card_no: Optional[str]
    loyalty_points: int = 0
    credit_limit: Decimal
    current_balance: Decimal
    total_purchases: Decimal
    is_active: bool
    created_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# Detailed Response (Ä°statistiklerle)
class CustomerDetail(Customer):
    """MÃ¼ÅŸteri Detay Response"""
    tax_office: Optional[str]
    tax_number: Optional[str]
    address: Optional[str]
    district: Optional[str]
    first_purchase_date: Optional[datetime]
    last_purchase_date: Optional[datetime]
    total_purchase_count: int = 0
    average_basket_size: Decimal


# List Response
class CustomerList(BaseModel):
    """MÃ¼ÅŸteri Liste Response"""
    total: int = Field(..., description="Toplam kayÄ±t sayÄ±sÄ±")
    items: List[Customer] = Field(..., description="MÃ¼ÅŸteri listesi")
    page: int = Field(default=1, description="Sayfa numarasÄ±")
    page_size: int = Field(default=50, description="Sayfa boyutu")


# Loyalty Response
class CustomerLoyalty(BaseModel):
    """MÃ¼ÅŸteri Sadakat Bilgisi"""
    customer_id: int
    customer_name: str
    loyalty_card_no: Optional[str]
    loyalty_points: int
    loyalty_tier: Optional[str]
    total_purchases: Decimal
    
    class Config:
        from_attributes = True
