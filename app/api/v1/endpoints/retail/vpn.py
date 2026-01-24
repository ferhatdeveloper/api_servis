"""
ExRetailOS VPN Manager API Endpoints
VPN Yönetim Modülü (WireGuard)
Mağazalar ve merkez arası güvenli bağlantı yönetimi.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
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
    name: str = Field(..., description="VPN istemci adı (Mağaza veya kişi ismi)")
    type: str = Field("store", description="İstemci türü: 'store', 'fieldsales', 'warehouse', 'central'")
    location: Optional[str] = Field(None, description="Fiziksel konum bilgisi")
    device_type: str = Field("desktop", description="Cihaz tipi: 'desktop', 'mobile', 'server'")


class VPNClientResponse(BaseModel):
    id: str = Field(..., description="Unique Client ID")
    name: str = Field(..., description="İstemci Adı")
    type: str = Field(..., description="Tür")
    public_key: str = Field(..., description="WireGuard Public Key")
    ip_address: str = Field(..., description="Atanan VPN IP Adresi")
    location: str
    device_type: str
    status: str = Field(..., description="Bağlantı Durumu")
    created_at: str
    data_transferred: Dict[str, int] = Field(..., description="Veri transfer istatistikleri (byte)")


class VPNServerStatus(BaseModel):
    status: str = Field(..., description="Sunucu durumu: 'running', 'stopped'")
    port: int = Field(..., description="Dinlenen Port (UDP)")
    public_key: Optional[str]
    network: str = Field(..., description="VPN Alt Ağı (10.8.0.0/24)")
    connected_clients: int
    total_clients: int
    interface: str = Field(..., description="Ağ arayüzü (wg0)")


class VPNConfigResponse(BaseModel):
    config: str = Field(..., description="İstemci konfigürasyon dosyası içeriği")
    filename: str = Field(..., description="Dosya adı (.conf)")


# Endpoints
@router.get("/status", response_model=VPNServerStatus)
async def get_server_status():
    """
    **VPN Sunucu Durumu**

    VPN sunucusunun anlık durumunu, çalışan portu ve bağlı istemci sayısını döner.
    """
    vpn = get_vpn_manager()
    if not vpn:
        raise HTTPException(status_code=500, detail="VPN Manager not available")
    
    status = vpn.get_server_status()
    return status


@router.post("/server/start")
async def start_server():
    """
    **Sunucuyu Başlat**

    WireGuard servisini sunucu üzerinde başlatır.
    """
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
    """
    **Sunucuyu Durdur**

    WireGuard servisini durdurur. Tüm bağlantılar kesilir.
    """
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
    """
    **İstemci Listesi**

    Kayıtlı tüm VPN istemcilerini ve son durumlarını listeler.
    """
    vpn = get_vpn_manager()
    if not vpn:
        raise HTTPException(status_code=500, detail="VPN Manager not available")
    
    clients = vpn.list_clients()
    return clients


@router.get("/clients/{client_id}", response_model=VPNClientResponse)
async def get_client(client_id: str):
    """
    **İstemci Detayı**

    Belirli bir istemcinin detaylı bilgilerini döner.
    """
    vpn = get_vpn_manager()
    if not vpn:
        raise HTTPException(status_code=500, detail="VPN Manager not available")
    
    client = vpn.get_client_info(client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return client


@router.post("/clients", response_model=VPNClientResponse)
async def create_client(client_data: VPNClientCreate):
    """
    **Yeni İstemci Ekle**

    Yeni bir VPN kullanıcısı oluşturur (Public/Private key üretir).
    Otomatik olarak bir IP adresi atar.
    """
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
    """
    **İstemci Sil**

    İstemciyi sistemden ve WireGuard konfigürasyonundan kaldırır.
    """
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
    """
    **Konfigürasyon Dosyası İndir**

    İstemci (client) tarafında import edilecek .conf dosyasını oluşturur.
    Bu dosya WireGuard istemcisine yüklenerek bağlantı sağlanır.
    """
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
    """
    **Veritabanı Dışa Aktar**

    VPN istemci veritabanını JSON olarak yedekler.
    """
    vpn = get_vpn_manager()
    if not vpn:
        raise HTTPException(status_code=500, detail="VPN Manager not available")
    
    vpn.export_database("./vpn_database.json")
    return {"message": "Database exported successfully", "filepath": "./vpn_database.json"}


@router.post("/import")
async def import_database(filepath: str = "./vpn_database.json"):
    """
    **Veritabanı İçe Aktar**

    JSON yedeğinden VPN istemci listesini geri yükler.
    """
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
    """
    **Demo İstemci Listesi**

    WireGuard kurulumu olmayan ortamlar için örnek/mock veri döner.
    Test amaçlıdır.
    """
    demo_clients = [
        {
            "id": "1",
            "name": "Merkez Mağaza - İstanbul",
            "type": "central",
            "public_key": "CENTRAL_PUB_KEY_ABC123",
            "ip_address": "10.8.0.1",
            "status": "connected",
            "location": "İstanbul, Türkiye",
            "device_type": "server",
            "created_at": datetime.now().isoformat(),
            "data_transferred": {"upload": 157286400, "download": 335544320}
        },
        {
            "id": "2",
            "name": "Şube 1 - Ankara",
            "type": "store",
            "public_key": "STORE1_PUB_KEY_DEF456",
            "ip_address": "10.8.0.2",
            "status": "connected",
            "location": "Ankara, Türkiye",
            "device_type": "desktop",
            "created_at": datetime.now().isoformat(),
            "data_transferred": {"upload": 83886080, "download": 125829120}
        }
    ]
    return demo_clients
