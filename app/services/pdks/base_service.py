"""
Temel servis sınıfı
"""
from sqlalchemy.orm import Session
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')


class BaseService(Generic[T]):
    """Tüm servisler için temel sınıf"""
    
    def __init__(self, db: Session, model: type):
        self.db = db
        self.model = model
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Tüm kayıtları al"""
        return self.db.query(self.model).offset(skip).limit(limit).all()
    
    def get_by_id(self, id: int) -> Optional[T]:
        """ID ile kayıt al"""
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def create(self, data: dict) -> T:
        """Yeni kayıt oluştur"""
        instance = self.model(**data)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance
    
    def update(self, id: int, data: dict) -> T:
        """Kayıt güncelle"""
        instance = self.get_by_id(id)
        if not instance:
            raise ValueError(f"Kayıt bulunamadı: {id}")
        
        for key, value in data.items():
            setattr(instance, key, value)
        
        self.db.commit()
        self.db.refresh(instance)
        return instance
    
    def delete(self, id: int) -> bool:
        """Kayıt sil"""
        instance = self.get_by_id(id)
        if not instance:
            raise ValueError(f"Kayıt bulunamadı: {id}")
        
        self.db.delete(instance)
        self.db.commit()
        return True
