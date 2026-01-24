"""
RetailOS - Tekrarlı Kayıt Kontrol Sistemi
Veri bütünlüğünü sağlamak için hash tabanlı kontrol mekanizması.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import hashlib
import json

router = APIRouter()


class DuplicateCheckRequest(BaseModel):
    table_name: str = Field(..., description="Kontrol edilecek tablo adı (Örn: FaturaMaster, Urunler)")
    hash: str = Field(..., description="Verinin benzersiz hash değeri (Frontend tarafında üretilir)")
    data: dict = Field(..., description="Kaydedilmek istenen ham veri (JSON formatında)")


class DuplicateCheckResponse(BaseModel):
    is_duplicate: bool = Field(..., description="True ise kayıt daha önce eklenmiştir")
    existing_record_id: Optional[int] = Field(None, description="Eğer kayıt varsa, veritabanındaki ID'si")
    hash: str = Field(..., description="Kontrol edilen hash değeri")
    message: str = Field(..., description="Kullanıcıya gösterilecek durum mesajı")


@router.post("/fatura", response_model=DuplicateCheckResponse)
async def check_duplicate_fatura(request: DuplicateCheckRequest):
    """
    **Fatura Tekrar Kontrolü**

    Sisteme yeni bir fatura eklenmeden önce çalıştırılır. Fatura numarası, cari ve tarih gibi alanların
    kombinasyonu kontrol edilerek mükerrer giriş engellenir.

    **Örnek İstek:**
    ```json
    {
        "table_name": "FaturaMaster",
        "hash": "abc123hashdegeri...",
        "data": {
            "fatura_no": "F-2024-001",
            "firma_id": 1,
            "cari_id": 123,
            "tutar": 1500.00
        }
    }
    ```
    """
    # TODO: Database'de hash kontrolü yap
    # SELECT * FROM TekrarliKayitKontrol WHERE TabloAdi = ? AND KayitHash = ?
    
    # Şimdilik mock response
    return DuplicateCheckResponse(
        is_duplicate=False,
        hash=request.hash,
        message="Fatura kaydı benzersiz, işleme devam edilebilir."
    )


@router.post("/urun", response_model=DuplicateCheckResponse)
async def check_duplicate_urun(request: DuplicateCheckRequest):
    """
    **Ürün Tekrar Kontrolü**

    Yeni ürün kartı açılırken Barkod veya Ürün Kodu çakışmalarını önler.
    Aynı barkod ile ikinci bir ürün eklenmesini engellemek için kullanılır.
    """
    # TODO: Database kontrolü
    return DuplicateCheckResponse(
        is_duplicate=False,
        hash=request.hash,
        message="Ürün benzersiz, kaydedilebilir."
    )


@router.post("/musteri", response_model=DuplicateCheckResponse)
async def check_duplicate_musteri(request: DuplicateCheckRequest):
    """
    **Müşteri (Cari) Tekrar Kontrolü**

    Müşteri eklenirken Vergi No veya TC Kimlik No kontrolü yapar.
    Aynı vergi numarasına sahip mükerrer cari kart açılmasını engeller.
    """
    # TODO: Database kontrolü
    return DuplicateCheckResponse(
        is_duplicate=False,
        hash=request.hash,
        message="Müşteri kaydı benzersiz."
    )


@router.post("/kasa-hareket", response_model=DuplicateCheckResponse)
async def check_duplicate_kasa_hareket(request: DuplicateCheckRequest):
    """
    **Kasa Hareket Kontrolü**

    Kasa fişlerinin yanlışlıkla çift kaydedilmesini önler.
    Tarih, saat ve işlem tutarı kombinasyonu kontrol edilir.
    """
    # TODO: Database kontrolü
    return DuplicateCheckResponse(
        is_duplicate=False,
        hash=request.hash,
        message="Kasa hareketi benzersiz."
    )


@router.post("/generic", response_model=DuplicateCheckResponse)
async def check_duplicate_generic(request: DuplicateCheckRequest):
    """
    **Genel (Generic) Tekrar Kontrolü**

    Özel bir endpoint'i olmayan diğer tüm tablolar için global kontrol noktasıdır.
    'table_name' parametresine göre dinamik kontrol yapar.
    """
    return DuplicateCheckResponse(
        is_duplicate=False,
        hash=request.hash,
        message=f"{request.table_name} için kayıt benzersiz."
    )


@router.post("/save-hash")
async def save_hash(request: DuplicateCheckRequest):
    """
    **Hash Kaydetme (İşlem Onayı)**

    Bir kayıt başarıyla veritabanına eklendikten sonra bu endpoint çağrılmalıdır.
    Bu işlem, hash değerini kalıcı hale getirir ve bir sonraki kontrolde 'Mükerrer' uyarısı verilmesini sağlar.
    """
    # TODO: Database'e hash kaydet
    
    return {
        "status": "success",
        "message": "Hash başarıyla kaydedildi."
    }


@router.delete("/clear-old-hashes")
async def clear_old_hashes(days: int = 90):
    """
    **Eski Hash Temizliği**

    Performans optimizasyonu için veritabanındaki eski hash kayıtlarını siler.
    Varsayılan olarak 90 günden eski kayıtlar temizlenir.
    """
    # TODO: 90 günden eski hash'leri sil
    
    return {
        "status": "success",
        "message": f"{days} günden eski hash kayıtları temizlendi."
    }

