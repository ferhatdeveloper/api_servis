"""
ExRetailOS VPN Manager API Endpoints
FastAPI routes for VPN management
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

try:
    from app.services.retail.vpn_manager import VPNManager
except ImportError:
    # Fallback for testing
    VPNManager = None

router = APIRouter(prefix="/vpn", tags=["VPN Manager"])

# Global VPN Manager instance
vpn_manager = None

def get_vpn_manager():
    """Get or create VPN Manager instance"""
    global vpn_manager
    if vpn_manager is None and VPNManager is not None:
        vpn_manager = VPNManager()
        vpn_manager.initialize_server()
    return vpn_manager


# Pydantic Models
class VPNClientCreate(BaseModel):
    name: str
    type: str = "store"  # store, fieldsales, warehouse, central
    location: Optional[str] = None
    device_type: str = "desktop"  # desktop, mobile, server


class VPNClientResponse(BaseModel):
    id: str
    name: str
    type: str
    public_key: str
    ip_address: str
    location: str
    device_type: str
    status: str
    created_at: str
    data_transferred: Dict[str, int]


class VPNServerStatus(BaseModel):
    status: str
    port: int
    public_key: Optional[str]
    network: str
    connected_clients: int
    total_clients: int
    interface: str


class VPNConfigResponse(BaseModel):
    config: str
    filename: str


# Endpoints
@router.get("/status", response_model=VPNServerStatus)
async def get_server_status():
    """Get VPN server status"""
    vpn = get_vpn_manager()
    if not vpn:
        raise HTTPException(status_code=500, detail="VPN Manager not available")
    
    status = vpn.get_server_status()
    return status


@router.post("/server/start")
async def start_server():
    """Start VPN server"""
    vpn = get_vpn_manager()
    if not vpn:
        raise HTTPException(status_code=500, detail="VPN Manager not available")
    
    success = vpn.start_server()
    if success:
        return {"message": "VPN server started successfully", "status": "running"}
    else:
        raise HTTPException(status_code=500, detail="Failed to start VPN server")


@router.post("/server/stop")
async def stop_server():
    """Stop VPN server"""
    vpn = get_vpn_manager()
    if not vpn:
        raise HTTPException(status_code=500, detail="VPN Manager not available")
    
    success = vpn.stop_server()
    if success:
        return {"message": "VPN server stopped successfully", "status": "stopped"}
    else:
        raise HTTPException(status_code=500, detail="Failed to stop VPN server")


@router.get("/clients", response_model=List[VPNClientResponse])
async def list_clients():
    """List all VPN clients"""
    vpn = get_vpn_manager()
    if not vpn:
        raise HTTPException(status_code=500, detail="VPN Manager not available")
    
    clients = vpn.list_clients()
    return clients


@router.get("/clients/{client_id}", response_model=VPNClientResponse)
async def get_client(client_id: str):
    """Get specific VPN client"""
    vpn = get_vpn_manager()
    if not vpn:
        raise HTTPException(status_code=500, detail="VPN Manager not available")
    
    client = vpn.get_client_info(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return client


@router.post("/clients", response_model=VPNClientResponse)
async def create_client(client_data: VPNClientCreate):
    """Create new VPN client"""
    vpn = get_vpn_manager()
    if not vpn:
        raise HTTPException(status_code=500, detail="VPN Manager not available")
    
    client = vpn.add_client(
        name=client_data.name,
        client_type=client_data.type,
        location=client_data.location,
        device_type=client_data.device_type
    )
    
    if not client:
        raise HTTPException(status_code=500, detail="Failed to create client")
    
    return client


@router.delete("/clients/{client_id}")
async def delete_client(client_id: str):
    """Delete VPN client"""
    vpn = get_vpn_manager()
    if not vpn:
        raise HTTPException(status_code=500, detail="VPN Manager not available")
    
    success = vpn.remove_client(client_id)
    if success:
        return {"message": "Client deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Client not found")


@router.get("/clients/{client_id}/config", response_model=VPNConfigResponse)
async def get_client_config(client_id: str, server_endpoint: str = "45.123.45.67:51820"):
    """Get client configuration file"""
    vpn = get_vpn_manager()
    if not vpn:
        raise HTTPException(status_code=500, detail="VPN Manager not available")
    
    config = vpn.generate_client_config(client_id, server_endpoint)
    if not config:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client = vpn.get_client_info(client_id)
    filename = f"{client['name'].replace(' ', '_')}.conf"
    
    return {
        "config": config,
        "filename": filename
    }


@router.post("/export")
async def export_database():
    """Export VPN database"""
    vpn = get_vpn_manager()
    if not vpn:
        raise HTTPException(status_code=500, detail="VPN Manager not available")
    
    vpn.export_database("./vpn_database.json")
    return {"message": "Database exported successfully", "filepath": "./vpn_database.json"}


@router.post("/import")
async def import_database(filepath: str = "./vpn_database.json"):
    """Import VPN database"""
    vpn = get_vpn_manager()
    if not vpn:
        raise HTTPException(status_code=500, detail="VPN Manager not available")
    
    try:
        vpn.import_database(filepath)
        return {"message": "Database imported successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to import database: {str(e)}")


# Demo endpoint for testing without WireGuard
@router.get("/demo/clients")
async def get_demo_clients():
    """Get demo VPN clients (for testing without WireGuard)"""
    demo_clients = [
        {
            "id": "1",
            "name": "Merkez MaÄŸaza - Ä°stanbul",
            "type": "central",
            "public_key": "CENTRAL_PUB_KEY_ABC123",
            "ip_address": "10.8.0.1",
            "status": "connected",
            "location": "Ä°stanbul, TÃ¼rkiye",
            "device_type": "server",
            "created_at": datetime.now().isoformat(),
            "data_transferred": {"upload": 157286400, "download": 335544320}
        },
        {
            "id": "2",
            "name": "Åube 1 - Ankara",
            "type": "store",
            "public_key": "STORE1_PUB_KEY_DEF456",
            "ip_address": "10.8.0.2",
            "status": "connected",
            "location": "Ankara, TÃ¼rkiye",
            "device_type": "desktop",
            "created_at": datetime.now().isoformat(),
            "data_transferred": {"upload": 83886080, "download": 125829120}
        },
        {
            "id": "3",
            "name": "Depo 1 - Gebze",
            "type": "warehouse",
            "public_key": "WMS1_PUB_KEY_JKL012",
            "ip_address": "10.8.0.4",
            "status": "connected",
            "location": "Gebze, Kocaeli",
            "device_type": "server",
            "created_at": datetime.now().isoformat(),
            "data_transferred": {"upload": 209715200, "download": 524288000}
        },
        {
            "id": "4",
            "name": "Saha SatÄ±ÅŸ - Ahmet YÄ±lmaz",
            "type": "fieldsales",
            "public_key": "FS1_PUB_KEY_MNO345",
            "ip_address": "10.8.0.5",
            "status": "connected",
            "location": "Bursa, TÃ¼rkiye",
            "device_type": "mobile",
            "created_at": datetime.now().isoformat(),
            "data_transferred": {"upload": 15728640, "download": 26214400}
        }
    ]
    return demo_clients
