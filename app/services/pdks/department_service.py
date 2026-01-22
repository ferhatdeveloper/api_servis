"""
Departman Servisi - CRUD İşlemleri Örneği
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.services.pdks.base_service import BaseService
from app.models.pdks.department import Department
import logging

logger = logging.getLogger(__name__)


class DepartmentService(BaseService[Department]):
    """Departman CRUD servisi"""
    
    def __init__(self, db: Session):
        super().__init__(db, Department)
    
    def get_by_name(self, name: str) -> Optional[Department]:
        """İsme göre departman bul"""
        return self.db.query(self.model).filter(
            self.model.name == name
        ).first()
    
    def search(self, keyword: str, limit: int = 10) -> List[Department]:
        """Arama yap (performanslı)"""
        return self.db.query(self.model)\
            .filter(
                (self.model.name.ilike(f"%{keyword}%")) |
                (self.model.description.ilike(f"%{keyword}%"))
            )\
            .limit(limit)\
            .all()
    
    def get_with_employee_count(self) -> List[Dict[str, Any]]:
        """Departmanları çalışan sayısı ile birlikte getir"""
        from sqlalchemy import func
        from app.models.pdks.employee import Employee
        
        result = self.db.query(
            self.model.id,
            self.model.name,
            self.model.description,
            func.count(Employee.id).label('employee_count')
        ).outerjoin(Employee, self.model.id == Employee.department_id)\
        .group_by(self.model.id)\
        .all()
        
        return [
            {
                "id": row.id,
                "name": row.name,
                "description": row.description,
                "employee_count": row.employee_count
            }
            for row in result
        ]
    
    def bulk_create(self, departments: List[Dict[str, Any]]) -> List[Department]:
        """Performanslı toplu oluşturma"""
        objects = [self.model(**dept) for dept in departments]
        self.db.bulk_save_objects(objects)
        self.db.commit()
        return objects
    
    def update_status(self, id: int, status: str) -> Department:
        """Durum güncelleme"""
        instance = self.get_by_id(id)
        if not instance:
            raise ValueError(f"Departman bulunamadı: {id}")
        
        instance.status = status
        self.db.commit()
        self.db.refresh(instance)
        return instance
