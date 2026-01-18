"""
Realtime WebSocket endpoint
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import asyncio

router = APIRouter(prefix="/realtime", tags=["Realtime"])


class ConnectionManager:
    """WebSocket bağlantı yöneticisi"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Yeni bağlantıyı kabul et"""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Bağlantıyı kapat"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Tüm bağlı istemcilere mesaj gönder"""
        if self.active_connections:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(connection)
            
            # Kopan bağlantıları temizle
            for conn in disconnected:
                self.disconnect(conn)


manager = ConnectionManager()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint"""
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # Mesajı işle
            try:
                message = json.loads(data)
                
                # Broadcast et
                response = {
                    "type": "message",
                    "data": message,
                    "timestamp": asyncio.get_event_loop().time()
                }
                
                await manager.broadcast(response)
                
            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "message": "Geçersiz JSON formatı"
                }
                await websocket.send_json(error_response)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"İstemci bağlantısı kesildi: {websocket}")


@router.post("/broadcast")
async def broadcast_message(message: dict):
    """Yeni mesaj yayınla"""
    await manager.broadcast({
        "type": "broadcast",
        "data": message,
        "timestamp": asyncio.get_event_loop().time()
    })
    
    return {
        "status": "success",
        "message": "Mesaj yayınlandı",
        "connections": len(manager.active_connections)
    }


@router.get("/connections")
async def get_connections():
    """Aktif bağlantı sayısını al"""
    return {
        "active_connections": len(manager.active_connections)
    }
