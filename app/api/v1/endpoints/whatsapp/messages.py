from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import json

from app.core.async_database import get_db
from app.services.whatsapp_service import WhatsAppService

router = APIRouter()
whatsapp_service = WhatsAppService()

# ============================================================================
# MODELS
# ============================================================================

class MessageBase(BaseModel):
    contact_phone: str = Field(..., description="Recipient Phone (905xxxxxxxxx)")
    
class TextMessageCreate(MessageBase):
    text: str = Field(..., description="Message Content")

class MediaMessageCreate(MessageBase):
    media_url: str = Field(..., description="Link to file")
    media_type: str = Field("image", description="image, video, document, audio")
    caption: Optional[str] = None

class LocationMessageCreate(MessageBase):
    latitude: float
    longitude: float
    title: Optional[str] = None
    address: Optional[str] = None

# ============================================================================
# DB HELPERS
# ============================================================================

def log_whatsapp_to_db(db: Session, phone: str, type: str, content: str, firma_id: str):
    # Get or create contact
    contact_query = "SELECT id FROM whatsapp_contacts WHERE phone = :phone"
    contact = db.execute(contact_query, {"phone": phone}).fetchone()
    
    if not contact:
        insert_contact = "INSERT INTO whatsapp_contacts (phone, name, created_at) VALUES (:phone, 'Unknown', NOW()) RETURNING id"
        contact_id = db.execute(insert_contact, {"phone": phone}).fetchone()[0]
    else:
        contact_id = contact[0]
        
    # Insert message
    insert_query = """
        INSERT INTO whatsapp_messages (
            contact_id, contact_phone, message_type, message_content,
            direction, status, firma_id, created_at
        ) VALUES (
            :contact_id, :phone, :type, :content,
            'outbound', 'pending', :firma_id, NOW()
        )
        RETURNING id
    """
    res = db.execute(insert_query, {
        "contact_id": contact_id,
        "phone": phone,
        "type": type,
        "content": content,
        "firma_id": firma_id
    })
    msg_id = res.fetchone()[0]
    db.commit()
    return msg_id, contact_id

def update_db_status(db: Session, msg_id: int, success: bool, feedback: str):
    status = "sent" if success else "failed"
    query = """
        UPDATE whatsapp_messages 
        SET status = :status, 
            error_message = :error_msg,
            sent_at = CASE WHEN :status = 'sent' THEN NOW() ELSE NULL END
        WHERE id = :msg_id
    """
    db.execute(query, {"status": status, "error_msg": None if success else str(feedback), "msg_id": msg_id})
    db.commit()

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/send-text")
async def send_text(
    payload: TextMessageCreate,
    firma_id: str = Query("001"),
    db: Session = Depends(get_db)
):
    msg_id, _ = log_whatsapp_to_db(db, payload.contact_phone, "text", payload.text, firma_id)
    
    result = whatsapp_service.send_text(payload.contact_phone, payload.text)
    success = "key" in result or result.get("status") == "sent"
    
    update_db_status(db, msg_id, success, result.get("message", "Error"))
    
    return {"success": success, "result": result}

@router.post("/send-media")
async def send_media(
    payload: MediaMessageCreate,
    firma_id: str = Query("001"),
    db: Session = Depends(get_db)
):
    log_content = f"Media: {payload.media_type} - {payload.caption or ''}"
    msg_id, _ = log_whatsapp_to_db(db, payload.contact_phone, payload.media_type, log_content, firma_id)
    
    result = whatsapp_service.send_media(
        phone=payload.contact_phone,
        media_url=payload.media_url,
        caption=payload.caption,
        media_type=payload.media_type
    )
    
    success = "key" in result or result.get("status") == "sent"
    update_db_status(db, msg_id, success, result.get("message", "Error"))
    
    return {"success": success, "result": result}

@router.post("/send-location")
async def send_location(
    payload: LocationMessageCreate,
    firma_id: str = Query("001"),
    db: Session = Depends(get_db)
):
    log_content = f"Location: {payload.latitude}, {payload.longitude}"
    msg_id, _ = log_whatsapp_to_db(db, payload.contact_phone, "location", log_content, firma_id)
    
    result = whatsapp_service.send_location(
        phone=payload.contact_phone,
        latitude=payload.latitude,
        longitude=payload.longitude,
        title=payload.title,
        address=payload.address
    )
    
    success = "key" in result or result.get("status") == "sent"
    update_db_status(db, msg_id, success, result.get("message", "Error"))
    
    return {"success": success, "result": result}
