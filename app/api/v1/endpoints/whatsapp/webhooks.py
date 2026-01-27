from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/events")
async def handle_whatsapp_events(request: Request, db: Session = Depends(get_db)):
    """
    Handle incoming webhooks from Evolution API.
    Capture incoming messages and save to local DB.
    """
    try:
        data = await request.json()
        event_type = data.get("event")
        instance = data.get("instance")
        
        # We only care about new messages for now
        if event_type == "messages.upsert":
            message_data = data.get("data", {})
            key = message_data.get("key", {})
            
            # Skip if message is from us (outbound messages also trigger upsert)
            if key.get("fromMe") is True:
                return {"status": "skipped", "reason": "outbound"}
            
            remote_jid = key.get("remoteJid", "")
            # Extract phone from jid (e.g. 905xxxxxxxxx@s.whatsapp.net)
            phone = remote_jid.split("@")[0]
            
            # Extract content
            message_dict = message_data.get("message", {})
            content = ""
            msg_type = "text"
            
            if "conversation" in message_dict:
                content = message_dict["conversation"]
            elif "extendedTextMessage" in message_dict:
                content = message_dict["extendedTextMessage"].get("text", "")
            elif "imageMessage" in message_dict:
                content = "[Image]"
                msg_type = "image"
            elif "videoMessage" in message_dict:
                content = "[Video]"
                msg_type = "video"
            elif "documentMessage" in message_dict:
                content = "[Document]"
                msg_type = "document"
            
            # 1. Get or Create Contact
            contact_name = message_data.get("pushName", "Unknown")
            contact_query = "SELECT id FROM whatsapp_contacts WHERE phone = :phone"
            contact = db.execute(contact_query, {"phone": phone}).fetchone()
            
            if not contact:
                insert_contact = """
                    INSERT INTO whatsapp_contacts (phone, name, created_at)
                    VALUES (:phone, :name, NOW())
                    RETURNING id
                """
                contact_id = db.execute(insert_contact, {"phone": phone, "name": contact_name}).fetchone()[0]
            else:
                contact_id = contact[0]
                # Update last seen name if it was Unknown
                db.execute("UPDATE whatsapp_contacts SET last_message_at = NOW() WHERE id = :id", {"id": contact_id})

            # 2. Save Message
            insert_msg = """
                INSERT INTO whatsapp_messages (
                    contact_id, contact_phone, message_type, message_content,
                    direction, status, firma_id, created_at, sent_at
                ) VALUES (
                    :contact_id, :phone, :msg_type, :content,
                    'inbound', 'received', '001', NOW(), NOW()
                )
            """
            db.execute(insert_msg, {
                "contact_id": contact_id,
                "phone": phone,
                "msg_type": msg_type,
                "content": content
            })
            
            db.commit()
            logger.info(f"Incoming WhatsApp message saved: {phone}")

        return {"status": "success"}
    except Exception as e:
        db.rollback()
        logger.error(f"Webhook processing error: {str(e)}")
        # Still return 200 to prevent Evolution API from retrying infinitely
        return {"status": "error", "message": str(e)}
