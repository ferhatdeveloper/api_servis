"""
RetailOS - Duplicate Check Endpoints
TekrarlÄ± kayÄ±t engelleme sistemi
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import hashlib
import json

router = APIRouter()


class DuplicateCheckRequest(BaseModel):
    table_name: str
    hash: str
    data: dict


class DuplicateCheckResponse(BaseModel):
    is_duplicate: bool
    existing_record_id: Optional[int] = None
    hash: str
    message: str


@router.post("/fatura", response_model=DuplicateCheckResponse)
async def check_duplicate_fatura(request: DuplicateCheckRequest):
    """
    Fatura tekrar kontrolÃ¼
    
    POST /api/v1/duplicate-check/fatura
    {
        "table_name": "FaturaMaster",
        "hash": "abc123...",
        "data": {
            "fatura_no": "F-2024-001",
            "firma_id": 1,
            "cari_id": 123,
            "tutar": 1500.00
        }
    }
    """
    # TODO: Database'de hash kontrolÃ¼ yap
    # SELECT * FROM TekrarliKayitKontrol WHERE TabloAdi = ? AND KayitHash = ?
    
    # Åimdilik mock response
    return DuplicateCheckResponse(
        is_duplicate=False,
        hash=request.hash,
        message="KayÄ±t benzersiz, iÅŸleme devam edilebilir"
    )


@router.post("/urun", response_model=DuplicateCheckResponse)
async def check_duplicate_urun(request: DuplicateCheckRequest):
    """
    ÃœrÃ¼n tekrar kontrolÃ¼
    
    POST /api/v1/duplicate-check/urun
    {
        "table_name": "Urunler",
        "hash": "def456...",
        "data": {
            "urun_kodu": "PRD001",
            "firma_id": 1,
            "barkod": "1234567890123"
        }
    }
    """
    # TODO: Database kontrolÃ¼
    return DuplicateCheckResponse(
        is_duplicate=False,
        hash=request.hash,
        message="ÃœrÃ¼n benzersiz"
    )


@router.post("/musteri", response_model=DuplicateCheckResponse)
async def check_duplicate_musteri(request: DuplicateCheckRequest):
    """
    MÃ¼ÅŸteri tekrar kontrolÃ¼ (TC/Vergi No bazlÄ±)
    """
    # TODO: Database kontrolÃ¼
    return DuplicateCheckResponse(
        is_duplicate=False,
        hash=request.hash,
        message="MÃ¼ÅŸteri benzersiz"
    )


@router.post("/kasa-hareket", response_model=DuplicateCheckResponse)
async def check_duplicate_kasa_hareket(request: DuplicateCheckRequest):
    """
    Kasa hareketi tekrar kontrolÃ¼
    """
    # TODO: Database kontrolÃ¼
    return DuplicateCheckResponse(
        is_duplicate=False,
        hash=request.hash,
        message="Hareket benzersiz"
    )


@router.post("/generic", response_model=DuplicateCheckResponse)
async def check_duplicate_generic(request: DuplicateCheckRequest):
    """
    Genel tekrar kontrolÃ¼ (her tablo iÃ§in)
    
    POST /api/v1/duplicate-check/generic
    {
        "table_name": "KasaHareketleri",
        "hash": "ghi789...",
        "data": { ... }
    }
    """
    # TODO: Generic database kontrolÃ¼
    # Tablo bazÄ±nda hash kontrolÃ¼ yap
    
    return DuplicateCheckResponse(
        is_duplicate=False,
        hash=request.hash,
        message=f"{request.table_name} iÃ§in kayÄ±t benzersiz"
    )


@router.post("/save-hash")
async def save_hash(request: DuplicateCheckRequest):
    """
    BaÅŸarÄ±lÄ± kayÄ±ttan sonra hash'i kaydet
    
    POST /api/v1/duplicate-check/save-hash
    {
        "table_name": "FaturaMaster",
        "hash": "abc123...",
        "data": { ... }
    }
    """
    # TODO: Database'e hash kaydet
    # INSERT INTO TekrarliKayitKontrol (TabloAdi, KayitHash, KayitData) VALUES (?, ?, ?)
    
    return {
        "status": "success",
        "message": "Hash kaydedildi"
    }


@router.delete("/clear-old-hashes")
async def clear_old_hashes(days: int = 90):
    """
    Eski hash'leri temizle (performans iÃ§in)
    
    DELETE /api/v1/duplicate-check/clear-old-hashes?days=90
    """
    # TODO: 90 gÃ¼nden eski hash'leri sil
    # DELETE FROM TekrarliKayitKontrol WHERE OlusturmaTarihi < DATE_SUB(NOW(), INTERVAL ? DAY)
    
    return {
        "status": "success",
        "message": f"{days} gÃ¼nden eski hash'ler temizlendi"
    }

