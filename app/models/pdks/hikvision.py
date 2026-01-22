"""
Hikvision Cihaz Logları için Veritabanı Modeli
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AttendanceLog(Base):
    """Cihazdan gelen geçiş loglarını saklayan tablo"""
    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String, index=True, nullable=True) # Personel ID / Kart No
    event_time = Column(DateTime, nullable=False)           # Olay zamanı
    event_type = Column(String, nullable=True)              # face, card, fingerprint, pwd
    original_event_type = Column(Integer, nullable=True)    # Hikvision event code (75, 1, etc.)
    device_ip = Column(String, nullable=True)               # Cihaz IP
    device_name = Column(String, nullable=True)             # Cihaz Adı (opsiyonel)
    raw_data = Column(Text, nullable=True)                  # Ham JSON verisi (debug için)

    def __repr__(self):
        return f"<AttendanceLog(id={self.id}, employee={self.employee_id}, time={self.event_time})>"
