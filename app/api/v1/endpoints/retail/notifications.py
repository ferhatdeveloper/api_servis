"""
Notifications API Endpoints
Çok kanallı (Multi-channel) bildirim sistemi (Push, Email, SMS, In-App).
OneSignal ve SMTP entegrasyonlarını içerir.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field

from app.core.async_database import get_db

router = APIRouter()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class NotificationCreate(BaseModel):
    type: str = Field(..., description="Bildirim tipi: 'info', 'success', 'warning', 'error'")
    channel: str = Field(..., description="Gönderim kanalı: 'push', 'email', 'sms', 'in-app' veya 'all'")
    title: str = Field(..., description="Bildirim başlığı")
    message: str = Field(..., description="Bildirim içeriği")
    user_id: Optional[str] = Field(None, description="Hedef kullanıcı ID'si (Boş bırakılırsa genel olabilir)")
    customer_id: Optional[str] = Field(None, description="İlgili müşteri ID'si (Opsiyonel)")
    role_id: Optional[str] = Field(None, description="Belirli bir role gönderim yapılacaksa rol ID (Opsiyonel)")
    action_url: Optional[str] = Field(None, description="Tıklandığında gidilecek URL")
    action_label: Optional[str] = Field(None, description="Buton üzerinde yazacak metin")
    metadata: Optional[dict] = Field(None, description="Ekstra veri (JSON objesi)")


class NotificationResponse(BaseModel):
    id: int = Field(..., description="Bildirim ID")
    type: str = Field(..., description="Bildirim tipi")
    channel: str = Field(..., description="Kanal")
    title: str = Field(..., description="Başlık")
    message: str = Field(..., description="Mesaj")
    status: str = Field(..., description="Durum: 'pending', 'sent', 'read', 'failed'")
    read_at: Optional[datetime] = Field(None, description="Okunma zamanı")
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    created_at: datetime = Field(..., description="Oluşturulma zamanı")


class NotificationPreferences(BaseModel):
    push_enabled: bool = Field(True, description="Mobil bildirimler açık mı?")
    email_enabled: bool = Field(True, description="E-posta bildirimleri açık mı?")
    sms_enabled: bool = Field(False, description="SMS bildirimleri açık mı?")
    in_app_enabled: bool = Field(True, description="Uygulama içi bildirimler açık mı?")
    categories: dict = Field(
        default={
            "sales": True,
            "stock": True,
            "finance": True,
            "system": True,
            "marketing": False
        },
        description="Bildirim kategorileri ve durumları (Satış, Stok vb.)"
    )
    email_address: Optional[str] = Field(None, description="Alternatif e-posta adresi")
    phone_number: Optional[str] = Field(None, description="SMS için telefon numarası")


# ============================================================================
# ENDPOINTS: Notifications
# ============================================================================

@router.post("/send")
async def send_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db)
):
    """
    **Bildirim Gönder**

    Kullanıcıya veya bir gruba bildirim gönderir.
    Veritabanına kaydeder ve seçilen kanala (OneSignal Push, Email vb.) iletir.
    
    - **push**: OneSignal üzerinden mobil bildirim.
    - **email**: SMTP üzerinden e-posta.
    - **in-app**: Sadece uygulama içi paneline düşer.
    """
    try:
        query = """
            INSERT INTO notifications (
                type, channel, title, message,
                user_id, customer_id, role_id,
                action_url, action_label, metadata,
                status, created_at
            ) VALUES (
                :type, :channel, :title, :message,
                :user_id, :customer_id, :role_id,
                :action_url, :action_label, :metadata,
                'pending', NOW()
            )
            RETURNING id
        """
        
        import json
        
        result = db.execute(query, {
            "type": notification.type,
            "channel": notification.channel,
            "title": notification.title,
            "message": notification.message,
            "user_id": notification.user_id,
            "customer_id": notification.customer_id,
            "role_id": notification.role_id,
            "action_url": notification.action_url,
            "action_label": notification.action_label,
            "metadata": json.dumps(notification.metadata) if notification.metadata else None
        })
        
        notification_id = result.fetchone()[0]
        db.commit()
        
        # Trigger external notifications (Fire & Forget)
        if notification.channel == "push" or notification.channel == "all":
             import asyncio
             asyncio.create_task(send_push_notification(notification))

        return {
            "success": True,
            "notification_id": notification_id,
            "message": "Bildirim başarıyla kuyruğa alındı."
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

async def send_push_notification(notification: NotificationCreate):
    """
    **OneSignal Push Gönderimi**
    
    Arka planda çalışır. Bloklamaması için async/thread kullanır.
    """
    from app.core.config import settings
    import requests
    import json
    
    if not settings.ONESIGNAL_APP_ID or not settings.ONESIGNAL_API_KEY:
        print("OneSignal configuration missing, skipping push.")
        return

    try:
        header = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Basic {settings.ONESIGNAL_API_KEY}"
        }

        payload = {
            "app_id": settings.ONESIGNAL_APP_ID,
            "headings": {"en": notification.title},
            "contents": {"en": notification.message},
            "channel_for_external_user_ids": "push",
            "include_external_user_ids": [notification.user_id] if notification.user_id else [] 
        }
        
        if not payload["include_external_user_ids"]:
             return

        if notification.metadata:
            payload["data"] = notification.metadata
            
        if notification.action_url:
            payload["url"] = notification.action_url

        # Run blocking request in thread
        import asyncio
        await asyncio.to_thread(requests.post, "https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))
        
    except Exception as e:
        print(f"OneSignal Error: {e}")


@router.get("/list")
async def list_notifications(
    user_id: str = Query(..., description="Bildirimleri çekilecek kullanıcı ID"),
    status: Optional[str] = Query(None, description="Filtre: 'read', 'unread' vb."),
    type: Optional[str] = Query(None, description="Filtre: 'info', 'warning' vb."),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """
    **Bildirim Listesi**

    Bir kullanıcının geçmiş bildirimlerini listeler.
    Sayfalama (pagination) ve filtreleme destekler.
    """
    try:
        where_clauses = ["user_id = :user_id"]
        params = {"user_id": user_id}
        
        if status:
            where_clauses.append("status = :status")
            params["status"] = status
        
        if type:
            where_clauses.append("type = :type")
            params["type"] = type
        
        where_clause = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                id, type, channel, title, message, status,
                read_at, action_url, action_label, created_at
            FROM notifications
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        
        params["limit"] = limit
        params["offset"] = offset
        
        result = db.execute(query, params)
        
        notifications = []
        for row in result:
            notifications.append({
                "id": row[0],
                "type": row[1],
                "channel": row[2],
                "title": row[3],
                "message": row[4],
                "status": row[5],
                "read_at": row[6].isoformat() if row[6] else None,
                "action_url": row[7],
                "action_label": row[8],
                "created_at": row[9].isoformat() if row[9] else None
            })
        
        # Get unread count
        count_query = """
            SELECT COUNT(*)
            FROM notifications
            WHERE user_id = :user_id AND status != 'read'
        """
        
        unread_count = db.execute(count_query, {"user_id": user_id}).fetchone()[0]
        
        return {
            "success": True,
            "notifications": notifications,
            "unread_count": unread_count,
            "total": len(notifications)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/mark-read")
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """
    **Okundu Olarak İşaretle**

    Tek bir bildirimi okundu (read) durumuna çeker.
    """
    try:
        query = """
            UPDATE notifications
            SET status = 'read',
            read_at = NOW()
            WHERE id = :notification_id
              AND status != 'read'
        """
        
        db.execute(query, {"notification_id": notification_id})
        db.commit()
        
        return {
            "success": True,
            "message": "Notification marked as read"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-all-read")
async def mark_all_read(
    user_id: str = Query(..., description="İşlem yapılacak kullanıcı ID"),
    db: Session = Depends(get_db)
):
    """
    **Tümünü Okundu Olarak İşaretle**

    Kullanıcının bekleyen tüm bildirimlerini 'okundu' (read) statüsüne günceller.
    Genellikle bildirim merkezi açıldığında veya 'Tümünü Okundu Yap' butonu ile çağrılır.
    """
    try:
        query = """
            UPDATE notifications
            SET status = 'read',
                read_at = NOW()
            WHERE user_id = :user_id
              AND status != 'read'
        """
        
        result = db.execute(query, {"user_id": user_id})
        db.commit()
        
        return {
            "success": True,
            "marked_count": result.rowcount
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """
    **Bildirim Sil**

    Belirtilen ID'li bildirimi veritabanından kalıcı olarak siler.
    """
    try:
        query = "DELETE FROM notifications WHERE id = :notification_id"
        db.execute(query, {"notification_id": notification_id})
        db.commit()
        
        return {
            "success": True,
            "message": "Bildirim silindi."
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS: Preferences
# ============================================================================

@router.get("/preferences/{user_id}")
async def get_preferences(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    **Bildirim Tercihleri (Getir)**

    Kullanıcının bildirim ayarlarını döner.
    Hangi kanalların (Push, Email, SMS) açık olduğu ve kategori bazlı izinleri içerir.
    """
    try:
        query = """
            SELECT 
                push_enabled, email_enabled, sms_enabled, in_app_enabled,
                categories, email_address, phone_number
            FROM notification_preferences
            WHERE user_id = :user_id
        """
        
        result = db.execute(query, {"user_id": user_id}).fetchone()
        
        if not result:
            # Return defaults
            return {
                "success": True,
                "preferences": {
                    "push_enabled": True,
                    "email_enabled": True,
                    "sms_enabled": False,
                    "in_app_enabled": True,
                    "categories": {
                        "sales": True,
                        "stock": True,
                        "finance": True,
                        "system": True,
                        "marketing": False
                    },
                    "email_address": None,
                    "phone_number": None
                }
            }
        
        import json
        
        return {
            "success": True,
            "preferences": {
                "push_enabled": result[0],
                "email_enabled": result[1],
                "sms_enabled": result[2],
                "in_app_enabled": result[3],
                "categories": json.loads(result[4]) if result[4] else {},
                "email_address": result[5],
                "phone_number": result[6]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences/{user_id}")
async def update_preferences(
    user_id: str,
    preferences: NotificationPreferences,
    db: Session = Depends(get_db)
):
    """
    **Bildirim Tercihleri (Güncelle)**

    Kullanıcının bildirim ayarlarını kaydeder/günceller.
    Kullanıcı belirli bir kanalı veya kategoriyi kapatmak isterse burası kullanılır.
    """
    try:
        import json
        
        # Check if preferences exist
        check_query = "SELECT id FROM notification_preferences WHERE user_id = :user_id"
        existing = db.execute(check_query, {"user_id": user_id}).fetchone()
        
        if existing:
            # Update
            query = """
                UPDATE notification_preferences
                SET push_enabled = :push_enabled,
                    email_enabled = :email_enabled,
                    sms_enabled = :sms_enabled,
                    in_app_enabled = :in_app_enabled,
                    categories = :categories,
                    email_address = :email_address,
                    phone_number = :phone_number,
                    updated_at = NOW()
                WHERE user_id = :user_id
            """
        else:
            # Insert
            query = """
                INSERT INTO notification_preferences (
                    user_id, push_enabled, email_enabled, sms_enabled, in_app_enabled,
                    categories, email_address, phone_number
                ) VALUES (
                    :user_id, :push_enabled, :email_enabled, :sms_enabled, :in_app_enabled,
                    :categories, :email_address, :phone_number
                )
            """
        
        db.execute(query, {
            "user_id": user_id,
            "push_enabled": preferences.push_enabled,
            "email_enabled": preferences.email_enabled,
            "sms_enabled": preferences.sms_enabled,
            "in_app_enabled": preferences.in_app_enabled,
            "categories": json.dumps(preferences.categories),
            "email_address": preferences.email_address,
            "phone_number": preferences.phone_number
        })
        
        db.commit()
        
        return {
            "success": True,
            "message": "Tercihler başarıyla güncellendi."
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS: Statistics
# ============================================================================

@router.get("/stats")
async def get_notification_stats(
    user_id: Optional[str] = Query(None, description="Filtre: Kullanıcı ID"),
    start_date: Optional[date] = Query(None, description="Başlangıç Tarihi"),
    end_date: Optional[date] = Query(None, description="Bitiş Tarihi"),
    db: Session = Depends(get_db)
):
    """
    **Bildirim İstatistikleri**

    Sistemdeki bildirimlerin gönderim durumlarını raporlar.
    Kanal (channel), Tip (type) ve Durum (status) bazında gruplayarak sayılar döner.
    """
    try:
        where_clauses = []
        params = {}
        
        if user_id:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = user_id
        
        if start_date:
            where_clauses.append("created_at >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            where_clauses.append("created_at <= :end_date")
            params["end_date"] = end_date
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
            SELECT 
                channel,
                type,
                status,
                COUNT(*) as count
            FROM notifications
            WHERE {where_clause}
            GROUP BY channel, type, status
        """
        
        result = db.execute(query, params)
        
        stats = {}
        for row in result:
            channel = row[0]
            type_val = row[1]
            status = row[2]
            count = row[3]
            
            if channel not in stats:
                stats[channel] = {}
            if type_val not in stats[channel]:
                stats[channel][type_val] = {}
            stats[channel][type_val][status] = count
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
