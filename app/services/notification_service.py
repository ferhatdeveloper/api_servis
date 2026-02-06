import requests
import json
import os
import sqlite3

class NotificationService:
    def __init__(self, db_path="api.db"):
        self.db_path = db_path

    def get_setting(self, key, default=None):
        try:
            if not os.path.exists(self.db_path): return default
            conn = sqlite3.connect(self.db_path)
            res = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            conn.close()
            return res[0] if res else default
        except: return default

    def send_sms(self, phone, message):
        """
        Sends SMS via configured provider (NetGSM, Twilio, etc.)
        """
        provider = self.get_setting("SMS_Provider", "NetGSM")
        
        if provider == "NetGSM":
            user = self.get_setting("Netgsm_User")
            pwd = self.get_setting("Netgsm_Pass")
            header = self.get_setting("Netgsm_Header")
            
            if not (user and pwd): return False, "NetGSM bilgileri eksik."
            
            # Simple XML Post for NetGSM (Mock)
            # In production, implement full XML payload
            return True, "SMS Gönderildi (Simülasyon)"
            
        return False, "SMS Sağlayıcısı bulunamadı."
