"""
RetailOS - WebSocket Manager
Merkez <-> Åube Realtime Senkronizasyon
Public IP gerektirmez, merkez server Ã¼zerinden WebSocket baÄŸlantÄ±sÄ±
"""

from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket baÄŸlantÄ± yÃ¶neticisi"""
    
    def __init__(self):
        # Aktif baÄŸlantÄ±lar: {magaza_id: WebSocket}
        self.active_connections: Dict[int, WebSocket] = {}
        
        # Merkez baÄŸlantÄ±larÄ±: {firma_id: WebSocket}
        self.merkez_connections: Dict[int, WebSocket] = {}
        
        # BaÄŸlantÄ± bilgileri
        self.connection_info: Dict[int, dict] = {}
        
    async def connect(self, websocket: WebSocket, magaza_id: int, firma_id: int, is_merkez: bool = False):
        """Yeni baÄŸlantÄ± kabul et"""
        await websocket.accept()
        
        if is_merkez:
            self.merkez_connections[firma_id] = websocket
            logger.info(f"Merkez baÄŸlandÄ±: Firma {firma_id}")
        else:
            self.active_connections[magaza_id] = websocket
            logger.info(f"MaÄŸaza baÄŸlandÄ±: MaÄŸaza {magaza_id}")
        
        # BaÄŸlantÄ± bilgilerini kaydet
        self.connection_info[magaza_id] = {
            "firma_id": firma_id,
            "magaza_id": magaza_id,
            "is_merkez": is_merkez,
            "connected_at": datetime.now().isoformat(),
            "last_ping": datetime.now().isoformat()
        }
        
    def disconnect(self, magaza_id: int):
        """BaÄŸlantÄ±yÄ± kapat"""
        if magaza_id in self.active_connections:
            del self.active_connections[magaza_id]
            logger.info(f"MaÄŸaza baÄŸlantÄ±sÄ± kesildi: {magaza_id}")
            
        if magaza_id in self.connection_info:
            del self.connection_info[magaza_id]
    
    async def send_to_magaza(self, magaza_id: int, message: dict):
        """Belirli bir maÄŸazaya mesaj gÃ¶nder"""
        if magaza_id in self.active_connections:
            try:
                await self.active_connections[magaza_id].send_json(message)
                logger.debug(f"Mesaj gÃ¶nderildi -> MaÄŸaza {magaza_id}")
                return True
            except Exception as e:
                logger.error(f"Mesaj gÃ¶nderim hatasÄ± (MaÄŸaza {magaza_id}): {str(e)}")
                self.disconnect(magaza_id)
                return False
        else:
            logger.warning(f"MaÄŸaza {magaza_id} baÄŸlÄ± deÄŸil!")
            return False
    
    async def send_to_merkez(self, firma_id: int, message: dict):
        """Merkeze mesaj gÃ¶nder"""
        if firma_id in self.merkez_connections:
            try:
                await self.merkez_connections[firma_id].send_json(message)
                logger.debug(f"Mesaj gÃ¶nderildi -> Merkez {firma_id}")
                return True
            except Exception as e:
                logger.error(f"Mesaj gÃ¶nderim hatasÄ± (Merkez {firma_id}): {str(e)}")
                return False
        return False
    
    async def broadcast_to_firma(self, firma_id: int, message: dict, exclude_magaza: int = None):
        """Firmaya ait tÃ¼m maÄŸazalara broadcast"""
        sent_count = 0
        for magaza_id, websocket in self.active_connections.items():
            if exclude_magaza and magaza_id == exclude_magaza:
                continue
                
            info = self.connection_info.get(magaza_id, {})
            if info.get("firma_id") == firma_id:
                try:
                    await websocket.send_json(message)
                    sent_count += 1
                except Exception as e:
                    logger.error(f"Broadcast hatasÄ± (MaÄŸaza {magaza_id}): {str(e)}")
                    
        logger.info(f"Broadcast: {sent_count} maÄŸazaya mesaj gÃ¶nderildi (Firma {firma_id})")
        return sent_count
    
    def get_connected_magazalar(self, firma_id: int) -> List[int]:
        """Firmaya ait baÄŸlÄ± maÄŸazalarÄ± getir"""
        magazalar = []
        for magaza_id, info in self.connection_info.items():
            if info.get("firma_id") == firma_id and not info.get("is_merkez"):
                magazalar.append(magaza_id)
        return magazalar
    
    def is_magaza_online(self, magaza_id: int) -> bool:
        """MaÄŸaza online mÄ±?"""
        return magaza_id in self.active_connections


# Global singleton instance
manager = ConnectionManager()


class DataSyncManager:
    """Veri senkronizasyon yÃ¶neticisi"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.conn_manager = connection_manager
        
    async def merkez_to_sube_sync(self, firma_id: int, magaza_ids: List[int], data_type: str, data: dict):
        """
        Merkezden ÅŸubeye veri gÃ¶nder
        
        Args:
            firma_id: Firma ID
            magaza_ids: Hedef maÄŸaza ID listesi (None = tÃ¼m maÄŸazalar)
            data_type: Veri tipi (urun, musteri, kampanya, vb.)
            data: GÃ¶nderilecek veri
        """
        message = {
            "type": "data_sync",
            "action": "merkez_to_sube",
            "data_type": data_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "firma_id": firma_id
        }
        
        if magaza_ids is None:
            # TÃ¼m maÄŸazalara gÃ¶nder
            magaza_ids = self.conn_manager.get_connected_magazalar(firma_id)
        
        success_count = 0
        failed_magazalar = []
        
        for magaza_id in magaza_ids:
            result = await self.conn_manager.send_to_magaza(magaza_id, message)
            if result:
                success_count += 1
            else:
                failed_magazalar.append(magaza_id)
        
        return {
            "success_count": success_count,
            "failed_magazalar": failed_magazalar,
            "total_sent": len(magaza_ids)
        }
    
    async def sube_to_merkez_sync(self, magaza_id: int, firma_id: int, data_type: str, data: dict):
        """
        Åubeden merkeze veri gÃ¶nder
        
        Args:
            magaza_id: MaÄŸaza ID
            firma_id: Firma ID
            data_type: Veri tipi
            data: GÃ¶nderilecek veri
        """
        message = {
            "type": "data_sync",
            "action": "sube_to_merkez",
            "data_type": data_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "magaza_id": magaza_id,
            "firma_id": firma_id
        }
        
        result = await self.conn_manager.send_to_merkez(firma_id, message)
        
        return {
            "success": result,
            "message": "Merkeze veri gÃ¶nderildi" if result else "Merkez baÄŸlÄ± deÄŸil"
        }
    
    async def bidirectional_sync(self, firma_id: int, magaza_ids: List[int], data_type: str):
        """
        Ä°ki yÃ¶nlÃ¼ senkronizasyon
        Hem merkez -> ÅŸube, hem ÅŸube -> merkez
        """
        # TODO: Database'den verileri Ã§ek ve senkronize et
        pass


# Global sync manager
sync_manager = DataSyncManager(manager)


async def handle_merkez_veri_gonder(firma_id: int, magaza_ids: List[int], data_type: str, data: dict):
    """
    Merkez Dashboard'dan 'Veri GÃ¶nder' butonuna basÄ±ldÄ±ÄŸÄ±nda
    
    Args:
        firma_id: Firma ID
        magaza_ids: Hedef maÄŸaza ID'leri (None = hepsi)
        data_type: urun, musteri, kampanya, fiyat, vb.
        data: GÃ¶nderilecek veri paketi
    """
    logger.info(f"Merkez veri gÃ¶nder: {data_type} -> MaÄŸazalar: {magaza_ids}")
    
    result = await sync_manager.merkez_to_sube_sync(
        firma_id=firma_id,
        magaza_ids=magaza_ids,
        data_type=data_type,
        data=data
    )
    
    # Log veritabanÄ±na kaydet
    # TODO: SenkronizasyonLoglari tablosuna INSERT
    
    return result


async def handle_merkez_veri_al(firma_id: int, magaza_ids: List[int], data_type: str):
    """
    Merkez Dashboard'dan 'Veri Al' butonuna basÄ±ldÄ±ÄŸÄ±nda
    
    MaÄŸazalardan veri talep eder, maÄŸazalar cevap verir
    """
    logger.info(f"Merkez veri al: {data_type} <- MaÄŸazalar: {magaza_ids}")
    
    request_message = {
        "type": "data_request",
        "action": "merkez_veri_al",
        "data_type": data_type,
        "timestamp": datetime.now().isoformat(),
        "request_id": f"{firma_id}_{datetime.now().timestamp()}"
    }
    
    if magaza_ids is None:
        magaza_ids = manager.get_connected_magazalar(firma_id)
    
    responses = []
    for magaza_id in magaza_ids:
        await manager.send_to_magaza(magaza_id, request_message)
        # MaÄŸazalar veriyi sube_to_merkez_sync ile gÃ¶nderecek
    
    return {
        "request_sent_to": magaza_ids,
        "message": "Veri talebi gÃ¶nderildi, maÄŸazalar cevap verecek"
    }


async def heartbeat_checker():
    """
    Periyodik olarak baÄŸlÄ± maÄŸazalara ping gÃ¶nder
    Cevap vermeyenleri disconnect et
    """
    while True:
        await asyncio.sleep(30)  # 30 saniyede bir
        
        ping_message = {
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        }
        
        for magaza_id, websocket in list(manager.active_connections.items()):
            try:
                await websocket.send_json(ping_message)
                manager.connection_info[magaza_id]["last_ping"] = datetime.now().isoformat()
            except Exception as e:
                logger.warning(f"Heartbeat failed for MaÄŸaza {magaza_id}, disconnecting...")
                manager.disconnect(magaza_id)


# Ã–rnek mesaj formatlarÄ±:

"""
MERKEZ -> ÅUBE (ÃœrÃ¼n GÃ¼ncelleme):
{
    "type": "data_sync",
    "action": "merkez_to_sube",
    "data_type": "urun",
    "data": {
        "urun_id": 123,
        "urun_adi": "Coca Cola 330ml",
        "fiyat": 15.00,
        "stok": 100
    },
    "timestamp": "2024-12-10T15:30:00",
    "firma_id": 1
}

ÅUBE -> MERKEZ (SatÄ±ÅŸ Raporu):
{
    "type": "data_sync",
    "action": "sube_to_merkez",
    "data_type": "satis",
    "data": {
        "satis_id": 456,
        "magaza_id": 2,
        "tutar": 1500.00,
        "tarih": "2024-12-10"
    },
    "timestamp": "2024-12-10T16:00:00",
    "magaza_id": 2,
    "firma_id": 1
}

MERKEZ -> ÅUBE (Veri Talebi):
{
    "type": "data_request",
    "action": "merkez_veri_al",
    "data_type": "gunluk_satis",
    "timestamp": "2024-12-10T17:00:00",
    "request_id": "1_1702224000"
}

HEARTBEAT:
{
    "type": "ping",
    "timestamp": "2024-12-10T17:05:00"
}

PONG (Cevap):
{
    "type": "pong",
    "magaza_id": 2,
    "timestamp": "2024-12-10T17:05:01"
}
"""

