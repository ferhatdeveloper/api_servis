import logging
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from app.services.pdks.email_service import EmailService
from app.core.pdks_core_database import database_manager
from sqlalchemy import text

logger = logging.getLogger(__name__)

class ReportScheduler:
    """Raporların zamanlanmış gönderimini yöneten servis"""
    
    _scheduler = AsyncIOScheduler()
    
    @classmethod
    def start(cls):
        """Scheduler'ı başlatır"""
        if not cls._scheduler.running:
            cls._scheduler.add_job(cls._check_and_send_reports, 'cron', minute='*') # Her dakika kontrol et
            cls._scheduler.start()
            logger.info("⏰ Rapor zamanlayıcı başlatıldı (Dakikalık kontrol)")

    @classmethod
    async def _check_and_send_reports(cls):
        """Zamanı gelen raporları kontrol eder ve gönderir"""
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        logger.info(f"🔍 Rapor kontrolü yapılıyor: {current_time}")
        
        try:
            # Not: Burada normalde veritabanından ayarları çekmeliyiz.
            # Şimdilik örnek bir yapı kuruyoruz, tablo henüz yoksa hata almamak için sarmallıyoruz.
            session = database_manager.get_session()
            try:
                # E-posta ayarlarını ve planlanmış raporları çek
                # Tablo: email_report_settings (id, smtp_server, smtp_port, smtp_user, smtp_pass, recipients, schedule_time, is_active)
                result = session.execute(text("SELECT * FROM email_report_settings WHERE is_active = 1 AND schedule_time = :time"), {"time": current_time})
                configs = result.fetchall()
                
                for config in configs:
                    cls._process_and_send(config)
                    
            except Exception as db_e:
                # logger.debug(f"Veritabanı tablosu henüz hazır olmayabilir: {db_e}")
                pass
            finally:
                session.close()
                
        except Exception as e:
            logger.error(f"❌ Rapor kontrol döngüsünde hata: {str(e)}")

    @classmethod
    def _process_and_send(cls, config):
        """Tekil bir raporu hazırlar ve gönderir"""
        # Verileri hazırla (Burada gerçek PDKS verilerini çekmelisiniz)
        report_data = {
            "date": datetime.now().strftime("%d.%m.%Y"),
            "report_name": "Günlük Özet Raporu",
            "total_checkins": "124",  # Örnek veri
            "total_absent": "12",     # Örnek veri
            "late_arrivals": "5",     # Örnek veri
            "active_leaves": "3",      # Örnek veri
            "system_url": "https://pdks.exfin.com" # Örnek URL
        }
        
        smtp_config = {
            "server": config.smtp_server,
            "port": config.smtp_port,
            "user": config.smtp_user,
            "password": config.smtp_pass,
            "use_tls": True
        }
        
        recipients = config.recipients.split(',')
        
        EmailService.send_report_email(smtp_config, [r.strip() for r in recipients], report_data)
