"""
RetailOS - Sale Model
SatÄ±ÅŸ ve SatÄ±ÅŸ Detay modelleri
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, DECIMAL, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class Sale(Base):
    """SatÄ±ÅŸlar (Ana Tablo)"""
    __tablename__ = "sales"
    
    sale_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    firma_id = Column(Integer, ForeignKey("firmalar.firma_id", ondelete="CASCADE"), nullable=False)
    store_id = Column(Integer, ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False)
    
    # Fatura Bilgileri
    invoice_no = Column(String(100), unique=True, nullable=False, index=True)
    invoice_date = Column(DateTime, nullable=False, server_default=func.now())
    invoice_type = Column(String(50), default="Perakende")  # Perakende, Toptan, E-ticaret
    
    # MÃ¼ÅŸteri
    customer_id = Column(Integer, ForeignKey("customers.customer_id", ondelete="SET NULL"))
    customer_name = Column(String(200))
    
    # Personel
    cashier_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    salesperson_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    
    # Tutar Bilgileri
    subtotal = Column(DECIMAL(15, 2), nullable=False, default=0.00)  # Ara Toplam
    discount_amount = Column(DECIMAL(15, 2), default=0.00)  # Ä°ndirim
    discount_rate = Column(DECIMAL(5, 2), default=0.00)  # Ä°ndirim OranÄ±
    tax_amount = Column(DECIMAL(15, 2), default=0.00)  # TAX ToplamÄ±
    total_amount = Column(DECIMAL(15, 2), nullable=False, default=0.00)  # Genel Toplam
    
    # Ã–deme
    payment_method = Column(String(50), default="Nakit")  # Nakit, Kredi KartÄ±, AÃ§Ä±k Hesap
    payment_status = Column(String(50), default="Ã–dendi")  # Ã–dendi, Bekliyor, KÄ±smi
    paid_amount = Column(DECIMAL(15, 2), default=0.00)
    remaining_amount = Column(DECIMAL(15, 2), default=0.00)
    
    # Kampanya
    campaign_id = Column(Integer, ForeignKey("campaigns.campaign_id", ondelete="SET NULL"))
    campaign_discount = Column(DECIMAL(15, 2), default=0.00)
    
    # Sadakat
    points_earned = Column(Integer, default=0)
    points_used = Column(Integer, default=0)
    
    # Durum
    status = Column(String(50), default="TamamlandÄ±")  # TamamlandÄ±, Ä°ptal, Ä°ade, Beklemede
    is_canceled = Column(Boolean, default=False)
    cancel_reason = Column(Text)
    cancel_date = Column(DateTime)
    
    # Logo/Nebim Entegrasyon
    logo_trcode = Column(Integer)  # 0-31 arasÄ± fatura tipi
    logo_fiche_no = Column(String(50))
    is_logo_synced = Column(Boolean, default=False)
    logo_sync_date = Column(DateTime)
    
    # Sistem
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    notes = Column(Text)
    
    # Ä°liÅŸkiler
    customer = relationship("Customer", back_populates="sales")
    sale_items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Sale {self.invoice_no}: {self.total_amount}>"
    
    def to_dict(self):
        """Model'i dict'e Ã§evir"""
        return {
            "sale_id": self.sale_id,
            "invoice_no": self.invoice_no,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "customer_name": self.customer_name,
            "subtotal": float(self.subtotal) if self.subtotal else 0,
            "discount_amount": float(self.discount_amount) if self.discount_amount else 0,
            "tax_amount": float(self.tax_amount) if self.tax_amount else 0,
            "total_amount": float(self.total_amount) if self.total_amount else 0,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SaleItem(Base):
    """SatÄ±ÅŸ DetaylarÄ± (Kalemler)"""
    __tablename__ = "sale_items"
    
    item_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sale_id = Column(Integer, ForeignKey("sales.sale_id", ondelete="CASCADE"), nullable=False)
    
    # ÃœrÃ¼n Bilgileri
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    variant_id = Column(Integer, ForeignKey("product_variants.variant_id", ondelete="SET NULL"))
    product_code = Column(String(100), nullable=False)
    product_name = Column(String(200), nullable=False)
    
    # Varyant Bilgileri
    variant_name = Column(String(200))
    size = Column(String(50))
    color = Column(String(50))
    
    # Miktar ve Birim
    quantity = Column(DECIMAL(15, 3), nullable=False)
    unit = Column(String(20), default="ADET")
    unit_multiplier = Column(DECIMAL(15, 4), default=1.0000)
    
    # Fiyat
    unit_price = Column(DECIMAL(15, 2), nullable=False)
    list_price = Column(DECIMAL(15, 2))  # Liste fiyatÄ±
    discount_rate = Column(DECIMAL(5, 2), default=0.00)
    discount_amount = Column(DECIMAL(15, 2), default=0.00)
    net_price = Column(DECIMAL(15, 2), nullable=False)  # Ä°ndirimli fiyat
    
    # TAX
    tax_rate = Column(DECIMAL(5, 2), default=20.00)
    tax_amount = Column(DECIMAL(15, 2), default=0.00)
    
    # Toplam
    line_total = Column(DECIMAL(15, 2), nullable=False)  # (Miktar Ã— Net Fiyat) + TAX
    
    # Maliyet (FIFO'dan gelecek)
    cost_price = Column(DECIMAL(15, 2))
    total_cost = Column(DECIMAL(15, 2))
    profit_margin = Column(DECIMAL(15, 2))
    
    # Kampanya
    campaign_id = Column(Integer)
    campaign_discount = Column(DECIMAL(15, 2), default=0.00)
    
    # SÄ±ra
    line_number = Column(Integer, default=1)
    
    # Ä°liÅŸkiler
    sale = relationship("Sale", back_populates="sale_items")
    product = relationship("Product")
    
    def __repr__(self):
        return f"<SaleItem {self.product_code}: {self.quantity} Ã— {self.unit_price}>"
    
    def to_dict(self):
        """Model'i dict'e Ã§evir"""
        return {
            "item_id": self.item_id,
            "product_code": self.product_code,
            "product_name": self.product_name,
            "variant_name": self.variant_name,
            "quantity": float(self.quantity) if self.quantity else 0,
            "unit": self.unit,
            "unit_price": float(self.unit_price) if self.unit_price else 0,
            "discount_amount": float(self.discount_amount) if self.discount_amount else 0,
            "net_price": float(self.net_price) if self.net_price else 0,
            "tax_rate": float(self.tax_rate) if self.tax_rate else 0,
            "tax_amount": float(self.tax_amount) if self.tax_amount else 0,
            "line_total": float(self.line_total) if self.line_total else 0,
        }
