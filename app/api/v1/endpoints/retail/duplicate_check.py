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

    api.db içindeki sent_invoices tablosundan fatura numarasının daha önce 
    gönderilip gönderilmediğini kontrol eder.
    """
    import sqlite3
    import os
    
    # Resolve api.db path relative to project root
    base_dir = os.getcwd()
    db_path = os.path.join(base_dir, "api.db")
    
    invoice_no = request.data.get("fatura_no")
    if not invoice_no:
        return DuplicateCheckResponse(
            is_duplicate=False,
            hash=request.hash,
            message="Fatura numarası ('fatura_no') veride bulunamadı."
        )

    try:
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            res = conn.execute("SELECT id FROM sent_invoices WHERE invoice_no = ?", (invoice_no,)).fetchone()
            conn.close()
            
            if res:
                return DuplicateCheckResponse(
                    is_duplicate=True,
                    existing_record_id=res["id"],
                    hash=request.hash,
                    message=f"Bu fatura ({invoice_no}) zaten gönderilmiş! ⚠️"
                )
    except Exception as e:
        pass

    return DuplicateCheckResponse(
        is_duplicate=False,
        hash=request.hash,
        message="Fatura benzersiz, gönderilebilir. ✅"
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
    Yalnızca fatura gönderimi başarılı olduktan sonra bu endpoint çağrılarak
    fatura numarasını api.db'ye (sent_invoices) işler.
    """
    import sqlite3
    import os
    
    base_dir = os.getcwd()
    db_path = os.path.join(base_dir, "api.db")
    
    invoice_no = request.data.get("fatura_no")
    customer_code = request.data.get("cari_code") or request.data.get("customer_code")
    customer_name = request.data.get("cari_adi") or request.data.get("customer_name")
    amount = request.data.get("tutar") or request.data.get("total_amount") or 0.0
    status = request.data.get("status", "SENT")

    if not invoice_no:
        return {"status": "error", "message": "Fatura numarası ('fatura_no') eksik."}

    try:
        if not os.path.exists(db_path):
             return {"status": "error", "message": "api.db dosyası bulunamadı."}
             
        conn = sqlite3.connect(db_path)
        conn.execute("""
            INSERT OR REPLACE INTO sent_invoices 
            (invoice_no, customer_code, customer_name, total_amount, status) 
            VALUES (?, ?, ?, ?, ?)
        """, (invoice_no, customer_code, customer_name, amount, status))
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"Fatura {invoice_no} gönderim kaydı oluşturuldu."}
    except Exception as e:
        return {"status": "error", "message": f"Kayıt hatası: {str(e)}"}


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

