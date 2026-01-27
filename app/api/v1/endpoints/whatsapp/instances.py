from fastapi import APIRouter, Depends, Query
from app.services.whatsapp_service import WhatsAppService

router = APIRouter()
whatsapp_service = WhatsAppService()

@router.get("/status")
async def get_instance_status():
    """Check if WhatsApp is connected"""
    return whatsapp_service.get_status()

@router.get("/connect")
async def get_qr():
    """Generate QR code for login"""
    return whatsapp_service.get_qr_code()

@router.delete("/logout")
async def logout_instance():
    """Disconnect WhatsApp"""
    return whatsapp_service.logout()

@router.post("/sync-webhook")
async def sync_webhook(webhook_url: str = Query(..., description="Your Backend URL (e.g. http://server-ip:8000/api/v1/whatsapp/webhooks/events)")):
    """Sync your backend URL to Evolution API for webhooks"""
    return whatsapp_service.set_webhook(webhook_url)
