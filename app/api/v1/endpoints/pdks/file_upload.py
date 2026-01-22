"""
Dosya yükleme/indirme endpoints
"""
import os
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Optional
import uuid
from datetime import datetime

router = APIRouter(prefix="/files", tags=["Files"])

# Upload dizini
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Alt dizinler
UPLOAD_DIRS = {
    "employee_documents": UPLOAD_DIR / "employee_documents",
    "profile_photos": UPLOAD_DIR / "profile_photos",
    "general": UPLOAD_DIR / "general",
}

# Tüm alt dizinleri oluştur
for dir_path in UPLOAD_DIRS.values():
    dir_path.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: Optional[str] = Query("general", description="Dosya kategorisi"),
    employee_id: Optional[str] = Query(None, description="Çalışan ID'si"),
):
    """
    Dosya yükle
    
    Kategoriler:
    - employee_documents: Çalışan dökümanları
    - profile_photos: Profil fotoğrafları
    - general: Genel dosyalar
    """
    try:
        # Kategori kontrolü
        if category not in UPLOAD_DIRS:
            raise HTTPException(status_code=400, detail=f"Geçersiz kategori: {category}")
        
        # Dosya uzantısı kontrolü
        file_ext = Path(file.filename).suffix
        if not file_ext:
            raise HTTPException(status_code=400, detail="Dosya uzantısı bulunamadı")
        
        # Benzersiz dosya adı oluştur
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        # Kategoriye göre alt dizin seç
        upload_path = UPLOAD_DIRS[category]
        
        # Employee ID varsa alt klasör oluştur
        if employee_id:
            employee_folder = upload_path / employee_id
            employee_folder.mkdir(parents=True, exist_ok=True)
            file_path = employee_folder / unique_filename
        else:
            file_path = upload_path / unique_filename
        
        # Dosyayı kaydet
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Dosya boyutu
        file_size = os.path.getsize(file_path)
        
        # URL oluştur
        relative_path = file_path.relative_to(UPLOAD_DIR)
        file_url = f"/files/download/{relative_path.as_posix()}"
        
        return {
            "status": "success",
            "filename": file.filename,
            "saved_filename": unique_filename,
            "url": file_url,
            "size": file_size,
            "category": category,
            "employee_id": employee_id,
            "uploaded_at": datetime.now().isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya yüklenirken hata: {str(e)}")


@router.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """
    Dosya indir
    """
    try:
        # Güvenlik kontrolü - path traversal saldırısını önle
        safe_path = Path(UPLOAD_DIR / file_path).resolve()
        if not str(safe_path).startswith(str(Path(UPLOAD_DIR).resolve())):
            raise HTTPException(status_code=403, detail="Yetkisiz dosya erişimi")
        
        if not safe_path.exists():
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
        return FileResponse(
            safe_path,
            filename=safe_path.name,
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya indirilemedi: {str(e)}")


@router.delete("/delete/{file_path:path}")
async def delete_file(file_path: str):
    """
    Dosya sil
    """
    try:
        # Güvenlik kontrolü
        safe_path = Path(UPLOAD_DIR / file_path).resolve()
        if not str(safe_path).startswith(str(Path(UPLOAD_DIR).resolve())):
            raise HTTPException(status_code=403, detail="Yetkisiz dosya erişimi")
        
        if not safe_path.exists():
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
        safe_path.unlink()
        
        return {
            "status": "success",
            "message": "Dosya silindi",
            "filename": safe_path.name,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya silinemedi: {str(e)}")


@router.get("/list")
async def list_files(
    category: Optional[str] = Query("general", description="Dosya kategorisi"),
    employee_id: Optional[str] = Query(None, description="Çalışan ID'si"),
):
    """
    Dosya listesi
    """
    try:
        if category not in UPLOAD_DIRS:
            raise HTTPException(status_code=400, detail=f"Geçersiz kategori: {category}")
        
        upload_path = UPLOAD_DIRS[category]
        
        if employee_id:
            employee_folder = upload_path / employee_id
            if not employee_folder.exists():
                return {
                    "status": "success",
                    "files": [],
                    "count": 0,
                }
            files = list(employee_folder.iterdir())
        else:
            files = list(upload_path.iterdir())
        
        file_list = []
        for file_path in files:
            if file_path.is_file():
                file_stats = file_path.stat()
                relative_path = file_path.relative_to(UPLOAD_DIR)
                
                file_list.append({
                    "name": file_path.name,
                    "size": file_stats.st_size,
                    "url": f"/files/download/{relative_path.as_posix()}",
                    "modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                })
        
        return {
            "status": "success",
            "files": file_list,
            "count": len(file_list),
            "category": category,
            "employee_id": employee_id,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya listesi alınamadı: {str(e)}")

