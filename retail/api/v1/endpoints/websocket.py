"""
RetailOS - WebSocket Endpoints
Realtime senkronizasyon endpoint'leri
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import logging

from retail.realtime.websocket_manager import manager, sync_manager, handle_merkez_veri_gonder, handle_merkez_veri_al

router = APIRouter()
logger = logging.getLogger(__name__)


# ========================================
# MODELS
# ========================================

class VeriGonderRequest(BaseModel):
    firma_id: int
    magaza_ids: Optional[List[int]] = None  # None = tÃ¼m maÄŸazalar
    data_type: str  # urun, musteri, kampanya, fiyat, vb.
    data: dict


class VeriAlRequest(BaseModel):
    firma_id: int
    magaza_ids: Optional[List[int]] = None
    data_type: str


# ========================================
# WEBSOCKET ENDPOINTS
# ========================================

@router.websocket("/ws/magaza/{magaza_id}")
async def websocket_magaza_endpoint(
    websocket: WebSocket,
    magaza_id: int,
    firma_id: int
):
    """
    MaÄŸaza WebSocket baÄŸlantÄ±sÄ±
    
    Usage (JavaScript):
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/magaza/2?firma_id=1');
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === 'data_sync') {
            // Veri gÃ¼ncelle
            updateLocalData(message.data_type, message.data);
        }
    };
    
    ws.send(JSON.stringify({
        type: 'pong',
        magaza_id: 2,
        timestamp: new Date().toISOString()
    }));
    ```
    """
    await manager.connect(websocket, magaza_id, firma_id, is_merkez=False)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Mesaj tipine gÃ¶re iÅŸle
            if data.get("type") == "pong":
                # Heartbeat cevabÄ±
                manager.connection_info[magaza_id]["last_ping"] = data.get("timestamp")
                logger.debug(f"Pong alÄ±ndÄ±: MaÄŸaza {magaza_id}")
                
            elif data.get("type") == "data_sync" and data.get("action") == "sube_to_merkez":
                # Åubeden merkeze veri
                await sync_manager.sube_to_merkez_sync(
                    magaza_id=magaza_id,
                    firma_id=firma_id,
                    data_type=data.get("data_type"),
                    data=data.get("data")
                )
                
            elif data.get("type") == "status_update":
                # Durum gÃ¼ncellemesi
                logger.info(f"Durum gÃ¼ncelleme: MaÄŸaza {magaza_id} - {data.get('message')}")
                
    except WebSocketDisconnect:
        manager.disconnect(magaza_id)
        logger.info(f"MaÄŸaza {magaza_id} baÄŸlantÄ±sÄ± kesildi")
    except Exception as e:
        logger.error(f"WebSocket hatasÄ± (MaÄŸaza {magaza_id}): {str(e)}")
        manager.disconnect(magaza_id)


@router.websocket("/ws/merkez/{firma_id}")
async def websocket_merkez_endpoint(
    websocket: WebSocket,
    firma_id: int
):
    """
    Merkez WebSocket baÄŸlantÄ±sÄ±
    
    Usage (JavaScript):
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/ws/merkez/1');
    
    ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (message.type === 'data_sync' && message.action === 'sube_to_merkez') {
            // Åubeden gelen veri
            console.log('Veri alÄ±ndÄ±:', message.data_type, message.data);
        }
    };
    ```
    """
    # Merkez iÃ§in magaza_id = 0 kullan
    await manager.connect(websocket, 0, firma_id, is_merkez=True)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "pong":
                logger.debug(f"Pong alÄ±ndÄ±: Merkez {firma_id}")
                
    except WebSocketDisconnect:
        logger.info(f"Merkez {firma_id} baÄŸlantÄ±sÄ± kesildi")
    except Exception as e:
        logger.error(f"WebSocket hatasÄ± (Merkez {firma_id}): {str(e)}")


# ========================================
# HTTP ENDPOINTS (WebSocket KontrolÃ¼)
# ========================================

@router.post("/veri-gonder")
async def veri_gonder(request: VeriGonderRequest):
    """
    Merkezden ÅŸubelere veri gÃ¶nder
    
    POST /api/v1/ws/veri-gonder
    {
        "firma_id": 1,
        "magaza_ids": [2, 3, 4],  // null = tÃ¼m maÄŸazalar
        "data_type": "urun",
        "data": {
            "urun_id": 123,
            "urun_adi": "Test ÃœrÃ¼n",
            "fiyat": 100.00
        }
    }
    """
    result = await handle_merkez_veri_gonder(
        firma_id=request.firma_id,
        magaza_ids=request.magaza_ids,
        data_type=request.data_type,
        data=request.data
    )
    
    return {
        "status": "success",
        "message": f"{result['success_count']} maÄŸazaya veri gÃ¶nderildi",
        "details": result
    }


@router.post("/veri-al")
async def veri_al(request: VeriAlRequest):
    """
    Åubelerden veri talep et
    
    POST /api/v1/ws/veri-al
    {
        "firma_id": 1,
        "magaza_ids": [2, 3],  // null = tÃ¼m maÄŸazalar
        "data_type": "gunluk_satis"
    }
    """
    result = await handle_merkez_veri_al(
        firma_id=request.firma_id,
        magaza_ids=request.magaza_ids,
        data_type=request.data_type
    )
    
    return {
        "status": "success",
        "message": "Veri talebi gÃ¶nderildi",
        "details": result
    }


@router.get("/baglantilar/{firma_id}")
async def get_baglantilar(firma_id: int):
    """
    Firmaya ait aktif baÄŸlantÄ±larÄ± listele
    
    GET /api/v1/ws/baglantilar/1
    """
    magazalar = manager.get_connected_magazalar(firma_id)
    
    baglanti_detaylari = []
    for magaza_id in magazalar:
        info = manager.connection_info.get(magaza_id, {})
        baglanti_detaylari.append({
            "magaza_id": magaza_id,
            "connected_at": info.get("connected_at"),
            "last_ping": info.get("last_ping"),
            "is_online": manager.is_magaza_online(magaza_id)
        })
    
    return {
        "firma_id": firma_id,
        "toplam_baglanti": len(magazalar),
        "baglantilar": baglanti_detaylari
    }


@router.get("/magaza-durum/{magaza_id}")
async def get_magaza_durum(magaza_id: int):
    """
    MaÄŸaza durumunu kontrol et
    
    GET /api/v1/ws/magaza-durum/2
    """
    is_online = manager.is_magaza_online(magaza_id)
    info = manager.connection_info.get(magaza_id, {})
    
    return {
        "magaza_id": magaza_id,
        "is_online": is_online,
        "connection_info": info if is_online else None
    }


@router.post("/test-mesaj")
async def test_mesaj(magaza_id: int, mesaj: str):
    """
    Test mesajÄ± gÃ¶nder
    
    POST /api/v1/ws/test-mesaj?magaza_id=2&mesaj=Test
    """
    message = {
        "type": "test",
        "message": mesaj,
        "timestamp": "2024-12-10T15:00:00"
    }
    
    result = await manager.send_to_magaza(magaza_id, message)
    
    return {
        "success": result,
        "message": "Mesaj gÃ¶nderildi" if result else "MaÄŸaza offline"
    }

