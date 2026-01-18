from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from typing import List, Optional
from app.core.pdks_database import get_db
from app.services.pdks.email_service import EmailService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email-settings", tags=["Email Settings"])

class EmailSettingsSchema(BaseModel):
    smtp_server: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    recipients: str
    schedule_time: str
    is_active: bool = True

class TestEmailRequest(BaseModel):
    smtp_server: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    recipient: str

@router.get("/")
async def get_email_settings(db: Session = Depends(get_db)):
    """Mevcut e-posta ayarlarını getirir"""
    try:
        # Tablo yoksa oluştur (Basit yaklaşım)
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS email_report_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                smtp_server TEXT,
                smtp_port INTEGER,
                smtp_user TEXT,
                smtp_pass TEXT,
                recipients TEXT,
                schedule_time TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        """))
        db.commit()
        
        result = db.execute(text("SELECT * FROM email_report_settings LIMIT 1"))
        setting = result.fetchone()
        
        if setting:
            return {
                "smtp_server": setting.smtp_server,
                "smtp_port": setting.smtp_port,
                "smtp_user": setting.smtp_user,
                "smtp_pass": setting.smtp_pass,
                "recipients": setting.recipients,
                "schedule_time": setting.schedule_time,
                "is_active": bool(setting.is_active)
            }
        return None
    except Exception as e:
        logger.error(f"E-posta ayarları getirme hatası: {e}")
        return None

@router.post("/")
async def save_email_settings(settings: EmailSettingsSchema, db: Session = Depends(get_db)):
    """E-posta ayarlarını kaydeder veya günceller"""
    try:
        # Önce mevcut kayıt var mı bak
        result = db.execute(text("SELECT id FROM email_report_settings LIMIT 1"))
        existing = result.fetchone()
        
        if existing:
            db.execute(text("""
                UPDATE email_report_settings SET 
                smtp_server = :server, smtp_port = :port, smtp_user = :user, 
                smtp_pass = :pass, recipients = :recips, schedule_time = :time, 
                is_active = :active WHERE id = :id
            """), {
                "server": settings.smtp_server, "port": settings.smtp_port,
                "user": settings.smtp_user, "pass": settings.smtp_pass,
                "recips": settings.recipients, "time": settings.schedule_time,
                "active": 1 if settings.is_active else 0, "id": existing.id
            })
        else:
            db.execute(text("""
                INSERT INTO email_report_settings 
                (smtp_server, smtp_port, smtp_user, smtp_pass, recipients, schedule_time, is_active)
                VALUES (:server, :port, :user, :pass, :recips, :time, :active)
            """), {
                "server": settings.smtp_server, "port": settings.smtp_port,
                "user": settings.smtp_user, "pass": settings.smtp_pass,
                "recips": settings.recipients, "time": settings.schedule_time,
                "active": 1 if settings.is_active else 0
            })
        
        db.commit()
        return {"status": "success", "message": "Ayarlar başarıyla kaydedildi"}
    except Exception as e:
        db.rollback()
        logger.error(f"E-posta ayarları kaydetme hatası: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def send_test_email(request: TestEmailRequest):
    """SMTP ayarlarını test etmek için mail gönderir"""
    smtp_config = {
        "server": request.smtp_server,
        "port": request.smtp_port,
        "user": request.smtp_user,
        "password": request.smtp_pass,
        "use_tls": True
    }
    
    report_data = {
        "date": "TEST",
        "report_name": "Test E-postası",
        "total_checkins": "99",
        "total_absent": "0",
        "late_arrivals": "0",
        "active_leaves": "0",
        "system_url": "#"
    }
    
    success = EmailService.send_report_email(smtp_config, [request.recipient], report_data)
    
    if success:
        return {"status": "success", "message": "Test e-postası başarıyla gönderildi"}
    else:
        raise HTTPException(status_code=400, detail="E-postası gönderilemedi. Lütfen ayarları kontrol edin.")
