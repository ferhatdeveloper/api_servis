"""
WhatsApp API Endpoints
WhatsApp Business messaging integration

@created: 2024-12-18
@author: ExRetailOS Team
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel

from retail.core.database import get_db

router = APIRouter()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class WhatsAppMessageCreate(BaseModel):
    contact_phone: str
    message_type: str  # text, image, document, template
    message_content: str
    template_id: Optional[str] = None
    template_variables: Optional[dict] = None
    media_url: Optional[str] = None
    transaction_type: Optional[str] = None
    transaction_id: Optional[str] = None


class WhatsAppContactCreate(BaseModel):
    name: str
    phone: str
    customer_id: Optional[str] = None
    tags: Optional[list] = []


class WhatsAppTemplateCreate(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    content: str
    category: str  # marketing, transactional, service, utility
    variables: Optional[list] = []
    language: str = 'en'


# ============================================================================
# ENDPOINTS: Messages
# ============================================================================

@router.post("/send")
async def send_whatsapp_message(
    message: WhatsAppMessageCreate,
    firma_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Send WhatsApp message
    """
    try:
        import json
        
        # Get or create contact
        contact_query = """
            SELECT id FROM whatsapp_contacts WHERE phone = :phone
        """
        contact = db.execute(contact_query, {"phone": message.contact_phone}).fetchone()
        
        if not contact:
            # Create contact
            insert_contact = """
                INSERT INTO whatsapp_contacts (phone, name, created_at)
                VALUES (:phone, 'Unknown', NOW())
                RETURNING id
            """
            contact_id = db.execute(insert_contact, {"phone": message.contact_phone}).fetchone()[0]
        else:
            contact_id = contact[0]
        
        # Insert message
        insert_query = """
            INSERT INTO whatsapp_messages (
                contact_id, contact_phone, message_type, message_content,
                direction, status, template_id, template_variables,
                media_url, transaction_type, transaction_id,
                firma_id, created_at
            ) VALUES (
                :contact_id, :contact_phone, :message_type, :message_content,
                'outbound', 'pending', :template_id, :template_variables,
                :media_url, :transaction_type, :transaction_id,
                :firma_id, NOW()
            )
            RETURNING id
        """
        
        result = db.execute(insert_query, {
            "contact_id": contact_id,
            "contact_phone": message.contact_phone,
            "message_type": message.message_type,
            "message_content": message.message_content,
            "template_id": message.template_id,
            "template_variables": json.dumps(message.template_variables) if message.template_variables else None,
            "media_url": message.media_url,
            "transaction_type": message.transaction_type,
            "transaction_id": message.transaction_id,
            "firma_id": firma_id
        })
        
        message_id = result.fetchone()[0]
        
        # Update contact stats
        update_contact = """
            UPDATE whatsapp_contacts
            SET message_count = message_count + 1,
                last_message_at = NOW()
            WHERE id = :contact_id
        """
        db.execute(update_contact, {"contact_id": contact_id})
        
        db.commit()
        
        # TODO: Trigger actual WhatsApp API call
        # await send_via_twilio(message_id)
        # await send_via_messagebird(message_id)
        
        return {
            "success": True,
            "message_id": message_id,
            "status": "pending",
            "message": "WhatsApp message queued for sending"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/messages")
async def list_messages(
    firma_id: str = Query(...),
    contact_phone: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """
    List WhatsApp messages
    """
    try:
        where_clauses = ["firma_id = :firma_id", "direction = 'outbound'"]
        params = {"firma_id": firma_id}
        
        if contact_phone:
            where_clauses.append("contact_phone = :contact_phone")
            params["contact_phone"] = contact_phone
        
        if status:
            where_clauses.append("status = :status")
            params["status"] = status
        
        if start_date:
            where_clauses.append("created_at >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            where_clauses.append("created_at <= :end_date")
            params["end_date"] = end_date
        
        where_clause = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                wm.id, wm.contact_phone, wc.name as contact_name,
                wm.message_type, wm.message_content, wm.status,
                wm.template_id, wm.created_at, wm.sent_at, wm.delivered_at, wm.read_at
            FROM whatsapp_messages wm
            LEFT JOIN whatsapp_contacts wc ON wm.contact_id = wc.id
            WHERE {where_clause}
            ORDER BY wm.created_at DESC
            LIMIT :limit OFFSET :offset
        """
        
        params["limit"] = limit
        params["offset"] = offset
        
        result = db.execute(query, params)
        
        messages = []
        for row in result:
            messages.append({
                "id": row[0],
                "contact_phone": row[1],
                "contact_name": row[2] or "Unknown",
                "message_type": row[3],
                "message_content": row[4],
                "status": row[5],
                "template_id": row[6],
                "created_at": row[7].isoformat() if row[7] else None,
                "sent_at": row[8].isoformat() if row[8] else None,
                "delivered_at": row[9].isoformat() if row[9] else None,
                "read_at": row[10].isoformat() if row[10] else None
            })
        
        return {
            "success": True,
            "messages": messages,
            "count": len(messages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/messages/{message_id}/status")
async def update_message_status(
    message_id: int,
    status: str = Query(...),
    message_sid: Optional[str] = None,
    error_code: Optional[str] = None,
    error_message: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Update WhatsApp message status (webhook callback)
    """
    try:
        query = """
            UPDATE whatsapp_messages
            SET status = :status,
                message_sid = COALESCE(:message_sid, message_sid),
                error_code = :error_code,
                error_message = :error_message,
                sent_at = CASE WHEN :status = 'sent' THEN NOW() ELSE sent_at END,
                delivered_at = CASE WHEN :status = 'delivered' THEN NOW() ELSE delivered_at END,
                read_at = CASE WHEN :status = 'read' THEN NOW() ELSE read_at END,
                failed_at = CASE WHEN :status = 'failed' THEN NOW() ELSE failed_at END
            WHERE id = :message_id
        """
        
        db.execute(query, {
            "message_id": message_id,
            "status": status,
            "message_sid": message_sid,
            "error_code": error_code,
            "error_message": error_message
        })
        
        db.commit()
        
        return {
            "success": True,
            "message": "Status updated"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS: Contacts
# ============================================================================

@router.post("/contacts")
async def create_contact(
    contact: WhatsAppContactCreate,
    db: Session = Depends(get_db)
):
    """
    Create WhatsApp contact
    """
    try:
        import json
        
        query = """
            INSERT INTO whatsapp_contacts (
                name, phone, customer_id, tags, created_at
            ) VALUES (
                :name, :phone, :customer_id, :tags, NOW()
            )
            RETURNING id
        """
        
        result = db.execute(query, {
            "name": contact.name,
            "phone": contact.phone,
            "customer_id": contact.customer_id,
            "tags": json.dumps(contact.tags)
        })
        
        contact_id = result.fetchone()[0]
        db.commit()
        
        return {
            "success": True,
            "contact_id": contact_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contacts")
async def list_contacts(
    search: Optional[str] = None,
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """
    List WhatsApp contacts
    """
    try:
        where_clause = "is_active = TRUE"
        params = {}
        
        if search:
            where_clause += " AND (name ILIKE :search OR phone LIKE :search)"
            params["search"] = f"%{search}%"
        
        query = f"""
            SELECT 
                id, name, phone, customer_id, message_count,
                last_message_at, tags
            FROM whatsapp_contacts
            WHERE {where_clause}
            ORDER BY message_count DESC
            LIMIT :limit OFFSET :offset
        """
        
        params["limit"] = limit
        params["offset"] = offset
        
        result = db.execute(query, params)
        
        import json
        
        contacts = []
        for row in result:
            contacts.append({
                "id": row[0],
                "name": row[1],
                "phone": row[2],
                "customer_id": row[3],
                "message_count": row[4],
                "last_message_at": row[5].isoformat() if row[5] else None,
                "tags": json.loads(row[6]) if row[6] else []
            })
        
        return {
            "success": True,
            "contacts": contacts,
            "count": len(contacts)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS: Templates
# ============================================================================

@router.post("/templates")
async def create_template(
    template: WhatsAppTemplateCreate,
    db: Session = Depends(get_db)
):
    """
    Create WhatsApp template
    """
    try:
        import json
        
        query = """
            INSERT INTO whatsapp_templates (
                id, name, description, content, category,
                variables, language, status, created_at
            ) VALUES (
                :id, :name, :description, :content, :category,
                :variables, :language, 'draft', NOW()
            )
        """
        
        db.execute(query, {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "content": template.content,
            "category": template.category,
            "variables": json.dumps(template.variables),
            "language": template.language
        })
        
        db.commit()
        
        return {
            "success": True,
            "template_id": template.id,
            "message": "Template created (requires WhatsApp approval)"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates")
async def list_templates(
    category: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List WhatsApp templates
    """
    try:
        where_clauses = []
        params = {}
        
        if category:
            where_clauses.append("category = :category")
            params["category"] = category
        
        if status:
            where_clauses.append("status = :status")
            params["status"] = status
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
            SELECT 
                id, name, description, content, category,
                variables, language, status, usage_count
            FROM whatsapp_templates
            WHERE {where_clause}
            ORDER BY created_at DESC
        """
        
        result = db.execute(query, params)
        
        import json
        
        templates = []
        for row in result:
            templates.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "content": row[3],
                "category": row[4],
                "variables": json.loads(row[5]) if row[5] else [],
                "language": row[6],
                "status": row[7],
                "usage_count": row[8]
            })
        
        return {
            "success": True,
            "templates": templates
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS: Statistics
# ============================================================================

@router.get("/stats")
async def get_whatsapp_stats(
    firma_id: str = Query(...),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get WhatsApp statistics
    """
    try:
        where_clauses = ["firma_id = :firma_id", "direction = 'outbound'"]
        params = {"firma_id": firma_id}
        
        if start_date:
            where_clauses.append("created_at >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            where_clauses.append("created_at <= :end_date")
            params["end_date"] = end_date
        
        where_clause = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                message_type,
                status,
                COUNT(*) as count,
                DATE(created_at) as date
            FROM whatsapp_messages
            WHERE {where_clause}
            GROUP BY message_type, status, DATE(created_at)
            ORDER BY date DESC
        """
        
        result = db.execute(query, params)
        
        stats = {}
        for row in result:
            msg_type = row[0]
            status = row[1]
            count = row[2]
            date_str = row[3].isoformat() if row[3] else None
            
            if date_str not in stats:
                stats[date_str] = {}
            if msg_type not in stats[date_str]:
                stats[date_str][msg_type] = {}
            stats[date_str][msg_type][status] = count
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
