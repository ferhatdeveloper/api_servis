"""
Notifications API Endpoints
Multi-channel notification system

@created: 2024-12-18
@author: ExRetailOS Team
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel

from app.core.async_database import get_db

router = APIRouter()


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class NotificationCreate(BaseModel):
    type: str  # info, success, warning, error
    channel: str  # push, email, sms, in-app
    title: str
    message: str
    user_id: Optional[str] = None
    customer_id: Optional[str] = None
    role_id: Optional[str] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    metadata: Optional[dict] = None


class NotificationResponse(BaseModel):
    id: int
    type: str
    channel: str
    title: str
    message: str
    status: str
    read_at: Optional[datetime] = None
    action_url: Optional[str] = None
    action_label: Optional[str] = None
    created_at: datetime


class NotificationPreferences(BaseModel):
    push_enabled: bool = True
    email_enabled: bool = True
    sms_enabled: bool = False
    in_app_enabled: bool = True
    categories: dict = {
        "sales": True,
        "stock": True,
        "finance": True,
        "system": True,
        "marketing": False
    }
    email_address: Optional[str] = None
    phone_number: Optional[str] = None


# ============================================================================
# ENDPOINTS: Notifications
# ============================================================================

@router.post("/send")
async def send_notification(
    notification: NotificationCreate,
    db: Session = Depends(get_db)
):
    """
    Send a notification
    """
    try:
        query = """
            INSERT INTO notifications (
                type, channel, title, message,
                user_id, customer_id, role_id,
                action_url, action_label, metadata,
                status, created_at
            ) VALUES (
                :type, :channel, :title, :message,
                :user_id, :customer_id, :role_id,
                :action_url, :action_label, :metadata,
                'pending', NOW()
            )
            RETURNING id
        """
        
        import json
        
        result = db.execute(query, {
            "type": notification.type,
            "channel": notification.channel,
            "title": notification.title,
            "message": notification.message,
            "user_id": notification.user_id,
            "customer_id": notification.customer_id,
            "role_id": notification.role_id,
            "action_url": notification.action_url,
            "action_label": notification.action_label,
            "metadata": json.dumps(notification.metadata) if notification.metadata else None
        })
        
        notification_id = result.fetchone()[0]
        db.commit()
        
        # TODO: Trigger actual notification (push, email, sms)
        # await send_push_notification(notification_id)
        # await send_email_notification(notification_id)
        # await send_sms_notification(notification_id)
        
        return {
            "success": True,
            "notification_id": notification_id,
            "message": "Notification sent successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_notifications(
    user_id: str = Query(...),
    status: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db)
):
    """
    List notifications for a user
    """
    try:
        where_clauses = ["user_id = :user_id"]
        params = {"user_id": user_id}
        
        if status:
            where_clauses.append("status = :status")
            params["status"] = status
        
        if type:
            where_clauses.append("type = :type")
            params["type"] = type
        
        where_clause = " AND ".join(where_clauses)
        
        query = f"""
            SELECT 
                id, type, channel, title, message, status,
                read_at, action_url, action_label, created_at
            FROM notifications
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        
        params["limit"] = limit
        params["offset"] = offset
        
        result = db.execute(query, params)
        
        notifications = []
        for row in result:
            notifications.append({
                "id": row[0],
                "type": row[1],
                "channel": row[2],
                "title": row[3],
                "message": row[4],
                "status": row[5],
                "read_at": row[6].isoformat() if row[6] else None,
                "action_url": row[7],
                "action_label": row[8],
                "created_at": row[9].isoformat() if row[9] else None
            })
        
        # Get unread count
        count_query = """
            SELECT COUNT(*)
            FROM notifications
            WHERE user_id = :user_id AND status != 'read'
        """
        
        unread_count = db.execute(count_query, {"user_id": user_id}).fetchone()[0]
        
        return {
            "success": True,
            "notifications": notifications,
            "unread_count": unread_count,
            "total": len(notifications)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{notification_id}/mark-read")
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """
    Mark notification as read
    """
    try:
        query = """
            UPDATE notifications
            SET status = 'read',
                read_at = NOW()
            WHERE id = :notification_id
              AND status != 'read'
        """
        
        db.execute(query, {"notification_id": notification_id})
        db.commit()
        
        return {
            "success": True,
            "message": "Notification marked as read"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-all-read")
async def mark_all_read(
    user_id: str = Query(...),
    db: Session = Depends(get_db)
):
    """
    Mark all notifications as read for a user
    """
    try:
        query = """
            UPDATE notifications
            SET status = 'read',
                read_at = NOW()
            WHERE user_id = :user_id
              AND status != 'read'
        """
        
        result = db.execute(query, {"user_id": user_id})
        db.commit()
        
        return {
            "success": True,
            "marked_count": result.rowcount
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a notification
    """
    try:
        query = "DELETE FROM notifications WHERE id = :notification_id"
        db.execute(query, {"notification_id": notification_id})
        db.commit()
        
        return {
            "success": True,
            "message": "Notification deleted"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS: Preferences
# ============================================================================

@router.get("/preferences/{user_id}")
async def get_preferences(
    user_id: str,
    db: Session = Depends(get_db)
):
    """
    Get notification preferences for a user
    """
    try:
        query = """
            SELECT 
                push_enabled, email_enabled, sms_enabled, in_app_enabled,
                categories, email_address, phone_number
            FROM notification_preferences
            WHERE user_id = :user_id
        """
        
        result = db.execute(query, {"user_id": user_id}).fetchone()
        
        if not result:
            # Return defaults
            return {
                "success": True,
                "preferences": {
                    "push_enabled": True,
                    "email_enabled": True,
                    "sms_enabled": False,
                    "in_app_enabled": True,
                    "categories": {
                        "sales": True,
                        "stock": True,
                        "finance": True,
                        "system": True,
                        "marketing": False
                    },
                    "email_address": None,
                    "phone_number": None
                }
            }
        
        import json
        
        return {
            "success": True,
            "preferences": {
                "push_enabled": result[0],
                "email_enabled": result[1],
                "sms_enabled": result[2],
                "in_app_enabled": result[3],
                "categories": json.loads(result[4]) if result[4] else {},
                "email_address": result[5],
                "phone_number": result[6]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/preferences/{user_id}")
async def update_preferences(
    user_id: str,
    preferences: NotificationPreferences,
    db: Session = Depends(get_db)
):
    """
    Update notification preferences
    """
    try:
        import json
        
        # Check if preferences exist
        check_query = "SELECT id FROM notification_preferences WHERE user_id = :user_id"
        existing = db.execute(check_query, {"user_id": user_id}).fetchone()
        
        if existing:
            # Update
            query = """
                UPDATE notification_preferences
                SET push_enabled = :push_enabled,
                    email_enabled = :email_enabled,
                    sms_enabled = :sms_enabled,
                    in_app_enabled = :in_app_enabled,
                    categories = :categories,
                    email_address = :email_address,
                    phone_number = :phone_number,
                    updated_at = NOW()
                WHERE user_id = :user_id
            """
        else:
            # Insert
            query = """
                INSERT INTO notification_preferences (
                    user_id, push_enabled, email_enabled, sms_enabled, in_app_enabled,
                    categories, email_address, phone_number
                ) VALUES (
                    :user_id, :push_enabled, :email_enabled, :sms_enabled, :in_app_enabled,
                    :categories, :email_address, :phone_number
                )
            """
        
        db.execute(query, {
            "user_id": user_id,
            "push_enabled": preferences.push_enabled,
            "email_enabled": preferences.email_enabled,
            "sms_enabled": preferences.sms_enabled,
            "in_app_enabled": preferences.in_app_enabled,
            "categories": json.dumps(preferences.categories),
            "email_address": preferences.email_address,
            "phone_number": preferences.phone_number
        })
        
        db.commit()
        
        return {
            "success": True,
            "message": "Preferences updated successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ENDPOINTS: Statistics
# ============================================================================

@router.get("/stats")
async def get_notification_stats(
    user_id: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    """
    Get notification statistics
    """
    try:
        where_clauses = []
        params = {}
        
        if user_id:
            where_clauses.append("user_id = :user_id")
            params["user_id"] = user_id
        
        if start_date:
            where_clauses.append("created_at >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            where_clauses.append("created_at <= :end_date")
            params["end_date"] = end_date
        
        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        query = f"""
            SELECT 
                channel,
                type,
                status,
                COUNT(*) as count
            FROM notifications
            WHERE {where_clause}
            GROUP BY channel, type, status
        """
        
        result = db.execute(query, params)
        
        stats = {}
        for row in result:
            channel = row[0]
            type_val = row[1]
            status = row[2]
            count = row[3]
            
            if channel not in stats:
                stats[channel] = {}
            if type_val not in stats[channel]:
                stats[channel][type_val] = {}
            stats[channel][type_val][status] = count
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
