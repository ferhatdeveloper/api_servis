from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from pydantic import BaseModel
from app.services.whatsapp_service import WhatsAppService

router = APIRouter()
whatsapp_service = WhatsAppService()

class GroupCreate(BaseModel):
    name: str
    participants: List[str]

@router.get("/list")
async def list_groups():
    """Fetch all joined groups"""
    return whatsapp_service.fetch_groups()

@router.post("/create")
async def create_group(payload: GroupCreate):
    """Create a new WhatsApp group"""
    return whatsapp_service.create_group(payload.name, payload.participants)

@router.get("/{group_jid}")
async def get_group_info(group_jid: str):
    """Get group details and members"""
    return whatsapp_service.get_group_info(group_jid)
