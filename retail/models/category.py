"""
RetailOS - Category Model
Kategori (ÃœrÃ¼n Kategorileri) modeli
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from ..core.database import Base


class Category(Base):
    """ÃœrÃ¼n Kategorileri"""
    __tablename__ = "categories"
    
    category_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    firma_id = Column(Integer, ForeignKey("firmalar.firma_id", ondelete="CASCADE"), nullable=False)
    
    # Kategori Bilgileri
    category_code = Column(String(50), nullable=False, index=True)
    category_name = Column(String(200), nullable=False)
    category_name_en = Column(String(200))
    category_name_ar = Column(String(200))
    
    # HiyerarÅŸi
    parent_category_id = Column(Integer, ForeignKey("categories.category_id", ondelete="SET NULL"))
    category_level = Column(Integer, default=1)
    category_path = Column(String(500))  # /1/5/23/ gibi
    
    # GÃ¶rsel
    image_url = Column(String(500))
    icon_name = Column(String(100))
    color_code = Column(String(20))
    
    # SÄ±ralama ve GÃ¶rÃ¼nÃ¼m
    display_order = Column(Integer, default=0)
    show_in_menu = Column(Boolean, default=True)
    show_in_pos = Column(Boolean, default=True)
    
    # E-ticaret
    seo_url = Column(String(200))
    meta_title = Column(String(200))
    meta_description = Column(Text)
    meta_keywords = Column(String(500))
    
    # Logo/Nebim Entegrasyon
    logo_category_code = Column(String(50))
    is_logo_synced = Column(Boolean, default=False)
    logo_sync_date = Column(DateTime)
    
    # Sistem AlanlarÄ±
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    notes = Column(Text)
    
    # Ä°liÅŸkiler
    parent = relationship("Category", remote_side=[category_id], backref="children")
    products = relationship("Product", back_populates="category")
    
    def __repr__(self):
        return f"<Category {self.category_code}: {self.category_name}>"
    
    def to_dict(self):
        """Model'i dict'e Ã§evir"""
        return {
            "category_id": self.category_id,
            "firma_id": self.firma_id,
            "category_code": self.category_code,
            "category_name": self.category_name,
            "category_name_en": self.category_name_en,
            "category_name_ar": self.category_name_ar,
            "parent_category_id": self.parent_category_id,
            "category_level": self.category_level,
            "image_url": self.image_url,
            "icon_name": self.icon_name,
            "display_order": self.display_order,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
