"""
RetailOS - Menu Seed Endpoint
Mevcut statik menÃ¼ yapÄ±sÄ±nÄ± veritabanÄ±na aktarÄ±r
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx

from app.core.async_database import get_db
from app.core.config import settings
from app.models.retail.menu import MenuItem

router = APIRouter(prefix="/menu", tags=["menu"])


@router.post("/seed", status_code=200)
async def seed_menu_structure(
    menu_structure: List[Dict[str, Any]],
    db: Optional[AsyncSession] = Depends(get_db)
):
    """
    Mevcut statik menÃ¼ yapÄ±sÄ±nÄ± veritabanÄ±na aktarÄ±r
    Supabase REST API veya SQLAlchemy kullanÄ±r
    """
    # Ã–nce Supabase REST API ile dene
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
        try:
            return await seed_via_supabase_api(menu_structure)
        except Exception as e:
            # Supabase API baÅŸarÄ±sÄ±z olursa SQLAlchemy'ye geÃ§
            if db is None:
                raise HTTPException(
                    status_code=503,
                    detail=f"Database connection failed. Supabase API error: {str(e)}"
                )
    
    # SQLAlchemy ile devam et
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="Database not configured. Please set DATABASE_URL or SUPABASE credentials."
        )
    
    try:
        # Ã–nce mevcut menÃ¼ Ã¶ÄŸelerini kontrol et
        result = await db.execute(select(MenuItem))
        existing_items = result.scalars().all()
        
        if existing_items:
            return {
                "success": False,
                "message": "MenÃ¼ yapÄ±sÄ± zaten mevcut. Ã–nce mevcut menÃ¼yÃ¼ silin.",
                "count": len(existing_items)
            }
        
        created_items = []
        item_id_map = {}  # GeÃ§ici ID'lerden gerÃ§ek ID'lere mapping
        
        async def create_menu_item(
            item_data: Dict[str, Any],
            parent_id: int = None,
            section_id: int = None,
            order: int = 0
        ) -> int:
            """Recursive olarak menÃ¼ Ã¶ÄŸesi oluÅŸtur"""
            menu_type = item_data.get('menu_type', 'main')
            if 'title' in item_data and not parent_id:
                menu_type = 'section'
            
            # Icon adÄ±nÄ± al
            icon_name = None
            if 'icon_name' in item_data:
                icon_name = item_data['icon_name']
            elif 'icon' in item_data and item_data['icon']:
                # Lucide icon component'inden isim Ã§Ä±kar
                icon_name = getattr(item_data['icon'], 'name', None) or str(item_data['icon'])
            
            new_item = MenuItem(
                menu_type=menu_type,
                title=item_data.get('title'),
                label=item_data.get('label', ''),
                label_tr=item_data.get('label', ''),
                parent_id=parent_id,
                section_id=section_id,
                screen_id=item_data.get('screen_id') or item_data.get('id'),
                icon_name=icon_name,
                badge=item_data.get('badge'),
                display_order=order,
                is_active=True,
                is_visible=True
            )
            
            db.add(new_item)
            await db.flush()  # ID'yi almak iÃ§in flush
            await db.refresh(new_item)
            
            created_items.append(new_item.id)
            item_id_map[item_data.get('id')] = new_item.id
            
            # Children varsa recursive oluÅŸtur
            if 'children' in item_data and item_data['children']:
                current_section_id = section_id if menu_type != 'section' else new_item.id
                for idx, child in enumerate(item_data['children']):
                    await create_menu_item(
                        child,
                        parent_id=new_item.id if menu_type != 'section' else None,
                        section_id=current_section_id,
                        order=idx
                    )
            
            return new_item.id
        
        # TÃ¼m section'larÄ± oluÅŸtur
        for section_idx, section in enumerate(menu_structure):
            await create_menu_item(
                {
                    'menu_type': 'section',
                    'title': section.get('title', ''),
                    'label': section.get('title', ''),
                    'id': f"section_{section_idx}",
                    'children': section.get('items', [])
                },
                order=section_idx
            )
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"{len(created_items)} menÃ¼ Ã¶ÄŸesi oluÅŸturuldu",
            "count": len(created_items)
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

