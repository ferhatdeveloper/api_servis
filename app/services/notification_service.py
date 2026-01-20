import requests
import json
import os
import sqlite3

class NotificationService:
    def __init__(self, db_path="exfin.db"):
        self.db_path = db_path

    def get_setting(self, key, default=None):
        try:
            if not os.path.exists(self.db_path): return default
            conn = sqlite3.connect(self.db_path)
            res = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
            conn.close()
            return res[0] if res else default
        except: return default

    def send_whatsapp(self, phone, message, file_path=None):
        """
        Sends WhatsApp message. 
        Note: Official API requires templates. This simulates a generic provider or 
        uses a redirect link for local app if client-side. 
        For server-side, we'd need a provider like NetGSM or Twilio.
        """
        provider = self.get_setting("Whatsapp_Provider", "Twilio") # Twilio, NetGSM, Local
        
        if provider == "Twilio":
            sid = self.get_setting("Twilio_SID")
            token = self.get_setting("Twilio_Token")
            from_num = self.get_setting("Twilio_From")
            
            if not (sid and token and from_num):
                return False, "Twilio ayarları eksik."
            
            try:
                # Mock request for now as we don't have installed twilio lib in main scope yet,
                # but standard HTTP request is safer for portability
                url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
                auth = (sid, token)
                data = {
                    "From": f"whatsapp:{from_num}",
                    "To": f"whatsapp:{phone}",
                    "Body": message
                }
                
                resp = requests.post(url, data=data, auth=auth)
                if resp.status_code in [200, 201]:
                    return True, "Gönderildi"
                else:
                    return False, f"Hata: {resp.text}"
            except Exception as e:
                return False, str(e)

        return False, "Sağlayıcı yapılandırılmadı."

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
