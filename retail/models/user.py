"""RetailOS - User Model"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.sql import func
from retail.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    discount_limit = Column(Float, default=10.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
