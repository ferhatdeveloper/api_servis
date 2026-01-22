"""
RetailOS - Customers Endpoints
MÃ¼ÅŸteri CRUD iÅŸlemleri
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.async_database import get_db
from app.core.security_jwt import get_current_active_user
from app.models.retail import Customer
from app.models.user import User
from app.schemas.retail.customer import (
    Customer as CustomerSchema,
    CustomerCreate,
    CustomerUpdate,
    CustomerList,
    CustomerDetail,
    CustomerLoyalty
)

router = APIRouter()


@router.get("/", response_model=CustomerList)
async def get_customers(
    skip: int = Query(0, ge=0, description="Atlanacak kayÄ±t sayÄ±sÄ±"),
    limit: int = Query(50, ge=1, le=100, description="Getirilecek kayÄ±t sayÄ±sÄ±"),
    search: Optional[str] = Query(None, description="Arama metni (kod, ad, telefon)"),
    customer_type: Optional[str] = Query(None, description="MÃ¼ÅŸteri tipi filtresi"),
    is_active: Optional[bool] = Query(None, description="Aktif durum filtresi"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """MÃ¼ÅŸteri listesi getir"""
    query = db.query(Customer).filter(Customer.firma_id == current_user.firma_id)
    
    # Filtreler
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Customer.customer_code.ilike(search_filter)) |
            (Customer.customer_name.ilike(search_filter)) |
            (Customer.phone1.ilike(search_filter)) |
            (Customer.email.ilike(search_filter))
        )
    
    if customer_type:
        query = query.filter(Customer.customer_type == customer_type)
    
    if is_active is not None:
        query = query.filter(Customer.is_active == is_active)
    
    # Toplam sayÄ±
    total = query.count()
    
    # Sayfalama
    customers = query.order_by(Customer.customer_name).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "items": customers,
        "page": (skip // limit) + 1 if limit > 0 else 1,
        "page_size": limit
    }


@router.get("/{customer_id}", response_model=CustomerDetail)
async def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """MÃ¼ÅŸteri detay getir"""
    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id,
        Customer.firma_id == current_user.firma_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MÃ¼ÅŸteri bulunamadÄ±"
        )
    
    return customer


@router.get("/code/{customer_code}", response_model=CustomerSchema)
async def get_customer_by_code(
    customer_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """MÃ¼ÅŸteri kodu ile getir"""
    customer = db.query(Customer).filter(
        Customer.customer_code == customer_code.upper(),
        Customer.firma_id == current_user.firma_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"MÃ¼ÅŸteri bulunamadÄ±: {customer_code}"
        )
    
    return customer


@router.get("/loyalty/{card_no}", response_model=CustomerLoyalty)
async def get_customer_by_loyalty_card(
    card_no: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sadakat kartÄ± ile mÃ¼ÅŸteri bilgisi getir"""
    customer = db.query(Customer).filter(
        Customer.loyalty_card_no == card_no,
        Customer.firma_id == current_user.firma_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sadakat kartÄ± bulunamadÄ±: {card_no}"
        )
    
    return customer


@router.post("/", response_model=CustomerSchema, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Yeni mÃ¼ÅŸteri oluÅŸtur"""
    
    # MÃ¼ÅŸteri kodu kontrolÃ¼
    existing = db.query(Customer).filter(
        Customer.customer_code == customer_data.customer_code.upper(),
        Customer.firma_id == current_user.firma_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Bu mÃ¼ÅŸteri kodu zaten kullanÄ±lÄ±yor: {customer_data.customer_code}"
        )
    
    # Email kontrolÃ¼
    if customer_data.email:
        existing_email = db.query(Customer).filter(
            Customer.email == customer_data.email,
            Customer.firma_id == current_user.firma_id
        ).first()
        
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Bu e-posta adresi zaten kullanÄ±lÄ±yor: {customer_data.email}"
            )
    
    # Yeni mÃ¼ÅŸteri oluÅŸtur
    customer = Customer(
        **customer_data.dict(),
        created_by=current_user.id
    )
    
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return customer


@router.put("/{customer_id}", response_model=CustomerSchema)
async def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """MÃ¼ÅŸteri gÃ¼ncelle"""
    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id,
        Customer.firma_id == current_user.firma_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MÃ¼ÅŸteri bulunamadÄ±"
        )
    
    # GÃ¼ncellemeleri uygula
    update_data = customer_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)
    
    db.commit()
    db.refresh(customer)
    
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """MÃ¼ÅŸteri sil"""
    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id,
        Customer.firma_id == current_user.firma_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MÃ¼ÅŸteri bulunamadÄ±"
        )
    
    db.delete(customer)
    db.commit()
    
    return None


@router.post("/{customer_id}/block")
async def block_customer(
    customer_id: int,
    reason: str = Query(..., min_length=10, description="Bloke nedeni"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """MÃ¼ÅŸteriyi bloke et"""
    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id,
        Customer.firma_id == current_user.firma_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MÃ¼ÅŸteri bulunamadÄ±"
        )
    
    customer.is_blocked = True
    customer.block_reason = reason
    
    db.commit()
    
    return {"message": "MÃ¼ÅŸteri baÅŸarÄ±yla bloke edildi"}


@router.post("/{customer_id}/unblock")
async def unblock_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """MÃ¼ÅŸteri blokeyi kaldÄ±r"""
    customer = db.query(Customer).filter(
        Customer.customer_id == customer_id,
        Customer.firma_id == current_user.firma_id
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MÃ¼ÅŸteri bulunamadÄ±"
        )
    
    customer.is_blocked = False
    customer.block_reason = None
    
    db.commit()
    
    return {"message": "MÃ¼ÅŸteri blokesi kaldÄ±rÄ±ldÄ±"}
