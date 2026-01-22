from fastapi import WebSocket
from typing import Dict, List, Optional
import json
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # active_connections: {magaza_id: WebSocket}
        self.active_connections: Dict[int, WebSocket] = {}
        # connection_info: {magaza_id: {"connected_at": str, "last_ping": str}}
        self.connection_info: Dict[int, dict] = {}
        # firma_map: {firma_id: [magaza_id, ...]}
        self.firma_map: Dict[int, List[int]] = {}

    async def connect(self, websocket: WebSocket, magaza_id: int, firma_id: int, is_merkez: bool = False):
        await websocket.accept()
        if not is_merkez:
            self.active_connections[magaza_id] = websocket
            self.connection_info[magaza_id] = {
                "connected_at": datetime.now().isoformat(),
                "last_ping": datetime.now().isoformat()
            }
            if firma_id not in self.firma_map:
                self.firma_map[firma_id] = []
            if magaza_id not in self.firma_map[firma_id]:
                self.firma_map[firma_id].append(magaza_id)
            logger.info(f"Magaza {magaza_id} connected (Firma: {firma_id})")

    def disconnect(self, magaza_id: int):
        if magaza_id in self.active_connections:
            del self.active_connections[magaza_id]
        if magaza_id in self.connection_info:
            del self.connection_info[magaza_id]
        # Cleanup firma map if needed, but complex to reverse map quickly without iteration
        # For stub purposes, this is fine
        logger.info(f"Magaza {magaza_id} disconnected")

    def get_connected_magazalar(self, firma_id: int) -> List[int]:
        # Filter active connections by firma
        if firma_id in self.firma_map:
            # Verify they are still active
            active = []
            for mid in self.firma_map[firma_id]:
                if mid in self.active_connections:
                    active.append(mid)
            return active
        return []

    def is_magaza_online(self, magaza_id: int) -> bool:
        return magaza_id in self.active_connections

    async def send_to_magaza(self, magaza_id: int, message: dict) -> bool:
        if magaza_id in self.active_connections:
            try:
                await self.active_connections[magaza_id].send_json(message)
                return True
            except Exception as e:
                logger.error(f"Error sending to {magaza_id}: {e}")
                self.disconnect(magaza_id)
                return False
        return False

manager = ConnectionManager()

class SyncManager:
    async def sube_to_merkez_sync(self, magaza_id: int, firma_id: int, data_type: str, data: dict):
        logger.info(f"Sync received from Magaza {magaza_id}: {data_type}")
        # Placeholder for actual sync logic (saving to DB, etc.)
        pass

sync_manager = SyncManager()

async def handle_merkez_veri_gonder(firma_id: int, magaza_ids: Optional[List[int]], data_type: str, data: dict):
    targets = magaza_ids if magaza_ids else manager.get_connected_magazalar(firma_id)
    success_count = 0
    
    payload = {
        "type": "data_sync",
        "action": "merkez_to_sube",
        "data_type": data_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }

    for mid in targets:
        if await manager.send_to_magaza(mid, payload):
            success_count += 1
            
    return {"success_count": success_count, "total_targets": len(targets)}

async def handle_merkez_veri_al(firma_id: int, magaza_ids: Optional[List[int]], data_type: str):
    targets = magaza_ids if magaza_ids else manager.get_connected_magazalar(firma_id)
    success_count = 0
    
    payload = {
        "type": "data_request",
        "data_type": data_type,
        "timestamp": datetime.now().isoformat()
    }

    for mid in targets:
        if await manager.send_to_magaza(mid, payload):
            success_count += 1
            
    return {"success_count": success_count, "total_targets": len(targets)}
