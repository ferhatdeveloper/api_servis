"""
RetailOS - Menu Model
MenÃ¼ yapÄ±sÄ± modeli (Ana Menu, Alt Menu, Sub Menu)
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

from app.core.async_database import Base


class MenuItem(Base):
    """MenÃ¼ Ã¶ÄŸeleri - Ana Menu, Alt Menu, Sub Menu (TÃ¼m kullanÄ±cÄ±lar iÃ§in ortak)"""
    __tablename__ = "menu_items"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # MenÃ¼ Bilgileri
    menu_type = Column(String(50), nullable=False)  # 'section', 'main', 'sub'
    title = Column(String(200))  # Section baÅŸlÄ±ÄŸÄ± iÃ§in
    label = Column(String(200), nullable=False)  # MenÃ¼ Ã¶ÄŸesi etiketi
    label_tr = Column(String(200))  # TÃ¼rkÃ§e etiket
    label_en = Column(String(200))  # Ä°ngilizce etiket
    label_ar = Column(String(200))  # ArapÃ§a etiket
    
    # HiyerarÅŸi
    parent_id = Column(Integer, ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=True)
    section_id = Column(Integer, ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=True)  # Section referansÄ±
    
    # Ekran/ModÃ¼l Bilgileri
    screen_id = Column(String(100))  # ManagementModule'deki screen ID
    icon_name = Column(String(100))  # Lucide icon adÄ±
    badge = Column(String(50), nullable=True)  # Badge metni (Ã¶rn: "NEW", "5")
    
    # SÄ±ralama ve GÃ¶rÃ¼nÃ¼m
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_visible = Column(Boolean, default=True)
    
    # Sistem AlanlarÄ±
    created_by = Column(UUID(as_uuid=True), nullable=True)  # UUID tipinde, users tablosu varsa foreign key eklenir
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    notes = Column(Text)
    
    # Ä°liÅŸkiler
    parent = relationship("MenuItem", remote_side=[id], backref="children", foreign_keys=[parent_id])
    section = relationship("MenuItem", remote_side=[id], foreign_keys=[section_id])
    
    def __repr__(self):
        return f"<MenuItem(id={self.id}, label='{self.label}', type='{self.menu_type}')>"

