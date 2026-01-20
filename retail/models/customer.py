"""
RetailOS - Customer Model
MÃ¼ÅŸteri modeli
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, DECIMAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class Customer(Base):
    """MÃ¼ÅŸteriler"""
    __tablename__ = "customers"
    
    customer_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    firma_id = Column(Integer, ForeignKey("firmalar.firma_id", ondelete="CASCADE"), nullable=False)
    
    # MÃ¼ÅŸteri Bilgileri
    customer_code = Column(String(50), nullable=False, unique=True, index=True)
    customer_name = Column(String(200), nullable=False)
    customer_type = Column(String(50), default="Bireysel")  # Bireysel, Kurumsal
    customer_group = Column(String(100))
    
    # KiÅŸisel Bilgiler
    first_name = Column(String(100))
    last_name = Column(String(100))
    birth_date = Column(Date)
    gender = Column(String(10))  # Erkek, KadÄ±n, Belirtmek Ä°stemiyorum
    
    # Vergi Bilgileri
    tax_office = Column(String(100))
    tax_number = Column(String(20))
    tc_identity_no = Column(String(11))
    
    # Ä°letiÅŸim Bilgileri
    phone1 = Column(String(50))
    phone2 = Column(String(50))
    email = Column(String(100), index=True)
    address = Column(Text)
    city = Column(String(100))
    district = Column(String(100))
    postal_code = Column(String(10))
    country = Column(String(50), default="TÃ¼rkiye")
    
    # Sadakat ProgramÄ±
    loyalty_card_no = Column(String(50), unique=True, index=True)
    loyalty_points = Column(Integer, default=0)
    loyalty_tier = Column(String(50))  # Bronz, GÃ¼mÃ¼ÅŸ, AltÄ±n, Platin
    
    # Finansal Bilgiler
    credit_limit = Column(DECIMAL(15, 2), default=0.00)
    current_balance = Column(DECIMAL(15, 2), default=0.00)
    total_purchases = Column(DECIMAL(15, 2), default=0.00)
    total_points_earned = Column(Integer, default=0)
    
    # Ä°statistikler
    first_purchase_date = Column(DateTime)
    last_purchase_date = Column(DateTime)
    total_purchase_count = Column(Integer, default=0)
    average_basket_size = Column(DECIMAL(15, 2), default=0.00)
    
    # Pazarlama
    marketing_consent = Column(Boolean, default=False)
    sms_consent = Column(Boolean, default=False)
    email_consent = Column(Boolean, default=False)
    
    # E-DÃ¶nÃ¼ÅŸÃ¼m
    efatura_user = Column(Boolean, default=False)
    earsiv_user = Column(Boolean, default=False)
    gib_label = Column(String(100))
    
    # Ã–zel Kodlar
    special_code1 = Column(String(100))
    special_code2 = Column(String(100))
    special_code3 = Column(String(100))
    
    # Logo/Nebim Entegrasyon
    logo_customer_code = Column(String(50))
    is_logo_synced = Column(Boolean, default=False)
    logo_sync_date = Column(DateTime)
    
    # Sistem AlanlarÄ±
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    block_reason = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    notes = Column(Text)
    
    # Ä°liÅŸkiler
    sales = relationship("Sale", back_populates="customer")
    
    def __repr__(self):
        return f"<Customer {self.customer_code}: {self.customer_name}>"
    
    def to_dict(self):
        """Model'i dict'e Ã§evir"""
        return {
            "customer_id": self.customer_id,
            "customer_code": self.customer_code,
            "customer_name": self.customer_name,
            "customer_type": self.customer_type,
            "phone1": self.phone1,
            "email": self.email,
            "city": self.city,
            "loyalty_card_no": self.loyalty_card_no,
            "loyalty_points": self.loyalty_points,
            "credit_limit": float(self.credit_limit) if self.credit_limit else 0,
            "current_balance": float(self.current_balance) if self.current_balance else 0,
            "total_purchases": float(self.total_purchases) if self.total_purchases else 0,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
