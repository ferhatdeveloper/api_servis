import requests
import json
import logging
from typing import Optional, List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        self.api_url = settings.EVOLUTION_API_URL.rstrip('/')
        self.api_key = settings.EVOLUTION_API_TOKEN
        self.instance = settings.EVOLUTION_API_INSTANCE
        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    def _get_url(self, path: str) -> str:
        return f"{self.api_url}/{path}/{self.instance}"

    def _post_request(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        url = self._get_url(path)
        try:
            response = requests.post(url, json=data, headers=self.headers)
            return response.json()
        except Exception as e:
            logger.error(f"WhatsApp API Error (POST {path}): {str(e)}")
            return {"error": True, "message": str(e)}

    def _get_request(self, path: str) -> Dict[str, Any]:
        url = self._get_url(path)
        try:
            response = requests.get(url, headers=self.headers)
            return response.json()
        except Exception as e:
            logger.error(f"WhatsApp API Error (GET {path}): {str(e)}")
            return {"error": True, "message": str(e)}

    # --- Instance Management ---
    def get_status(self):
        """Check connection state"""
        url = f"{self.api_url}/instance/connectionState/{self.instance}"
        try:
            response = requests.get(url, headers=self.headers)
            return response.json()
        except Exception as e:
            return {"error": True, "message": str(e)}

    def get_qr_code(self):
        """Get QR code for connection"""
        url = f"{self.api_url}/instance/connect/{self.instance}"
        try:
            response = requests.get(url, headers=self.headers)
            return response.json()
        except Exception as e:
            return {"error": True, "message": str(e)}

    def logout(self):
        """Logout the instance"""
        url = f"{self.api_url}/instance/logout/{self.instance}"
        try:
            response = requests.delete(url, headers=self.headers)
            return response.json()
        except Exception as e:
            return {"error": True, "message": str(e)}

    # --- Messaging ---
    def send_text(self, phone: str, text: str):
        data = {
            "number": phone,
            "text": text,
            "linkPreview": True
        }
        return self._post_request("message/sendText", data)

    def send_media(self, phone: str, media_url: str, caption: str = "", media_type: str = "image"):
        endpoint_map = {
            "image": "message/sendMedia",
            "video": "message/sendMedia",
            "document": "message/sendMedia",
            "audio": "message/sendWhatsAppAudio"
        }
        
        data = {
            "number": phone,
            "media": media_url,
            "caption": caption,
            "mediaType": media_type
        }
        
        endpoint = endpoint_map.get(media_type, "message/sendMedia")
        return self._post_request(endpoint, data)

    def send_location(self, phone: str, latitude: float, longitude: float, title: str = "", address: str = ""):
        data = {
            "number": phone,
            "latitude": latitude,
            "longitude": longitude,
            "title": title,
            "address": address
        }
        return self._post_request("message/sendLocation", data)

    # --- Groups ---
    def fetch_groups(self):
        return self._get_request("group/fetchAllGroups")

    def create_group(self, name: str, participants: List[str]):
        data = {
            "groupName": name,
            "participants": participants
        }
        return self._post_request("group/create", data)

    def get_group_info(self, group_jid: str):
        url = f"{self.api_url}/group/findGroup/{self.instance}?groupJid={group_jid}"
        try:
            response = requests.get(url, headers=self.headers)
            return response.json()
        except Exception as e:
            return {"error": True, "message": str(e)}

    # --- Configuration ---
    def set_webhook(self, url: str):
        """Configure webhook URL for the instance"""
        data = {
            "enabled": True,
            "url": url,
            "webhookByEvents": False, # Global webhook
            "events": [
                "MESSAGES_UPSERT",
                "MESSAGES_UPDATE",
                "MESSAGES_DELETE",
                "SEND_MESSAGE",
                "CONNECTION_UPDATE"
            ]
        }
        return self._post_request("webhook/set", data)
