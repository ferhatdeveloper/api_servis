"""
Departman Router - CRUD İşlemleri Örneği
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict
import uuid

from app.core.pdks_dependencies import get_db
from app.services.pdks.department_service import DepartmentService
from app.models.pdks.department import Department, DepartmentCreate, DepartmentUpdate, DepartmentResponse

router = APIRouter(prefix="/departments", tags=["Departments"])


@router.post("/", response_model=DepartmentResponse, status_code=201)
async def create_department(
    department: DepartmentCreate,
    db: Session = Depends(get_db)
):
    """
    Yeni departman oluştur
    """
    service = DepartmentService(db)
    
    # İsim kontrolü
    if service.get_by_name(department.name):
        raise HTTPException(
            status_code=400,
            detail=f"'{department.name}' adında departman zaten mevcut"
        )
    
    new_dept = service.create(department.dict())
    
    return DepartmentResponse.from_orm(new_dept)


@router.get("/", response_model=List[DepartmentResponse])
async def get_departments(
    skip: int = Query(0, ge=0, description="Kayıt atlama"),
    limit: int = Query(100, ge=1, le=1000, description="Kayıt limiti"),
    status: str = Query(None, description="Durum filtresi"),
    db: Session = Depends(get_db)
):
    """
    Tüm departmanları listele (Sayfalanmış)
    """
    service = DepartmentService(db)
    
    # Filtreli sorgu
    query = db.query(service.model)
    
    if status:
        query = query.filter(service.model.status == status)
    
    departments = query.offset(skip).limit(limit).all()
    
    return [DepartmentResponse.from_orm(dept) for dept in departments]


@router.get("/{dept_id}", response_model=DepartmentResponse)
async def get_department(
    dept_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Belirli bir departmanı getir
    """
    service = DepartmentService(db)
    department = service.get_by_id(dept_id)
    
    if not department:
        raise HTTPException(
            status_code=404,
            detail=f"Departman bulunamadı: {dept_id}"
        )
    
    return DepartmentResponse.from_orm(department)


@router.put("/{dept_id}", response_model=DepartmentResponse)
async def update_department(
    dept_id: uuid.UUID,
    department: DepartmentUpdate,
    db: Session = Depends(get_db)
):
    """
    Departman güncelle
    """
    service = DepartmentService(db)
    
    updated = service.update(
        dept_id,
        department.dict(exclude_unset=True)
    )
    
    return DepartmentResponse.from_orm(updated)


@router.delete("/{dept_id}", status_code=204)
async def delete_department(
    dept_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Departman sil
    """
    service = DepartmentService(db)
    service.delete(dept_id)
    
    return None


@router.get("/{dept_id}/stats", response_model=Dict)
async def get_department_stats(
    dept_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Departman istatistikleri
    """
    from sqlalchemy import func, text
    from app.models.pdks.employee import Employee
    
    service = DepartmentService(db)
    department = service.get_by_id(dept_id)
    
    if not department:
        raise HTTPException(status_code=404, detail="Departman bulunamadı")
    
    # İstatistik sorgusu
    stats = db.query(
        func.count(Employee.id).label('total_employees'),
        func.avg(Employee.salary).label('avg_salary'),
        func.max(Employee.salary).label('max_salary'),
        func.min(Employee.salary).label('min_salary')
    ).filter(Employee.department_id == dept_id).first()
    
    return {
        "department": department.name,
        "stats": {
            "total_employees": stats.total_employees or 0,
            "avg_salary": float(stats.avg_salary) if stats.avg_salary else 0,
            "max_salary": float(stats.max_salary) if stats.max_salary else 0,
            "min_salary": float(stats.min_salary) if stats.min_salary else 0
        }
    }


@router.get("/search/query", response_model=List[DepartmentResponse])
async def search_departments(
    q: str = Query(..., description="Arama terimi"),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Departman ara
    """
    service = DepartmentService(db)
    departments = service.search(q, limit)
    
    return [DepartmentResponse.from_orm(dept) for dept in departments]


@router.post("/bulk", response_model=Dict)
async def bulk_create_departments(
    departments: List[DepartmentCreate],
    db: Session = Depends(get_db)
):
    """
    Performanslı toplu departman oluşturma
    """
    service = DepartmentService(db)
    
    created = service.bulk_create([dept.dict() for dept in departments])
    
    return {
        "status": "success",
        "created_count": len(created),
        "message": f"{len(created)} departman oluşturuldu"
    }
