"""
Hikvision Webhook Router
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.core.pdks_dependencies import get_db
from app.models.pdks.hikvision import AttendanceLog, Base

# Router tanımla prefix='/hikvision' olacak (api.py içinde /api altına eklenecek -> /api/hikvision)
router = APIRouter(prefix="/hikvision", tags=["Hikvision"])

@router.post("/webhook")
async def receive_event(request: Request, db: Session = Depends(get_db)):
    """
    Hikvision cihazından gelen eventleri karşılar.
    URL: POST /api/hikvision/webhook
    """
    try:
        # 1. JSON verisini al
        try:
            payload = await request.json()
        except:
            # Bazen cihazlar farklı content-type gönderebilir, body'i text olarak alıp deneyelim
            body = await request.body()
            payload = json.loads(body)
            
        # 2. Olay var mı kontrol et
        event_data = payload.get("AccessControllerEvent", {})
        
        # 3. Çalışan verisi var mı? (Sadece personel geçişlerini kaydet)
        if event_data.get("employeeNoString"):
            
            # Zaman formatı: "2024-01-10T21:45:00+03:00" -> datetime objesine
            event_time_str = event_data.get("absTime", datetime.now().isoformat())
            try:
                event_time = datetime.fromisoformat(event_time_str)
            except:
                event_time = datetime.now()

            # Yeni log oluştur
            new_log = AttendanceLog(
                employee_id=event_data.get("employeeNoString"),
                event_time=event_time,
                event_type=analyze_event_type(event_data.get("subEventType", 0)),
                original_event_type=event_data.get("subEventType"),
                device_ip=payload.get("ipAddress", "Unknown"),
                device_name=event_data.get("name", "Hikvision Device"),
                raw_data=json.dumps(payload, ensure_ascii=False)
            )
            
            # Veritabanına kaydet
            db.add(new_log)
            db.commit()
            
            return {"status": "success", "message": "Log saved", "employee": new_log.employee_id}
            
        return {"status": "ignored", "message": "No employee data in event"}

    except Exception as e:
        print(f"Hikvision Webhook Error: {e}")
        # Hikvision cihazı hata almasın diye 200 dönüyoruz ama logluyoruz
        return {"status": "error", "message": str(e)}

def analyze_event_type(sub_type):
    """Hikvision olay kodlarını okunabilir tipe çevirir"""
    mapping = {
        1: "card",          # Access Granted by Card
        75: "face",         # Access Granted by Face
        4: "fingerprint",   # Access Granted by Fingerprint (Genelde 4 veya 5)
        5: "fingerprint",
        25: "pwd",          # Access Granted by Password
    }
    return mapping.get(sub_type, "other")

@router.get("/logs")
async def get_logs(limit: int = 50, db: Session = Depends(get_db)):
    """Son logları listele (Test amaçlı)"""
    return db.query(AttendanceLog).order_by(AttendanceLog.event_time.desc()).limit(limit).all()
