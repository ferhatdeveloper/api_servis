"""
RetailOS - Menu Management Endpoints
MenÃ¼ yÃ¶netimi API endpoint'leri
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

from retail.core.database import get_db
from retail.models.menu import MenuItem

router = APIRouter(prefix="/menu", tags=["menu"])


# Pydantic Models
class MenuItemBase(BaseModel):
    menu_type: str  # 'section', 'main', 'sub'
    title: Optional[str] = None
    label: str
    label_tr: Optional[str] = None
    label_en: Optional[str] = None
    label_ar: Optional[str] = None
    parent_id: Optional[int] = None
    section_id: Optional[int] = None
    screen_id: Optional[str] = None
    icon_name: Optional[str] = None
    badge: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    is_visible: bool = True
    notes: Optional[str] = None


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    title: Optional[str] = None
    label: Optional[str] = None
    label_tr: Optional[str] = None
    label_en: Optional[str] = None
    label_ar: Optional[str] = None
    parent_id: Optional[int] = None
    section_id: Optional[int] = None
    screen_id: Optional[str] = None
    icon_name: Optional[str] = None
    badge: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    is_visible: Optional[bool] = None
    notes: Optional[str] = None


class MenuItemResponse(MenuItemBase):
    id: int
    created_by: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class MenuOrderUpdate(BaseModel):
    items: List[dict]  # [{id: int, display_order: int, parent_id: Optional[int]}]


@router.get("/", response_model=List[MenuItemResponse])
async def get_menu_items(
    db: AsyncSession = Depends(get_db),
    active_only: bool = True
):
    """TÃ¼m menÃ¼ Ã¶ÄŸelerini getir"""
    query = select(MenuItem)
    
    if active_only:
        query = query.where(MenuItem.is_active == True)
    
    query = query.order_by(MenuItem.display_order)
    
    result = await db.execute(query)
    items = result.scalars().all()
    return items


@router.get("/tree", response_model=List[dict])
async def get_menu_tree(
    db: AsyncSession = Depends(get_db),
    active_only: bool = True
):
    """MenÃ¼ yapÄ±sÄ±nÄ± hiyerarÅŸik olarak getir"""
    # VeritabanÄ± yapÄ±landÄ±rÄ±lmamÄ±ÅŸsa boÅŸ liste dÃ¶ndÃ¼r
    if db is None:
        return []
    
    try:
        query = select(MenuItem)
        
        if active_only:
            query = query.where(MenuItem.is_active == True)
        
        query = query.order_by(MenuItem.display_order)
        
        result = await db.execute(query)
        all_items = result.scalars().all()
    except Exception as e:
        # VeritabanÄ± baÄŸlantÄ±sÄ± hatasÄ± varsa boÅŸ liste dÃ¶ndÃ¼r
        return []
    
    # HiyerarÅŸik yapÄ± oluÅŸtur
    def build_tree(items):
        items_dict = {item.id: {
            "id": item.id,
            "menu_type": item.menu_type,
            "title": item.title,
            "label": item.label,
            "label_tr": item.label_tr,
            "label_en": item.label_en,
            "label_ar": item.label_ar,
            "parent_id": item.parent_id,
            "section_id": item.section_id,
            "screen_id": item.screen_id,
            "icon_name": item.icon_name,
            "badge": item.badge,
            "display_order": item.display_order,
            "is_active": item.is_active,
            "is_visible": item.is_visible,
            "children": []
        } for item in items}
        
        root_items = []
        for item in items:
            item_dict = items_dict[item.id]
            if item.menu_type == 'section':
                # Section'lar root'ta
                root_items.append(item_dict)
            elif item.parent_id is None:
                # Parent'Ä± olmayan item'lar root'a ekle
                root_items.append(item_dict)
            else:
                # Parent'Ä± olan item'larÄ± parent'Ä±n children'Ä±na ekle
                if item.parent_id in items_dict:
                    items_dict[item.parent_id]["children"].append(item_dict)
        
        # Section'lara gÃ¶re sÄ±rala
        root_items.sort(key=lambda x: (x.get("menu_type") != "section", x.get("display_order", 0)))
        
        return root_items
    
    return build_tree(all_items)


@router.get("/{menu_id}", response_model=MenuItemResponse)
async def get_menu_item(
    menu_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Tek bir menÃ¼ Ã¶ÄŸesini getir"""
    result = await db.execute(
        select(MenuItem).where(MenuItem.id == menu_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    return item


@router.post("/", response_model=MenuItemResponse, status_code=201)
async def create_menu_item(
    menu_item: MenuItemCreate,
    db: AsyncSession = Depends(get_db)
):
    """Yeni menÃ¼ Ã¶ÄŸesi oluÅŸtur"""
    new_item = MenuItem(**menu_item.dict())
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return new_item


@router.put("/{menu_id}", response_model=MenuItemResponse)
async def update_menu_item(
    menu_id: int,
    menu_item: MenuItemUpdate,
    db: AsyncSession = Depends(get_db)
):
    """MenÃ¼ Ã¶ÄŸesini gÃ¼ncelle"""
    result = await db.execute(
        select(MenuItem).where(MenuItem.id == menu_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    update_data = menu_item.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    await db.execute(
        update(MenuItem)
        .where(MenuItem.id == menu_id)
        .values(**update_data)
    )
    await db.commit()
    
    await db.refresh(item)
    return item


@router.delete("/{menu_id}", status_code=204)
async def delete_menu_item(
    menu_id: int,
    db: AsyncSession = Depends(get_db)
):
    """MenÃ¼ Ã¶ÄŸesini sil"""
    result = await db.execute(
        select(MenuItem).where(MenuItem.id == menu_id)
    )
    item = result.scalar_one_or_none()
    
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    await db.delete(item)
    await db.commit()
    return None


@router.post("/reorder", status_code=200)
async def reorder_menu_items(
    order_update: MenuOrderUpdate,
    db: AsyncSession = Depends(get_db)
):
    """MenÃ¼ Ã¶ÄŸelerinin sÄ±rasÄ±nÄ± gÃ¼ncelle (sÃ¼rÃ¼kle-bÄ±rak sonrasÄ±)"""
    try:
        for item_data in order_update.items:
            await db.execute(
                update(MenuItem)
                .where(MenuItem.id == item_data["id"])
                .values(
                    display_order=item_data["display_order"],
                    parent_id=item_data.get("parent_id"),
                    section_id=item_data.get("section_id"),
                    updated_at=datetime.utcnow()
                )
            )
        
        await db.commit()
        return {"success": True, "message": "Menu order updated successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


class MenuItemBulkUpdate(MenuItemUpdate):
    id: int

@router.post("/bulk-update", status_code=200)
async def bulk_update_menu_items(
    items: List[MenuItemBulkUpdate],
    db: AsyncSession = Depends(get_db)
):
    """Toplu menÃ¼ Ã¶ÄŸesi gÃ¼ncelleme"""
    try:
        for item_data in items:
            update_data = item_data.dict(exclude={'id'}, exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()
            
            await db.execute(
                update(MenuItem)
                .where(MenuItem.id == item_data.id)
                .values(**update_data)
            )
        
        await db.commit()
        return {"success": True, "message": "Menu items updated successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

