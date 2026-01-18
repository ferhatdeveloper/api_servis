"""
Departman Modeli - Örnek Model
"""
from typing import Optional
from pydantic import BaseModel
import uuid


class Department(BaseModel):
    """Departman Pydantic model"""
    id: Optional[uuid.UUID] = None
    name: str
    description: Optional[str] = None
    manager_id: Optional[uuid.UUID] = None
    budget: Optional[float] = None
    status: str = "active"
    
    class Config:
        from_attributes = True


class DepartmentCreate(BaseModel):
    """Departman oluşturma modeli"""
    name: str
    description: Optional[str] = None
    manager_id: Optional[uuid.UUID] = None
    budget: Optional[float] = None
    status: str = "active"


class DepartmentUpdate(BaseModel):
    """Departman güncelleme modeli"""
    name: Optional[str] = None
    description: Optional[str] = None
    manager_id: Optional[uuid.UUID] = None
    budget: Optional[float] = None
    status: Optional[str] = None


class DepartmentResponse(BaseModel):
    """Departman response modeli"""
    id: uuid.UUID
    name: str
    description: Optional[str]
    manager_id: Optional[uuid.UUID]
    budget: Optional[float]
    status: str
    
    class Config:
        from_attributes = True
