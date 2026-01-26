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

    def send_whatsapp(self, phone, message, file_path=None):
        """
        Sends WhatsApp message via configured provider.
        BerqenasCloud WhatsApp Api is the preferred free/self-hosted method.
        """
        from app.core.config import settings

        # Load from DB settings or use config defaults
        provider = self.get_setting("Whatsapp_Provider", settings.WHATSAPP_PROVIDER)
        
        # Clean phone number (ensure only digits)
        clean_phone = "".join(filter(str.isdigit, phone))

        if provider == "Evolution":
            api_url = self.get_setting("Evolution_Api_Url", settings.EVOLUTION_API_URL)
            api_token = self.get_setting("Evolution_Api_Token", settings.EVOLUTION_API_TOKEN)
            instance = self.get_setting("Evolution_Instance", settings.EVOLUTION_API_INSTANCE)

            if not (api_url and instance):
                return False, "BerqenasCloud WhatsApp Api ayarları eksik."

            try:
                # BerqenasCloud Engine v2 format
                url = f"{api_url.rstrip('/')}/message/sendText/{instance}"
                headers = {
                    "apikey": api_token,
                    "Content-Type": "application/json"
                }
                data = {
                    "number": clean_phone,
                    "text": message,
                    "linkPreview": True
                }

                resp = requests.post(url, json=data, headers=headers)
                if resp.status_code in [200, 201]:
                    return True, "Gönderildi"
                else:
                    return False, f"BerqenasCloud WhatsApp Api Hatası: {resp.status_code} - {resp.text}"
            except Exception as e:
                return False, f"Bağlantı Hatası: {str(e)}"

        elif provider == "Twilio":
            sid = self.get_setting("Twilio_SID", settings.TWILIO_ACCOUNT_SID)
            token = self.get_setting("Twilio_Token", settings.TWILIO_AUTH_TOKEN)
            from_num = self.get_setting("Twilio_From", settings.TWILIO_WHATSAPP_NUMBER)
            
            if not (sid and token and from_num):
                return False, "Twilio ayarları eksik."
            
            try:
                url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
                auth = (sid, token)
                data = {
                    "From": f"whatsapp:{from_num}",
                    "To": f"whatsapp:{clean_phone}",
                    "Body": message
                }
                
                resp = requests.post(url, data=data, auth=auth)
                if resp.status_code in [200, 201]:
                    return True, "Gönderildi"
                else:
                    return False, f"Twilio Hatası: {resp.text}"
            except Exception as e:
                return False, str(e)

        return False, f"Sağlayıcı ('{provider}') yapılandırılmadı."

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
